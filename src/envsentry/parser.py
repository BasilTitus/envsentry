"""A small, forgiving parser for dotenv files.

The parser never raises on bad input. Instead it records what it found on each
line so the linter can report precise, line-numbered problems.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class Entry:
    """One ``KEY=value`` assignment found in a dotenv file."""

    key: str
    value: str
    line: int
    raw: str
    quote: str | None = None  # '"', "'" or None
    exported: bool = False
    space_around_equals: bool = False
    unterminated_quote: bool = False


@dataclass
class BadLine:
    """A non-empty, non-comment line that is not a valid assignment."""

    line: int
    raw: str


@dataclass
class EnvFile:
    path: Path | None
    entries: list[Entry] = field(default_factory=list)
    bad_lines: list[BadLine] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)

    def keys(self) -> list[str]:
        return [e.key for e in self.entries]

    def as_dict(self) -> dict:
        """Last assignment wins, mirroring how most dotenv loaders behave."""
        return {e.key: e.value for e in self.entries}

    def get(self, key: str) -> Entry | None:
        found = None
        for entry in self.entries:
            if entry.key == key:
                found = entry
        return found


def _strip_inline_comment(value: str) -> str:
    # An unquoted value ends at " #" (whitespace followed by a hash).
    match = re.search(r"\s+#", value)
    return value[: match.start()] if match else value


def _parse_value(rest: str) -> tuple:
    """Return ``(value, quote, unterminated)`` for the text after ``=``."""
    rest = rest.lstrip()
    if rest[:1] in ('"', "'"):
        quote = rest[0]
        end = 1
        while end < len(rest):
            if rest[end] == "\\" and quote == '"':
                end += 2
                continue
            if rest[end] == quote:
                inner = rest[1:end]
                if quote == '"':
                    inner = inner.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")
                return inner, quote, False
            end += 1
        return rest[1:], quote, True
    return _strip_inline_comment(rest).rstrip(), None, False


def parse_text(text: str, path: Path | None = None) -> EnvFile:
    env = EnvFile(path=path, lines=text.splitlines())
    for number, raw in enumerate(env.lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        body = stripped
        exported = False
        if body.startswith("export ") or body.startswith("export\t"):
            exported = True
            body = body[len("export") :].lstrip()

        if "=" not in body:
            env.bad_lines.append(BadLine(line=number, raw=raw))
            continue

        key_part, rest = body.split("=", 1)
        key = key_part.strip()
        space_around = key_part != key_part.rstrip() or (rest[:1] in (" ", "\t"))
        value, quote, unterminated = _parse_value(rest)

        env.entries.append(
            Entry(
                key=key,
                value=value,
                line=number,
                raw=raw,
                quote=quote,
                exported=exported,
                space_around_equals=space_around,
                unterminated_quote=unterminated,
            )
        )
    return env


def parse_file(path) -> EnvFile:
    path = Path(path)
    text = path.read_text(encoding="utf-8-sig")
    return parse_text(text, path=path)
