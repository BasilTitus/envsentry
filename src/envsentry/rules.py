"""Lint and comparison rules. Each finding has a stable code you can ignore."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass

from .parser import KEY_RE, EnvFile
from .secrets import looks_like_secret

ERROR = "error"
WARNING = "warning"

# code -> (severity, short description). Documented in the README.
RULES = {
    "E001": (ERROR, "line is not a KEY=value assignment"),
    "E002": (ERROR, "invalid key name"),
    "E003": (ERROR, "duplicate key"),
    "E004": (ERROR, "unterminated quoted value"),
    "E101": (ERROR, "key required by the example file is missing"),
    "S001": (ERROR, "value looks like a real secret"),
    "W001": (WARNING, "key is not UPPER_SNAKE_CASE"),
    "W002": (WARNING, "whitespace around '='"),
    "W003": (WARNING, "unquoted value contains whitespace"),
    "W004": (WARNING, "trailing whitespace"),
    "W005": (WARNING, "empty value"),
    "W101": (WARNING, "key is not declared in the example file"),
}


@dataclass
class Finding:
    code: str
    message: str
    file: str
    line: int | None = None
    key: str | None = None

    @property
    def severity(self) -> str:
        return RULES[self.code][0]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["severity"] = self.severity
        return data


def _name(env: EnvFile) -> str:
    return str(env.path) if env.path else "<stdin>"


def lint(env: EnvFile, *, allow_empty: bool = False) -> list[Finding]:
    """Check a single dotenv file for syntax and style problems."""
    name = _name(env)
    out: list[Finding] = []

    for bad in env.bad_lines:
        out.append(Finding("E001", f"cannot parse: {bad.raw.strip()!r}", name, bad.line))

    seen = {}
    for e in env.entries:
        if not KEY_RE.match(e.key):
            out.append(Finding("E002", f"invalid key name {e.key!r}", name, e.line, e.key))
            continue
        if e.key in seen:
            out.append(
                Finding(
                    "E003",
                    f"{e.key} is already defined on line {seen[e.key]}",
                    name,
                    e.line,
                    e.key,
                )
            )
        else:
            seen[e.key] = e.line
        if e.unterminated_quote:
            out.append(Finding("E004", f"{e.key} has an unterminated {e.quote} quote", name, e.line, e.key))
        if e.key != e.key.upper():
            out.append(Finding("W001", f"{e.key} should be {e.key.upper()}", name, e.line, e.key))
        if e.space_around_equals:
            out.append(Finding("W002", f"remove spaces around '=' for {e.key}", name, e.line, e.key))
        if e.quote is None and any(ch.isspace() for ch in e.value):
            out.append(Finding("W003", f"quote the value of {e.key}", name, e.line, e.key))
        if e.raw != e.raw.rstrip():
            out.append(Finding("W004", "trailing whitespace", name, e.line, e.key))
        if not allow_empty and e.value == "" and e.quote is None:
            out.append(Finding("W005", f"{e.key} has no value", name, e.line, e.key))
    return out


def compare(env: EnvFile, example: EnvFile, *, allow_extra: bool = False) -> list[Finding]:
    """Compare a real env file against the example/template that documents it."""
    name = _name(env)
    out: list[Finding] = []
    env_keys = set(env.keys())
    for e in example.entries:
        if e.key not in env_keys:
            out.append(
                Finding(
                    "E101",
                    f"{e.key} is missing (declared in {_name(example)}:{e.line})",
                    name,
                    None,
                    e.key,
                )
            )
    if not allow_extra:
        example_keys = set(example.keys())
        for e in env.entries:
            if e.key not in example_keys:
                out.append(
                    Finding("W101", f"{e.key} is not documented in {_name(example)}", name, e.line, e.key)
                )
    return out


def scan_secrets(env: EnvFile) -> list[Finding]:
    """Flag values that look like real credentials (use on committed files)."""
    name = _name(env)
    out: list[Finding] = []
    for e in env.entries:
        reason = looks_like_secret(e.key, e.value)
        if reason:
            out.append(Finding("S001", f"{e.key} looks like a real secret ({reason})", name, e.line, e.key))
    return out


def filter_ignored(findings: Iterable[Finding], ignore: Iterable[str]) -> list[Finding]:
    ignored = {code.strip().upper() for code in ignore if code.strip()}
    return [f for f in findings if f.code not in ignored and f.code[:1] not in ignored]
