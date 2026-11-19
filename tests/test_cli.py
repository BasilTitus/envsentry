import json

import pytest

from envsentry.cli import main


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NO_COLOR", "1")
    (tmp_path / ".env").write_text("A=1\nB=2\n")
    (tmp_path / ".env.example").write_text("A=\nB=\n")
    return tmp_path


def test_check_passes(project, capsys):
    assert main(["check"]) == 0
    assert "All clear." in capsys.readouterr().out


def test_check_fails_on_missing_key(project, capsys):
    (project / ".env.example").write_text("A=\nB=\nC=\n")
    assert main(["check"]) == 1
    assert "E101" in capsys.readouterr().out


def test_check_fails_on_leaked_secret_in_example(project, capsys):
    (project / ".env.example").write_text("A=AKIAIOSFODNN7EXAMPLE\nB=\n")
    assert main(["check"]) == 1
    assert "S001" in capsys.readouterr().out


def test_warnings_only_fail_in_strict_mode(project):
    (project / ".env").write_text("A=1\nB=2\nlower=3\n")
    assert main(["lint"]) == 0
    assert main(["lint", "--strict"]) == 1
    assert main(["lint", "--strict", "--ignore", "W001"]) == 0


def test_json_output(project, capsys):
    (project / ".env").write_text("A=1\nA=2\n")
    assert main(["lint", "--format", "json"]) == 1
    data = json.loads(capsys.readouterr().out)
    assert data[0]["code"] == "E003"
    assert data[0]["severity"] == "error"
    assert data[0]["line"] == 2


def test_missing_file_is_usage_error(project, capsys):
    assert main(["lint", "nope.env"]) == 2
    assert "file not found" in capsys.readouterr().err


def test_example_command(project, capsys):
    (project / ".env").write_text("# hi\nSECRET=shh\n")
    assert main(["example"]) == 2  # refuses to overwrite
    assert main(["example", "--force"]) == 0
    assert (project / ".env.example").read_text() == "# hi\nSECRET=\n"
    assert main(["example", "--out", "-"]) == 0
    assert "SECRET=" in capsys.readouterr().out


def test_rules_lists_codes(capsys):
    assert main(["rules"]) == 0
    assert "S001" in capsys.readouterr().out
