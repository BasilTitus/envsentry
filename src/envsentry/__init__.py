"""envsentry: catch broken, incomplete and leaky .env files before they bite."""

from .example import make_example
from .parser import EnvFile, parse_file, parse_text
from .rules import RULES, Finding, compare, lint, scan_secrets

__all__ = [
    "EnvFile",
    "Finding",
    "RULES",
    "compare",
    "lint",
    "make_example",
    "parse_file",
    "parse_text",
    "scan_secrets",
]

__version__ = "0.1.0"
