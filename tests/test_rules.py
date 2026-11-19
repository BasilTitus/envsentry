import pytest

from envsentry import compare, lint, make_example, parse_text, scan_secrets
from envsentry.rules import filter_ignored


def codes(findings):
    return sorted(f.code for f in findings)


def test_clean_file_has_no_findings():
    assert lint(parse_text('A=1\nB="two words"\n')) == []


@pytest.mark.parametrize(
    "text, code",
    [
        ("nonsense\n", "E001"),
        ("1BAD=x\n", "E002"),
        ("A=1\nA=2\n", "E003"),
        ('A="open\n', "E004"),
        ("lower=x\n", "W001"),
        ("A = x\n", "W002"),
        ("A=two words\n", "W003"),
        ("A=x   \n", "W004"),
        ("A=\n", "W005"),
    ],
)
def test_each_lint_rule(text, code):
    assert code in codes(lint(parse_text(text)))


def test_allow_empty_and_quoted_empty():
    assert lint(parse_text("A=\n"), allow_empty=True) == []
    assert lint(parse_text('A=""\n')) == []


def test_compare_missing_and_extra():
    env = parse_text("A=1\nEXTRA=2\n")
    example = parse_text("A=\nB=\n")
    assert codes(compare(env, example)) == ["E101", "W101"]
    assert codes(compare(env, example, allow_extra=True)) == ["E101"]


def test_scan_finds_known_formats():
    token = "ghp_" + "a1B2c3D4" * 5
    env = parse_text(
        f"AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\nGH={token}\n"
        "DATABASE_URL=postgres://admin:hunter22@db:5432/app\n"
    )
    assert codes(scan_secrets(env)) == ["S001", "S001", "S001"]


def test_scan_finds_high_entropy_sensitive_key():
    env = parse_text("SESSION_SECRET=q8Zr2LkP0vWm9XtB4nHc7YsE\n")
    assert codes(scan_secrets(env)) == ["S001"]


@pytest.mark.parametrize(
    "line",
    [
        "API_KEY=",
        "API_KEY=changeme",
        "API_KEY=your-api-key-here",
        "API_KEY=<insert key>",
        "PASSWORD=${DB_PASSWORD}",
        "DATABASE_URL=postgres://localhost:5432/app",
        "DEBUG=true",
        "PORT=8080",
    ],
)
def test_scan_ignores_placeholders(line):
    assert scan_secrets(parse_text(line + "\n")) == []


def test_filter_ignored_by_code_and_prefix():
    findings = lint(parse_text("lower = two words\n"))
    assert codes(filter_ignored(findings, ["W001"])) == ["W002", "W003"]
    assert filter_ignored(findings, ["W"]) == []


def test_make_example_blanks_values_and_keeps_comments():
    env = parse_text('# Database\nDB_URL="postgres://u:p@h/db"\nexport TOKEN=abc\n\nPORT=80\n')
    assert make_example(env) == "# Database\nDB_URL=\nexport TOKEN=\n\nPORT=\n"
