"""AST/identifier-aware matcher for banned tokens.

Python sources are parsed with :mod:`ast` and :mod:`tokenize`. Bare
identifiers must equal a banned token exactly to fire (case-insensitively
in both Python and text); substring identifiers like ``train_test_split``
or ``pretrain`` do not. Strings, comments, docstrings and non-Python
text are scanned with word-boundary regex; ``\\b`` already treats ``_``
as a word character, so ``X_train`` and ``pretrain`` do not match
``\\btrain\\b``.

Allowlist exemptions are consulted *after* a candidate hit: if the
surrounding identifier or word is allowlisted, the hit is dropped.
"""

from __future__ import annotations

import ast
import io
import json
import re
import tokenize
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from chomsky_vv.banned.policy import BannedToken, BannedTokenPolicy


HitKind = str  # 'string_literal' | 'docstring' | 'comment' | 'identifier' | 'text' | 'ipynb_code' | 'ipynb_markdown'


@dataclass(frozen=True)
class Hit:
    """A single banned-token match in a source artifact."""

    token: str
    file: str
    line: int
    col: int
    kind: HitKind
    excerpt: str
    severity: str


_PYTHON_EXTENSIONS = frozenset({".py", ".pyi"})
_NOTEBOOK_EXTENSIONS = frozenset({".ipynb"})
_TEXT_EXTENSIONS = frozenset(
    {
        ".md",
        ".txt",
        ".rst",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".csv",
        ".tsv",
        ".log",
        ".html",
        ".htm",
        ".xml",
        ".cfg",
        ".ini",
        ".env",
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".go",
        ".rs",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".java",
        ".rb",
    }
)
_SKIP_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        "node_modules",
        ".tox",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".coverage",
        "dist",
        "build",
        ".eggs",
        ".idea",
        ".vscode",
    }
)


class BannedTokenMatcher:
    """Scan Python and text artifacts for banned tokens."""

    def __init__(self, policy: BannedTokenPolicy) -> None:
        self.policy = policy
        self._patterns: list[tuple[BannedToken, re.Pattern[str]]] = [
            (bt, _build_regex(bt)) for bt in policy.tokens
        ]
        self._identifier_tokens: list[BannedToken] = [
            bt for bt in policy.tokens if bt.match_kind in ("word", "literal")
        ]
        self._allow: frozenset[str] = frozenset(policy.allowlist_identifiers)

    # ------------------------------------------------------------------ public
    def scan_text(self, source: str, path: str | Path, kind: HitKind = "text") -> list[Hit]:
        """Scan an arbitrary text blob with word-boundary regex per token."""
        path_str = str(path)
        hits: list[Hit] = []
        for bt, pat in self._patterns:
            for m in pat.finditer(source):
                surrounding = _surrounding_word(source, m.start())
                if surrounding and surrounding in self._allow:
                    continue
                # Domain-kind hits also expose a wider surrounding token
                # (the URL/host) which we want to allowlist-check too.
                wider = _surrounding_url(source, m.start(), m.end())
                if wider and wider in self._allow:
                    continue
                line, col = _line_col(source, m.start())
                hits.append(
                    Hit(
                        token=bt.token,
                        file=path_str,
                        line=line,
                        col=col,
                        kind=kind,
                        excerpt=_excerpt(source, m.start(), m.end()),
                        severity=bt.severity,
                    )
                )
        return hits

    def scan_python(self, source: str, path: str | Path) -> list[Hit]:
        """Scan a Python source string AST-aware + tokenize comments."""
        path_str = str(path)
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return self.scan_text(source, path, kind="text")

        docstring_locs = _docstring_locations(tree)
        hits: list[Hit] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                node_kind: HitKind = (
                    "docstring" if (node.lineno, node.col_offset) in docstring_locs else "string_literal"
                )
                inner = self.scan_text(node.value, path_str, kind=node_kind)
                for h in inner:
                    hits.append(
                        Hit(
                            token=h.token,
                            file=path_str,
                            line=node.lineno + (h.line - 1),
                            col=node.col_offset if h.line == 1 else h.col,
                            kind=node_kind,
                            excerpt=h.excerpt,
                            severity=h.severity,
                        )
                    )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                bt = self._identifier_match(node.name)
                if bt is not None:
                    hits.append(
                        Hit(
                            token=bt.token,
                            file=path_str,
                            line=node.lineno,
                            col=node.col_offset,
                            kind="identifier",
                            excerpt=node.name,
                            severity=bt.severity,
                        )
                    )
            elif isinstance(node, ast.arg):
                bt = self._identifier_match(node.arg)
                if bt is not None:
                    hits.append(
                        Hit(
                            token=bt.token,
                            file=path_str,
                            line=node.lineno,
                            col=node.col_offset,
                            kind="identifier",
                            excerpt=node.arg,
                            severity=bt.severity,
                        )
                    )
            elif isinstance(node, ast.Name) and isinstance(getattr(node, "ctx", None), ast.Store):
                bt = self._identifier_match(node.id)
                if bt is not None:
                    hits.append(
                        Hit(
                            token=bt.token,
                            file=path_str,
                            line=node.lineno,
                            col=node.col_offset,
                            kind="identifier",
                            excerpt=node.id,
                            severity=bt.severity,
                        )
                    )

        # Comments via tokenize. Wrap to ignore tokenize errors on
        # exotic encodings or partial files.
        try:
            for tok in tokenize.tokenize(io.BytesIO(source.encode("utf-8")).readline):
                if tok.type != tokenize.COMMENT:
                    continue
                inner = self.scan_text(tok.string, path_str, kind="comment")
                for h in inner:
                    hits.append(
                        Hit(
                            token=h.token,
                            file=path_str,
                            line=tok.start[0],
                            col=tok.start[1] + h.col,
                            kind="comment",
                            excerpt=h.excerpt,
                            severity=h.severity,
                        )
                    )
        except (tokenize.TokenError, IndentationError):
            pass

        return hits

    def scan_path(self, path: str | Path) -> list[Hit]:
        """Recursively scan a file or directory and return all hits."""
        p = Path(path)
        if p.is_file():
            return self._scan_file(p)
        if p.is_dir():
            results: list[Hit] = []
            for sub in _walk_files(p):
                results.extend(self._scan_file(sub))
            return results
        return []

    # ----------------------------------------------------------------- helpers
    def _identifier_match(self, name: str) -> BannedToken | None:
        if name in self._allow:
            return None
        lower = name.lower()
        for bt in self._identifier_tokens:
            if name == bt.token or lower == bt.token.lower():
                return bt
        return None

    def _scan_file(self, p: Path) -> list[Hit]:
        ext = p.suffix.lower()
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
        if ext in _PYTHON_EXTENSIONS:
            return self.scan_python(text, str(p))
        if ext in _NOTEBOOK_EXTENSIONS:
            return _scan_notebook(text, str(p), self)
        if ext in _TEXT_EXTENSIONS or ext == "":
            return self.scan_text(text, str(p), kind="text")
        return []


