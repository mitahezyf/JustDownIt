from pathlib import Path

import pytest

from app.utils.filename import safe_filename, with_dir


# test usuwania nielegalnych znakow z nazwy pliku
def test_safe_filename_removes_illegal_chars():
    assert safe_filename("file<name>test") == "file name test"
    assert safe_filename("test:file|name") == "test file name"
    assert safe_filename('file"name*test') == "file name test"
    assert safe_filename("test/file\\name") == "test file name"
    assert safe_filename("file?name<test>") == "file name test"


# test normalizacji whitespace (wiele spacji -> jedna)
def test_safe_filename_normalizes_whitespace():
    assert safe_filename("file   name   test") == "file name test"
    assert safe_filename("file\t\tname") == "file name"
    assert safe_filename("file\n\nname") == "file name"


# test usuwania kropek i spacji z poczatku i konca
def test_safe_filename_strips_dots_and_spaces():
    assert safe_filename("  filename  ") == "filename"
    assert safe_filename("..filename..") == "filename"
    assert safe_filename(". . filename . .") == "filename"


# test obcinania za dlugich nazw
def test_safe_filename_truncates_long():
    long_name = "a" * 200
    result = safe_filename(long_name)
    assert len(result) <= 180
    assert result == "a" * 180


# test obcinania z zachowaniem calosci slow
def test_safe_filename_truncates_at_word():
    long_name = "word " * 50  # 250 znakow
    result = safe_filename(long_name)
    assert len(result) <= 180
    # nie powinno konczyc sie spacja
    assert not result.endswith(" ")


# test fallback na "untitled" dla pustego stringa
def test_safe_filename_fallback_untitled():
    assert safe_filename("") == "untitled"
    assert safe_filename("   ") == "untitled"
    assert safe_filename("...") == "untitled"
    assert safe_filename("<>:|?*") == "untitled"


# test customowego max_len
def test_safe_filename_custom_max_len():
    long_name = "a" * 100
    result = safe_filename(long_name, max_len=50)
    assert len(result) <= 50


# test tworzenia pelnej sciezki z katalogiem
def test_with_dir_creates_path(tmp_path):
    result = with_dir(tmp_path, "testfile", "mp4")
    assert result == tmp_path / "testfile.mp4"


# test tworzenia katalogu jesli nie istnieje
def test_with_dir_creates_directory(tmp_path):
    new_dir = tmp_path / "subdir" / "nested"
    result = with_dir(new_dir, "file", "txt")
    assert new_dir.exists()
    assert result == new_dir / "file.txt"


# test sanityzacji nazwy w with_dir
def test_with_dir_sanitizes_filename(tmp_path):
    result = with_dir(tmp_path, "bad<name>file", "mp3")
    assert result == tmp_path / "bad name file.mp3"


# test rozszerzenia z kropka i bez
def test_with_dir_extension_formats(tmp_path):
    result1 = with_dir(tmp_path, "file", "mp4")
    result2 = with_dir(tmp_path, "file", ".mp4")
    assert result1 == result2
    assert str(result1).endswith(".mp4")


# test rozwijania sciezki uzytkownika (~)
def test_with_dir_expands_user_path():
    # uzywamy Path.home() zamiast ~ bo ~ moze nie dzialac w testach

    home = Path.home()
    result = with_dir("~", "file", "txt")
    assert result.parent == home


# test parametryzowany dla roznych nielegalnych znakow
@pytest.mark.parametrize(
    "input_name,expected",
    [
        ("normal_file", "normal_file"),
        ("file with spaces", "file with spaces"),
        ("file<>test", "file test"),
        ("file:test|name", "file test name"),
        ('file"test*name', "file test name"),
        ("file/test\\name", "file test name"),
        ("file?test", "file test"),
        ("", "untitled"),
    ],
)
def test_safe_filename_parametrized(input_name, expected):
    assert safe_filename(input_name) == expected
