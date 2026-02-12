from unittest.mock import MagicMock, patch

import pytest

from app.utils.errors import CancelledError


# test wywolania download_video_mp4 z domyslnym formatem
def test_download_video_mp4_default_format(tmp_path):
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}):
        from app.core.download import download_video_mp4
        from app.core.ytclient import YTClient

        mock_yt = MagicMock(spec=YTClient)

        download_video_mp4(
            yt=mock_yt,
            url="https://youtube.com/watch?v=TEST",
            output_dir=str(tmp_path),
        )

        mock_yt.download.assert_called_once()
        call_args = mock_yt.download.call_args
        opts = call_args[0][1]

        # sprawdz domyslny format
        assert "format" in opts
        assert "bestvideo" in opts["format"]
        assert opts["merge_output_format"] == "mp4"


# test z customowym formatem
def test_download_video_mp4_custom_format(tmp_path):
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}):
        from app.core.download import download_video_mp4
        from app.core.ytclient import YTClient

        mock_yt = MagicMock(spec=YTClient)

        download_video_mp4(
            yt=mock_yt,
            url="https://youtube.com/watch?v=TEST",
            output_dir=str(tmp_path),
            format_id="137+bestaudio",
        )

        call_args = mock_yt.download.call_args
        opts = call_args[0][1]
        assert opts["format"] == "137+bestaudio"


# test callbacku postepu
def test_download_video_mp4_progress_callback(tmp_path):
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}):
        from app.core.download import download_video_mp4
        from app.core.ytclient import YTClient

        mock_yt = MagicMock(spec=YTClient)
        progress_calls = []

        def progress_cb(pct, downloaded, total):
            progress_calls.append((pct, downloaded, total))

        download_video_mp4(
            yt=mock_yt,
            url="https://youtube.com/watch?v=TEST",
            output_dir=str(tmp_path),
            progress_cb=progress_cb,
        )

        # sprawdz ze hook zostal dodany
        call_args = mock_yt.download.call_args
        opts = call_args[0][1]
        assert "progress_hooks" in opts
        assert len(opts["progress_hooks"]) == 1


# test hook anulowania
def test_download_video_mp4_cancel():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}):
        from app.core.download import _hook

        cancelled = False

        def cancel_cb():
            return cancelled

        progress_calls = []

        def progress_cb(pct, downloaded, total):
            progress_calls.append((pct, downloaded, total))

        hook = _hook(progress_cb, cancel_cb)

        # symuluj downloading
        hook({"status": "downloading", "downloaded_bytes": 1000, "total_bytes": 10000})
        assert len(progress_calls) == 1
        assert progress_calls[0][0] == pytest.approx(10.0)

        # symuluj anulowanie
        cancelled = True
        with pytest.raises(CancelledError):
            hook(
                {
                    "status": "downloading",
                    "downloaded_bytes": 2000,
                    "total_bytes": 10000,
                }
            )


# test hook z zerowymi bajtami
def test_download_hook_zero_bytes():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}):
        from app.core.download import _hook

        progress_calls = []

        def progress_cb(pct, downloaded, total):
            progress_calls.append((pct, downloaded, total))

        hook = _hook(progress_cb, None)
        hook({"status": "downloading", "downloaded_bytes": 0, "total_bytes": 0})

        # nie powinno crashnac
        assert len(progress_calls) == 1
        assert progress_calls[0][0] == 0.0


# test hook bez total_bytes (estimate)
def test_download_hook_estimate():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}):
        from app.core.download import _hook

        progress_calls = []

        def progress_cb(pct, downloaded, total):
            progress_calls.append((pct, downloaded, total))

        hook = _hook(progress_cb, None)
        hook(
            {
                "status": "downloading",
                "downloaded_bytes": 5000,
                "total_bytes_estimate": 10000,
            }
        )

        assert progress_calls[0][0] == pytest.approx(50.0)


# test download_audio_mp3
def test_download_audio_mp3_calls_ytclient(tmp_path):
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}):
        from app.core.download import download_audio_mp3
        from app.core.ytclient import YTClient

        mock_yt = MagicMock(spec=YTClient)

        download_audio_mp3(
            yt=mock_yt, url="https://youtube.com/watch?v=TEST", output_dir=str(tmp_path)
        )

        mock_yt.download.assert_called_once()
        call_args = mock_yt.download.call_args
        opts = call_args[0][1]

        # sprawdz format audio
        assert opts["format"] == "bestaudio/best"
        assert opts["keepvideo"] is False
        # sprawdz postprocessor
        assert "postprocessors" in opts
        processor = opts["postprocessors"][0]
        assert processor["key"] == "FFmpegExtractAudio"
        assert processor["preferredcodec"] == "mp3"
        assert processor["preferredquality"] == "320"


# test download_audio_mp3 z callbackiem
def test_download_audio_mp3_with_callbacks(tmp_path):
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}):
        from app.core.download import download_audio_mp3
        from app.core.ytclient import YTClient

        mock_yt = MagicMock(spec=YTClient)
        progress_calls = []
        cancel_calls = []

        def progress_cb(pct, downloaded, total):
            progress_calls.append((pct, downloaded, total))

        def cancel_cb():
            cancel_calls.append(True)
            return False

        download_audio_mp3(
            yt=mock_yt,
            url="https://youtube.com/watch?v=TEST",
            output_dir=str(tmp_path),
            progress_cb=progress_cb,
            cancel_cb=cancel_cb,
        )

        call_args = mock_yt.download.call_args
        opts = call_args[0][1]
        assert "progress_hooks" in opts


# test hook z roznym statusem
def test_download_hook_different_status():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}):
        from app.core.download import _hook

        progress_calls = []

        def progress_cb(pct, downloaded, total):
            progress_calls.append((pct, downloaded, total))

        hook = _hook(progress_cb, None)

        # status "finished" nie powinien wywolac progress_cb
        hook({"status": "finished"})
        assert len(progress_calls) == 0

        # tylko "downloading" wywoluje callback
        hook({"status": "downloading", "downloaded_bytes": 100, "total_bytes": 1000})
        assert len(progress_calls) == 1


# test restrictfilenames option
def test_download_video_restrictfilenames(tmp_path):
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}):
        from app.core.download import download_video_mp4
        from app.core.ytclient import YTClient

        mock_yt = MagicMock(spec=YTClient)

        download_video_mp4(
            yt=mock_yt, url="https://youtube.com/watch?v=TEST", output_dir=str(tmp_path)
        )

        call_args = mock_yt.download.call_args
        opts = call_args[0][1]
        assert opts["restrictfilenames"] is True
