from envsentry import parse_text


def test_basic_assignments_and_comments():
    env = parse_text("# comment\n\nFOO=bar\nexport BAZ=qux\n")
    assert env.as_dict() == {"FOO": "bar", "BAZ": "qux"}
    assert env.get("BAZ").exported
    assert env.get("FOO").line == 3


def test_quoted_values():
    env = parse_text('A="hello world"\nB=\'single # not comment\'\nC="line\\nbreak"\n')
    assert env.get("A").value == "hello world"
    assert env.get("A").quote == '"'
    assert env.get("B").value == "single # not comment"
    assert env.get("C").value == "line\nbreak"


def test_inline_comment_on_unquoted_value():
    env = parse_text("PORT=8080 # the port\nCOLOR=#fff\n")
    assert env.get("PORT").value == "8080"
    assert env.get("COLOR").value == "#fff"


def test_value_may_contain_equals():
    env = parse_text("URL=postgres://h/db?sslmode=require\n")
    assert env.get("URL").value == "postgres://h/db?sslmode=require"


def test_bad_lines_and_unterminated_quotes_do_not_raise():
    env = parse_text('just some text\nX="oops\n')
    assert [b.line for b in env.bad_lines] == [1]
    assert env.get("X").unterminated_quote


def test_space_around_equals_detected():
    assert parse_text("A = 1\n").get("A").space_around_equals
    assert not parse_text("A=1\n").get("A").space_around_equals


def test_last_assignment_wins():
    assert parse_text("A=1\nA=2\n").as_dict() == {"A": "2"}
