"""Generate a safe ``.env.example`` from a real ``.env`` file."""

from __future__ import annotations

from .parser import EnvFile


def make_example(env: EnvFile) -> str:
    """Return the file's text with every value blanked out.

    Comments, blank lines and ordering are preserved so the example stays a
    readable, documented template. ``export`` prefixes are kept as well.
    """
    by_line = {e.line: e for e in env.entries}
    out = []
    for number, raw in enumerate(env.lines, start=1):
        entry = by_line.get(number)
        if entry is None:
            out.append(raw.rstrip())
            continue
        prefix = "export " if entry.exported else ""
        out.append(f"{prefix}{entry.key}=")
    text = "\n".join(out)
    return text + "\n" if text else ""
