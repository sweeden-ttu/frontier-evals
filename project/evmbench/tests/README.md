# evmbench tests

## Running tests

Tests must be run via `uv run pytest`. Plain `pytest` uses system Python and
will miss declared dependencies. CI runs `uv run pytest` — local runs that
bypass uv will silently diverge.

```bash
cd project/evmbench
uv run pytest tests/ -q
```

## Layout

- `tests/test_audits_validation.py` — audit registry schema validation
- `tests/test_bootstrap.py` — bootstrap/sidecar config
- `tests/test_ploit_config.py` — ploit & Veto launch config
- `tests/test_chomsky_wiring.py` — Chomsky V&V producer/consumer pipeline
  (alphabet grounded against real `ctx_logger.info` sites, contracts,
  Veto bridge, and the lifecycle gate)
