# envsentry

[![CI](https://github.com/BasilTitus/envsentry/actions/workflows/ci.yml/badge.svg)](https://github.com/BasilTitus/envsentry/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

**Catch broken, incomplete and leaky `.env` files before they bite.**

Every project has a `.env` and a `.env.example`, and they drift apart. Someone adds `STRIPE_KEY`
to their `.env`, forgets the example, and the next person spends an hour working out why checkout
crashes. Or worse: someone pastes a real key into `.env.example` and commits it.

`envsentry` is a tiny, zero-dependency CLI that:

- **lints** dotenv files: duplicate keys, bad syntax, unterminated quotes, unquoted spaces…
- **compares** `.env` against `.env.example`: missing keys fail, undocumented keys warn
- **scans** committed files for real secrets: AWS, GitHub, Stripe, Slack, Google, `sk-` API keys,
  JWTs, private keys, passwords in URLs and high-entropy values on sensitive-looking keys
- **generates** a clean `.env.example` from your `.env`, keeping comments and order

```console
$ envsentry check
.env:4 W001 database_url should be DATABASE_URL
.env:7 E003 API_KEY is already defined on line 2
.env E101 REDIS_URL is missing (declared in .env.example:5)
.env.example:3 S001 STRIPE_KEY looks like a real secret (Stripe live key)
3 error(s), 1 warning(s)
```

## Install

```bash
pipx install envsentry      # or: pip install envsentry
```

Or run from a clone without installing: `python -m envsentry` with `src` on `PYTHONPATH`.

## Usage

| Command | What it does |
| --- | --- |
| `envsentry check` | Lint `.env`, compare it with `.env.example`, scan the example for secrets |
| `envsentry lint [FILES…]` | Syntax and style checks (default: `.env`) |
| `envsentry scan [FILES…]` | Secret scan for files you commit (default: `.env.example`) |
| `envsentry example` | Write `.env.example` from `.env` with every value blanked |
| `envsentry rules` | List every rule code |

Common options:

- `--format json`: machine-readable output for CI and editors
- `--ignore W001,W005`: skip rules by code, or a whole class with a prefix (`--ignore W`)
- `--strict`: fail on warnings too
- `check --env .env.local --example .env.template`: use other file names
- `check --allow-extra` / `--allow-empty`: relax the matching rules

Exit codes: `0` clean, `1` findings (errors, or warnings with `--strict`), `2` usage error such as a missing file.

## Rules

| Code | Severity | Meaning |
| --- | --- | --- |
| E001 | error | Line is not a `KEY=value` assignment |
| E002 | error | Invalid key name |
| E003 | error | Duplicate key |
| E004 | error | Unterminated quoted value |
| E101 | error | Key required by the example file is missing |
| S001 | error | Value looks like a real secret |
| W001 | warning | Key is not `UPPER_SNAKE_CASE` |
| W002 | warning | Whitespace around `=` |
| W003 | warning | Unquoted value contains whitespace |
| W004 | warning | Trailing whitespace |
| W005 | warning | Empty value |
| W101 | warning | Key is not declared in the example file |

Placeholders such as `changeme`, `your-api-key`, `<token>`, `${VAR}`, `localhost` URLs, numbers and
booleans are never reported as secrets.

## Use it in CI

**GitHub Actions**

```yaml
- uses: actions/setup-python@v5
  with: { python-version: "3.12" }
- run: pip install envsentry && envsentry scan .env.example
```

**pre-commit**

```yaml
repos:
  - repo: https://github.com/BasilTitus/envsentry
    rev: v0.1.0
    hooks:
      - id: envsentry-scan
```

## Use it as a library

```python
from envsentry import parse_file, lint, compare, scan_secrets

env = parse_file(".env")
problems = lint(env) + compare(env, parse_file(".env.example"))
for p in problems:
    print(p.code, p.line, p.message)
```

## Contributing

Bug reports, new secret patterns and rule ideas are very welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
