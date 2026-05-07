"""Σ-alphabet definitions for trace discretization.

A ``TokenSpec`` is a regex-driven recognizer. Each spec optionally declares
``push``/``pop`` semantics so probes that rely on stack discipline (P2, P3)
can interpret the trace without rescanning the source.

The matcher is intentionally O(|text| * |alphabet|): the whole framework runs
inside the verifier's Type-2 envelope, so we keep behavior predictable and
avoid combined regexes whose ``lastgroup`` semantics are fragile under nested
named groups in user-supplied patterns.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TokenSpec:
    name: str
    pattern: str
    push: bool = False
    pop: bool = False
    pairs_with: str | None = None

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", self.name):
            raise ValueError(f"token name must be a Python identifier: {self.name!r}")
        if self.pop and self.push:
            raise ValueError(f"token {self.name!r} cannot be both push and pop")
        if self.pairs_with is not None and not self.pop:
            raise ValueError(f"token {self.name!r} declares pairs_with but is not pop")
        # Eager compile validates the pattern at construction time.
        re.compile(self.pattern)


@dataclass
class Alphabet:
    tokens: list[TokenSpec]
    _compiled: list[re.Pattern[str]] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        names = [t.name for t in self.tokens]
        dups = sorted({n for n in names if names.count(n) > 1})
        if dups:
            raise ValueError(f"duplicate token names: {dups}")
        for t in self.tokens:
            if t.pairs_with is not None and t.pairs_with not in names:
                raise ValueError(
                    f"token {t.name!r} pairs_with {t.pairs_with!r} which is not in alphabet"
                )
        self._compiled = [re.compile(t.pattern) for t in self.tokens]

    @property
    def names(self) -> list[str]:
        return [t.name for t in self.tokens]

    def by_name(self, name: str) -> TokenSpec:
        for t in self.tokens:
            if t.name == name:
                return t
        raise KeyError(name)

    @property
    def push_names(self) -> frozenset[str]:
        return frozenset(t.name for t in self.tokens if t.push)

    @property
    def pop_names(self) -> frozenset[str]:
        return frozenset(t.name for t in self.tokens if t.pop)

    @property
    def pair_map(self) -> dict[str, str]:
        return {t.name: t.pairs_with for t in self.tokens if t.pop and t.pairs_with}

    def scan(self, text: str) -> list[tuple[TokenSpec, int, int]]:
        """Greedy left-to-right scan; the first declared spec that matches at
        a position wins. Non-matching characters are skipped one at a time."""
        out: list[tuple[TokenSpec, int, int]] = []
        pos = 0
        n = len(text)
        while pos < n:
            chosen: tuple[TokenSpec, int, int] | None = None
            for spec, rx in zip(self.tokens, self._compiled):
                m = rx.match(text, pos)
                if m and m.end() > m.start():
                    chosen = (spec, m.start(), m.end())
                    break
            if chosen is None:
                pos += 1
            else:
                out.append(chosen)
                pos = chosen[2]
        return out
