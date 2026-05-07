# paperbench tests

## Running tests

Tests must be run via `uv run pytest`. Plain `pytest` uses system Python and
will miss declared dependencies. CI runs `uv run pytest` — local runs that
bypass uv will silently diverge.

```bash
cd project/paperbench
uv run pytest tests/ -q
```

## Layout

- `tests/unit/` — pure unit tests; safe to run anywhere uv is present
- `tests/integration/` — require Docker daemon and may pull images
- `tests/unit/test_chomsky_wiring.py` — Chomsky V&V producer/consumer
  pipeline (alphabet, contracts, monitor bridge, gate)

## Environment requirements

Some tests require external services and will error or be skipped without
them:

- `tests/unit/test_computer.py` — needs a running Docker daemon
- `tests/unit/test_judge.py` (SimpleJudge variants) — needs `OPENAI_API_KEY`