# --------------------------------------------------------------------- internals
def _docstring_locations(tree: ast.AST) -> set[tuple[int, int]]:
    locs: set[tuple[int, int]] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", None)
            if not body:
                continue
            first = body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                locs.add((first.value.lineno, first.value.col_offset))
    return locs


def _walk_files(root: Path) -> Iterable[Path]:
    try:
        children = sorted(root.iterdir())
    except OSError:
        return
    for child in children:
        if child.is_symlink():
            continue
        if child.is_dir():
            if child.name in _SKIP_DIRS:
                continue
            yield from _walk_files(child)
        elif child.is_file():
            yield child


def _line_col(source: str, offset: int) -> tuple[int, int]:
    prefix = source[:offset]
    line = prefix.count("\n") + 1
    col = offset - (prefix.rfind("\n") + 1)
    return line, col


def _excerpt(source: str, start: int, end: int, around: int = 40) -> str:
    s = max(0, start - around)
    e = min(len(source), end + around)
    return source[s:e].replace("\n", "\\n")[:200]


_WORD_RE = re.compile(r"[A-Za-z0-9_]")


def _surrounding_word(source: str, offset: int) -> str | None:
    """Return the maximal ``[A-Za-z0-9_]`` run surrounding ``offset``."""
    left = offset
    while left > 0 and _WORD_RE.match(source[left - 1] or ""):
        left -= 1
    right = offset
    while right < len(source) and _WORD_RE.match(source[right] or ""):
        right += 1
    if right > left:
        return source[left:right]
    return None


_HOST_CHAR_RE = re.compile(r"[A-Za-z0-9._-]")


def _surrounding_url(source: str, start: int, end: int) -> str | None:
    """Return the URL-like blob surrounding a domain hit (``example.com``)."""
    left = start
    while left > 0 and _HOST_CHAR_RE.match(source[left - 1] or ""):
        left -= 1
    right = end
    while right < len(source) and _HOST_CHAR_RE.match(source[right] or ""):
        right += 1
    if right > left:
        return source[left:right]
    return None


def _build_regex(bt: BannedToken) -> re.Pattern[str]:
    flags = re.IGNORECASE
    if bt.match_kind == "domain":
        return re.compile(rf"(?<![A-Za-z0-9.]){re.escape(bt.token)}(?![A-Za-z0-9])", flags)
    if bt.match_kind == "literal":
        return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(bt.token)}(?![A-Za-z0-9_])", flags)
    return re.compile(rf"\b{re.escape(bt.token)}\b", flags)


def _scan_notebook(source: str, path: str, matcher: BannedTokenMatcher) -> list[Hit]:
    """Scan a Jupyter ``.ipynb`` by extracting cell sources."""
    try:
        nb = json.loads(source)
    except json.JSONDecodeError:
        return matcher.scan_text(source, path, kind="text")
    hits: list[Hit] = []
    for i, cell in enumerate(nb.get("cells", [])):
        cell_type = cell.get("cell_type", "")
        cell_source = cell.get("source", "")
        if isinstance(cell_source, list):
            cell_source = "".join(cell_source)
        kind: HitKind = "ipynb_code" if cell_type == "code" else "ipynb_markdown"
        ref = f"{path}#cell{i}"
        if cell_type == "code":
            hits.extend(matcher.scan_python(cell_source, ref))
        else:
            hits.extend(matcher.scan_text(cell_source, ref, kind=kind))
    return hits
