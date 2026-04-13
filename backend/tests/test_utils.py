"""
Unit tests for crud._utils helper functions.
"""
from crud._utils import escape_like


class TestEscapeLike:
    def test_plain_string_unchanged(self):
        assert escape_like("hello") == "hello"

    def test_empty_string_unchanged(self):
        assert escape_like("") == ""

    def test_percent_escaped(self):
        assert escape_like("100%") == "100\\%"

    def test_underscore_escaped(self):
        assert escape_like("file_name") == "file\\_name"

    def test_backslash_escaped(self):
        assert escape_like("C:\\path") == "C:\\\\path"

    def test_backslash_escaped_before_percent(self):
        # backslash must be escaped first; a literal \% must become \\\\\\%
        assert escape_like("\\%") == "\\\\\\%"

    def test_all_special_chars_combined(self):
        assert escape_like("%_\\") == "\\%\\_\\\\"

    def test_multiple_occurrences(self):
        assert escape_like("a%b%c") == "a\\%b\\%c"
