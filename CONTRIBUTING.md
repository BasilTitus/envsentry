# Contributing to envsentry

Thanks for helping! Small, focused pull requests are the easiest to review.

## Setup

```bash
git clone https://github.com/BasilTitus/envsentry
cd envsentry
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
ruff check .
```

## Adding a rule

1. Give it the next free code in `RULES` in `src/envsentry/rules.py`
   (`E` = error, `W` = warning, `S` = secret).
2. Emit a `Finding` for it in `lint`, `compare` or `scan_secrets`.
3. Add a test in `tests/test_rules.py` and a row to the Rules table in `README.md`.
4. Note it under "Unreleased" in `CHANGELOG.md`.

## Adding a secret pattern

Add a `(name, regex)` pair to `PATTERNS` in `src/envsentry/secrets.py`, with a test that it
matches and that a common placeholder does not. **Never commit a real credential in a test:**
build fake tokens at runtime (for example `"ghp_" + "a" * 36`) or use the provider's
documented example values.

## Ground rules

- No runtime dependencies. The standard library is enough.
- Keep Python 3.10 compatibility.
- Be kind: see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Releasing (maintainers)

1. Bump `__version__` in `src/envsentry/__init__.py` and move "Unreleased" notes in `CHANGELOG.md`
   under the new version.
2. Commit, then create a GitHub release with a tag that matches, e.g. `v0.2.0`.
3. The `Release` workflow builds the package and publishes it to PyPI through trusted publishing.
