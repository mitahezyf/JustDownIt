import sys
from unittest.mock import MagicMock, patch

import pytest

from app.utils.errors import DependencyMissingError


# test inicjalizacji ytclient
def test_ytclient_init():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}):
        from app.core.ytclient import YTClient

        client = YTClient(ffmpeg_path="/path/to/ffmpeg", proxy=None)
        assert client.ffmpeg_path == "/path/to/ffmpeg"
        assert client.proxy is None


# test inicjalizacji z proxy
def test_ytclient_init_with_proxy():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}):
        from app.core.ytclient import YTClient

        client = YTClient(ffmpeg_path="/path", proxy="http://proxy:8080")
        assert client.proxy == "http://proxy:8080"


# test bledu gdy brak yt-dlp
# test bledu gdy brak yt-dlp
def test_ytclient_missing_ytdlp():
    # Musimy usunac yt_dlp z sys.modules i zablokowac ponowny import
    with patch.dict("sys.modules"):
        sys.modules.pop("yt_dlp", None)

        import builtins

        orig_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "yt_dlp":
                raise ImportError("No module")
            return orig_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            from app.core.ytclient import YTClient

            with pytest.raises(DependencyMissingError):
                YTClient(ffmpeg_path="/path")


# test domyslnych opcji
def test_ytclient_base_opts_default():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}):
        from app.core.ytclient import YTClient

        client = YTClient(ffmpeg_path="/ffmpeg")
        opts = client._base_opts()

        assert opts["ffmpeg_location"] == "/ffmpeg"
        assert opts["no-mtime"] is True
        assert opts["quiet"] is True
        assert opts["no_warnings"] is True
        assert opts["ratelimit"] == 25_000_000
        assert opts["retries"] == 3
        assert opts["no_check_certificate"] is True


# test opcji z proxy
def test_ytclient_base_opts_with_proxy():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}):
        from app.core.ytclient import YTClient

        client = YTClient(ffmpeg_path="/ffmpeg", proxy="http://proxy:8080")
        opts = client._base_opts()

        assert opts["proxy"] == "http://proxy:8080"


# test opcji z dodatkowymi parametrami
def test_ytclient_base_opts_with_extra():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}):
        from app.core.ytclient import YTClient

        client = YTClient(ffmpeg_path="/ffmpeg")
        extra = {"custom_option": "value", "another": 123}
        opts = client._base_opts(extra)

        assert opts["custom_option"] == "value"
        assert opts["another"] == 123
        # domyslne powinny byc nadal
        assert opts["quiet"] is True


# test nadpisywania domyslnych opcji przez extra
def test_ytclient_base_opts_override():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}):
        from app.core.ytclient import YTClient

        client = YTClient(ffmpeg_path="/ffmpeg")
        extra = {"ratelimit": 50_000_000}
        opts = client._base_opts(extra)

        assert opts["ratelimit"] == 50_000_000


# test wywolania download
def test_ytclient_download_calls_ytdlp():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}) as mock_modules:
        mock_ytdlp = mock_modules["yt_dlp"]
        from app.core.ytclient import YTClient

        mock_ydl = MagicMock()
        mock_ytdlp.YoutubeDL.return_value.__enter__.return_value = mock_ydl

        client = YTClient(ffmpeg_path="/ffmpeg")
        client.download("https://youtube.com/watch?v=TEST", {"format": "best"})

        mock_ydl.download.assert_called_once_with(["https://youtube.com/watch?v=TEST"])


# test wywolania extract
def test_ytclient_extract_returns_info():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}) as mock_modules:
        mock_ytdlp = mock_modules["yt_dlp"]
        from app.core.ytclient import YTClient

        mock_ydl = MagicMock()
        mock_info = {"id": "TEST", "title": "Test Video"}
        mock_ydl.extract_info.return_value = mock_info
        mock_ytdlp.YoutubeDL.return_value.__enter__.return_value = mock_ydl

        client = YTClient(ffmpeg_path="/ffmpeg")
        result = client.extract("https://youtube.com/watch?v=TEST")

        assert result == mock_info
        mock_ydl.extract_info.assert_called_once_with(
            "https://youtube.com/watch?v=TEST", download=False
        )


# test extract z domyslnymi opcjami
def test_ytclient_extract_default_options():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}) as mock_modules:
        mock_ytdlp = mock_modules["yt_dlp"]
        from app.core.ytclient import YTClient

        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {}
        mock_ytdlp.YoutubeDL.return_value.__enter__.return_value = mock_ydl

        client = YTClient(ffmpeg_path="/ffmpeg")
        client.extract("https://youtube.com/watch?v=TEST")

        # sprawdz ze skip_download jest w opcjach
        call_args = mock_ytdlp.YoutubeDL.call_args[0][0]
        assert "skip_download" in call_args


# test extract z customowymi opcjami
def test_ytclient_extract_custom_options():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}) as mock_modules:
        mock_ytdlp = mock_modules["yt_dlp"]
        from app.core.ytclient import YTClient

        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {}
        mock_ytdlp.YoutubeDL.return_value.__enter__.return_value = mock_ydl

        client = YTClient(ffmpeg_path="/ffmpeg")
        client.extract("https://youtube.com/watch?v=TEST", {"custom": "option"})

        call_args = mock_ytdlp.YoutubeDL.call_args[0][0]
        assert "custom" in call_args


# test dostepu do errors property
def test_ytclient_errors_property():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}) as mock_modules:
        mock_ytdlp = mock_modules["yt_dlp"]
        from app.core.ytclient import YTClient

        mock_ytdlp.utils = MagicMock()
        client = YTClient(ffmpeg_path="/ffmpeg")

        errors = client.errors
        assert errors == mock_ytdlp.utils
