from core import utils


def test_text_sanitise():
    assert "a\\*b" == utils.Text.sanitise("a*b")
    assert "a\\_b" == utils.Text.sanitise("a_b")


def test_text_split():
    assert ["abc", "def"] == utils.Text.split("abcdef", limit=3)
    assert ["abcd", "efgh"] == utils.Text.split("abcdefgh", limit=4)


def test_text_split_lines():
    assert ["ab\ncd", "ef\ng"] == utils.Text.split_lines(
        ["ab", "cd", "ef", "g"], limit=5
    )
    assert ["abc\ndef", "g"] == utils.Text.split_lines(["abc", "def", "g"], limit=7)


def test_time_seconds():
    assert "0:32" == utils.Time.seconds(32)
    assert "12:34" == utils.Time.seconds(12 * 60 + 34)
    assert "1:23:45" == utils.Time.seconds(3600 + 23 * 60 + 45)
    assert "12 d, 13:14:15" == utils.Time.seconds(
        12 * 24 * 3600 + 13 * 3600 + 14 * 60 + 15
    )
