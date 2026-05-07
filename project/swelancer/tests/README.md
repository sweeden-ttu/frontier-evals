# swelancer tests

## Running tests

Tests must be run via `uv run pytest`. Plain `pytest` uses system Python and
will miss declared dependencies. CI runs `uv run pytest` — local runs that
bypass uv will silently diverge.

```bash
cd project/swelancer
uv run pytest tests/ -q
```

## Layout

- `tests/integration/` — integration tests
- `tests/test_chomsky_wiring.py` — Chomsky V&V producer/consumer pipeline
  including the NEW non-LLM Type-3 certifier (`SwelancerCertifier`):
  test-bundle isolation envelope + python-block CFG validator. Default
  mode is ENFORCING — any swelancer rollout containing a forbidden
  import / call / attribute access in a python block is refused at the
  gate. Override at the call site for calibration baselines.
