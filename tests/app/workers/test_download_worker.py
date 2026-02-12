from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import QCoreApplication

from app.utils.errors import CancelledError


# fixture dla Qt event loop
@pytest.fixture(scope="function")
def qapp():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield app


# test inicjalizacji download workera
def test_download_worker_init():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}), patch(
        "app.core.paths.get_ffmpeg_path", return_value="/mock/ffmpeg"
    ):
        from app.workers.download_worker import DownloadWorker

        worker = DownloadWorker(
            url="https://youtube.com/watch?v=TEST",
            folder="/output",
            download_type="mp4",
            format_id="137+bestaudio",
        )

        assert worker.url == "https://youtube.com/watch?v=TEST"
        assert worker.folder == "/output"
        assert worker.download_type == "mp4"
        assert worker.format_id == "137+bestaudio"
        assert worker._cancelled is False


# test anulowania
def test_download_worker_cancel():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}), patch(
        "app.core.paths.get_ffmpeg_path", return_value="/mock/ffmpeg"
    ):
        from app.workers.download_worker import DownloadWorker

        worker = DownloadWorker(
            url="https://youtube.com/watch?v=TEST",
            folder="/output",
            download_type="mp3",
            format_id=None,
        )

        assert worker._cancelled is False
        worker.cancel()
        assert worker._cancelled is True


# test callbacku postepu
def test_download_worker_on_progress():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}), patch(
        "app.core.paths.get_ffmpeg_path", return_value="/mock/ffmpeg"
    ):
        from app.workers.download_worker import DownloadWorker

        worker = DownloadWorker(
            url="https://youtube.com/watch?v=TEST",
            folder="/output",
            download_type="mp4",
            format_id="22",
        )

        # mockuj sygnaly
        progress_emitted = []
        log_emitted = []
        worker.progress_signal.connect(lambda v: progress_emitted.append(v))
        worker.log_signal.connect(lambda m: log_emitted.append(m))

        worker._on_progress(50.5, 5_000_000, 10_000_000)

        assert len(progress_emitted) == 1
        assert progress_emitted[0] == pytest.approx(50.5)
        assert len(log_emitted) == 1
        assert "50.5%" in log_emitted[0]
        assert "5.0" in log_emitted[0]  # MB
        assert "10.0" in log_emitted[0]  # MB


# test callbacku postepu bez total
def test_download_worker_on_progress_no_total():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}), patch(
        "app.core.paths.get_ffmpeg_path", return_value="/mock/ffmpeg"
    ):
        from app.workers.download_worker import DownloadWorker

        worker = DownloadWorker(
            url="https://youtube.com/watch?v=TEST",
            folder="/output",
            download_type="mp3",
            format_id=None,
        )

        log_emitted = []
        worker.log_signal.connect(lambda m: log_emitted.append(m))

        worker._on_progress(25.0, 0, 0)

        assert len(log_emitted) == 1
        assert "25.0%" in log_emitted[0]


# test sprawdzania anulowania
def test_download_worker_is_cancelled():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}), patch(
        "app.core.paths.get_ffmpeg_path", return_value="/mock/ffmpeg"
    ):
        from app.workers.download_worker import DownloadWorker

        worker = DownloadWorker(
            url="https://youtube.com/watch?v=TEST",
            folder="/output",
            download_type="mp4",
            format_id="best",
        )

        assert worker._is_cancelled() is False
        worker.cancel()
        assert worker._is_cancelled() is True


# test sukcesu pobierania mp3
def test_download_worker_mp3_success():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}), patch(
        "app.core.paths.get_ffmpeg_path", return_value="/mock/ffmpeg"
    ):
        from app.workers.download_worker import DownloadWorker

        with patch("app.workers.download_worker.download_audio_mp3") as mock_download:
            worker = DownloadWorker(
                url="https://youtube.com/watch?v=TEST",
                folder="/output",
                download_type="mp3",
                format_id=None,
            )

            finished_calls = []
            worker.finished_signal.connect(lambda s, e: finished_calls.append((s, e)))

            worker.run()

            assert len(finished_calls) == 1
            success, error = finished_calls[0]
            assert success is True
            assert error == ""
            mock_download.assert_called_once()


# test sukcesu pobierania mp4
def test_download_worker_mp4_success():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}), patch(
        "app.core.paths.get_ffmpeg_path", return_value="/mock/ffmpeg"
    ):
        from app.workers.download_worker import DownloadWorker

        with patch("app.workers.download_worker.download_video_mp4") as mock_download:
            worker = DownloadWorker(
                url="https://youtube.com/watch?v=TEST",
                folder="/output",
                download_type="mp4",
                format_id="137+bestaudio",
            )

            finished_calls = []
            worker.finished_signal.connect(lambda s, e: finished_calls.append((s, e)))

            worker.run()

            assert len(finished_calls) == 1
            success, error = finished_calls[0]
            assert success is True
            assert error == ""
            mock_download.assert_called_once()


# test obslugi anulowania
def test_download_worker_cancelled():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}), patch(
        "app.core.paths.get_ffmpeg_path", return_value="/mock/ffmpeg"
    ):
        from app.workers.download_worker import DownloadWorker

        with patch(
            "app.workers.download_worker.download_video_mp4",
            side_effect=CancelledError("User cancelled"),
        ):
            worker = DownloadWorker(
                url="https://youtube.com/watch?v=TEST",
                folder="/output",
                download_type="mp4",
                format_id="best",
            )

            finished_calls = []
            worker.finished_signal.connect(lambda s, e: finished_calls.append((s, e)))

            worker.run()

            assert len(finished_calls) == 1
            success, error = finished_calls[0]
            assert success is False
            assert "anulowane" in error.lower()


# test obslugi bledu
def test_download_worker_error():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}), patch(
        "app.core.paths.get_ffmpeg_path", return_value="/mock/ffmpeg"
    ):
        from app.workers.download_worker import DownloadWorker

        with patch(
            "app.workers.download_worker.download_audio_mp3",
            side_effect=Exception("Network error"),
        ):
            worker = DownloadWorker(
                url="https://youtube.com/watch?v=TEST",
                folder="/output",
                download_type="mp3",
                format_id=None,
            )

            finished_calls = []
            worker.finished_signal.connect(lambda s, e: finished_calls.append((s, e)))

            worker.run()

            assert len(finished_calls) == 1
            success, error = finished_calls[0]
            assert success is False
            assert "Network error" in error


# test sygnalow cancel_requested
def test_download_worker_cancel_signal():
    with patch.dict("sys.modules", {"yt_dlp": MagicMock()}), patch(
        "app.core.paths.get_ffmpeg_path", return_value="/mock/ffmpeg"
    ):
        from app.workers.download_worker import DownloadWorker

        worker = DownloadWorker(
            url="https://youtube.com/watch?v=TEST",
            folder="/output",
            download_type="mp4",
            format_id="best",
        )

        cancel_emitted = []
        worker.cancel_requested.connect(lambda: cancel_emitted.append(True))

        worker.cancel()
        assert len(cancel_emitted) == 1
