"""Heuristics for spotting real secrets that slipped into a committed file."""

from __future__ import annotations

import math
import re
from collections import Counter

# (name, pattern) pairs for well-known credential formats.
PATTERNS = [
    ("AWS access key ID", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("Stripe live key", re.compile(r"\b[sr]k_live_[A-Za-z0-9]{16,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("OpenAI / Anthropic style key", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}\b")),
    ("Private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    ("URL with embedded password", re.compile(r"[a-z][a-z0-9+.-]*://[^:/\s]+:[^@/\s]{3,}@")),
]

# Values people commonly use as placeholders. These are never flagged.
PLACEHOLDER_RE = re.compile(
    r"^(|changeme|change_me|replace_me|todo|xxx+|your[_-].*|<.*>|\$\{.*\}|"
    r"example.*|dummy.*|test.*|placeholder.*|secret|password|none|null|true|false|"
    r"localhost.*|\d+)$",
    re.IGNORECASE,
)

SENSITIVE_KEY_RE = re.compile(
    r"(SECRET|TOKEN|PASSWORD|PASSWD|PWD|API_?KEY|PRIVATE|CREDENTIAL|AUTH)", re.IGNORECASE
)


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    length = len(value)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def looks_like_secret(key: str, value: str) -> str | None:
    """Return a human-readable reason if ``value`` looks like a real secret."""
    if PLACEHOLDER_RE.match(value.strip()):
        return None
    for name, pattern in PATTERNS:
        if pattern.search(value):
            return name
    if (
        SENSITIVE_KEY_RE.search(key)
        and len(value) >= 16
        and " " not in value
        and shannon_entropy(value) >= 3.5
    ):
        return "high-entropy value for a sensitive-looking key"
    return None
