import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.paths import ensure_output_dir, get_ffmpeg_path, outtmpl_for
from app.utils.errors import DependencyMissingError


# test pobierania sciezki ffmpeg ze zmiennej srodowiskowej
def test_get_ffmpeg_path_from_env(tmp_path, monkeypatch):
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}):
        fake_ffmpeg = tmp_path / "ffmpeg.exe"
        fake_ffmpeg.touch()
        monkeypatch.setenv("FFMPEG_PATH", str(fake_ffmpeg))

        result = get_ffmpeg_path()
        assert result == str(fake_ffmpeg)


# test fallback na imageio_ffmpeg
def test_get_ffmpeg_path_from_imageio(monkeypatch):
    monkeypatch.delenv("FFMPEG_PATH", raising=False)

    with patch.dict("sys.modules", {"imageio_ffmpeg": MagicMock()}) as mock_modules:
        mock_imageio = mock_modules["imageio_ffmpeg"]
        mock_imageio.get_ffmpeg_exe.return_value = "/path/to/ffmpeg"
        result = get_ffmpeg_path()
        assert result == "/path/to/ffmpeg"
        mock_imageio.get_ffmpeg_exe.assert_called_once()


# test bledu gdy brak imageio_ffmpeg
def test_get_ffmpeg_path_missing_dependency(monkeypatch):
    monkeypatch.delenv("FFMPEG_PATH", raising=False)

    # Remove from sys.modules if present
    with patch.dict("sys.modules"):
        sys.modules.pop("imageio_ffmpeg", None)

        import builtins

        orig_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "imageio_ffmpeg":
                raise ImportError("No module")
            return orig_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(DependencyMissingError):
                get_ffmpeg_path()


# test env var z nieistniejacym plikiem (fallback na imageio)
def test_get_ffmpeg_path_env_nonexistent(monkeypatch):
    monkeypatch.setenv("FFMPEG_PATH", "/nonexistent/path/ffmpeg.exe")

    with patch.dict("sys.modules", {"imageio_ffmpeg": MagicMock()}) as mock_modules:
        mock_imageio = mock_modules["imageio_ffmpeg"]
        mock_imageio.get_ffmpeg_exe.return_value = "/fallback/ffmpeg"
        result = get_ffmpeg_path()
        # powinna uzyc fallback bo plik nie istnieje
        assert result == "/fallback/ffmpeg"


# test tworzenia katalogu wyjsciowego
def test_ensure_output_dir_creates(tmp_path):
    new_dir = tmp_path / "output" / "nested"
    result = ensure_output_dir(new_dir)

    assert result.exists()
    assert result.is_dir()
    assert result == new_dir.resolve()


# test z istniejacym katalogiem
def test_ensure_output_dir_existing(tmp_path):
    existing_dir = tmp_path / "existing"
    existing_dir.mkdir()

    result = ensure_output_dir(existing_dir)
    assert result.exists()
    assert result == existing_dir.resolve()


# test rozwijania ~
def test_ensure_output_dir_expands_user(monkeypatch):
    with patch("pathlib.Path.home") as mock_home:
        mock_home.return_value = Path("/home/user")
        # Path.expanduser jest wywolywane wewnetrznie
        result = ensure_output_dir("~/test")
        assert "test" in str(result)


# test tworzenia wzoru dla yt-dlp
def test_outtmpl_for_format(tmp_path):
    result = outtmpl_for(tmp_path)

    # powinien zawierac sciezke do katalogu i wzor yt-dlp
    assert str(tmp_path) in result
    assert "%(title)s.%(ext)s" in result


# test ze outtmpl tworzy katalog
def test_outtmpl_for_creates_dir(tmp_path):
    new_dir = tmp_path / "downloads"
    result = outtmpl_for(new_dir)

    assert new_dir.exists()
    assert str(new_dir) in result


# test formatu wyjsciowego outtmpl
def test_outtmpl_for_output_format(tmp_path):
    result = outtmpl_for(tmp_path)
    expected_suffix = "%(title)s.%(ext)s"

    assert result.endswith(expected_suffix)


# test z path jako string
def test_outtmpl_for_string_path(tmp_path):
    result = outtmpl_for(str(tmp_path))
    assert isinstance(result, str)
    assert str(tmp_path) in result


# test z path jako Path
def test_outtmpl_for_path_object(tmp_path):
    result = outtmpl_for(tmp_path)
    assert isinstance(result, str)
    assert str(tmp_path) in result
