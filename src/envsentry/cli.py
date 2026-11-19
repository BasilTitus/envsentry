"""Command-line interface for envsentry."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .example import make_example
from .parser import EnvFile, parse_file
from .rules import ERROR, RULES, Finding, compare, filter_ignored, lint, scan_secrets

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2


class _Style:
    def __init__(self, enabled: bool):
        self.enabled = enabled

    def _wrap(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.enabled else text

    def red(self, t: str) -> str:
        return self._wrap("31", t)

    def yellow(self, t: str) -> str:
        return self._wrap("33", t)

    def green(self, t: str) -> str:
        return self._wrap("32", t)

    def dim(self, t: str) -> str:
        return self._wrap("2", t)

    def bold(self, t: str) -> str:
        return self._wrap("1", t)


def _use_color(stream) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return hasattr(stream, "isatty") and stream.isatty()


def _load(path: str) -> EnvFile:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)
    return parse_file(p)


def _report(findings: list[Finding], fmt: str, strict: bool) -> int:
    if fmt == "json":
        print(json.dumps([f.to_dict() for f in findings], indent=2))
    else:
        style = _Style(_use_color(sys.stdout))
        for f in sorted(findings, key=lambda f: (f.file, f.line or 0, f.code)):
            loc = f"{f.file}:{f.line}" if f.line else f.file
            tag = style.red(f.code) if f.severity == ERROR else style.yellow(f.code)
            print(f"{style.bold(loc)} {tag} {f.message}")
        errors = sum(1 for f in findings if f.severity == ERROR)
        warnings = len(findings) - errors
        if findings:
            summary = f"{errors} error(s), {warnings} warning(s)"
            print(style.red(summary) if errors else style.yellow(summary))
        else:
            print(style.green("All clear."))

    if any(f.severity == ERROR for f in findings):
        return EXIT_FINDINGS
    if strict and findings:
        return EXIT_FINDINGS
    return EXIT_OK


def cmd_lint(args) -> int:
    findings: list[Finding] = []
    for path in args.files:
        findings += lint(_load(path), allow_empty=args.allow_empty)
    return _report(filter_ignored(findings, args.ignore), args.format, args.strict)


def cmd_check(args) -> int:
    env = _load(args.env)
    example = _load(args.example)
    findings = lint(env, allow_empty=args.allow_empty)
    findings += compare(env, example, allow_extra=args.allow_extra)
    findings += scan_secrets(example)
    return _report(filter_ignored(findings, args.ignore), args.format, args.strict)


def cmd_scan(args) -> int:
    findings: list[Finding] = []
    for path in args.files:
        findings += scan_secrets(_load(path))
    return _report(filter_ignored(findings, args.ignore), args.format, args.strict)


def cmd_example(args) -> int:
    text = make_example(_load(args.env))
    if args.out == "-":
        sys.stdout.write(text)
        return EXIT_OK
    out = Path(args.out)
    if out.exists() and not args.force:
        print(f"{out} already exists; pass --force to overwrite.", file=sys.stderr)
        return EXIT_USAGE
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out}")
    return EXIT_OK


def cmd_rules(args) -> int:
    for code, (severity, desc) in RULES.items():
        print(f"{code}  {severity:<7}  {desc}")
    return EXIT_OK


def _comma_list(value: str) -> list[str]:
    return [v for v in value.split(",") if v.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envsentry",
        description="Catch broken, incomplete and leaky .env files before they bite.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--format", choices=["text", "json"], default="text", help="output format")
    common.add_argument(
        "--ignore",
        type=_comma_list,
        default=[],
        metavar="CODES",
        help="comma-separated rule codes or prefixes to skip, e.g. W001,W005 or W",
    )
    common.add_argument("--strict", action="store_true", help="exit non-zero on warnings too")

    p = sub.add_parser("lint", parents=[common], help="check dotenv files for syntax and style problems")
    p.add_argument("files", nargs="*", default=[".env"], help="files to lint (default: .env)")
    p.add_argument("--allow-empty", action="store_true", help="do not warn about empty values")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser(
        "check",
        parents=[common],
        help="lint .env, compare it with .env.example and scan the example for leaked secrets",
    )
    p.add_argument("--env", default=".env", help="the real env file (default: .env)")
    p.add_argument("--example", default=".env.example", help="the template (default: .env.example)")
    p.add_argument("--allow-extra", action="store_true", help="do not warn about undocumented keys")
    p.add_argument("--allow-empty", action="store_true", help="do not warn about empty values")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("scan", parents=[common], help="look for real secrets in files you commit")
    p.add_argument("files", nargs="*", default=[".env.example"], help="files to scan (default: .env.example)")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("example", help="generate a .env.example with all values blanked")
    p.add_argument("--env", default=".env", help="source file (default: .env)")
    p.add_argument("--out", default=".env.example", help="output file, or - for stdout")
    p.add_argument("--force", action="store_true", help="overwrite the output file")
    p.set_defaults(func=cmd_example)

    p = sub.add_parser("rules", help="list every rule code")
    p.set_defaults(func=cmd_rules)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"envsentry: file not found: {exc.args[0]}", file=sys.stderr)
        return EXIT_USAGE
