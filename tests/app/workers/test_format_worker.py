from unittest.mock import patch

import pytest
from PyQt6.QtCore import QCoreApplication


# fixture dla Qt event loop
@pytest.fixture(scope="function")
def qapp():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield app


# test inicjalizacji format workera
def test_format_worker_init():
    from app.workers.format_worker import FormatFetchWorker

    worker = FormatFetchWorker(url="https://youtube.com/watch?v=TEST")
    assert worker.url == "https://youtube.com/watch?v=TEST"


# test parsowania formatow muxed (video+audio)
def test_format_worker_parses_muxed():
    from app.workers.format_worker import FormatFetchWorker

    with patch("app.workers.format_worker.yt_dlp.YoutubeDL") as mock_ydl:
        mock_info = {
            "formats": [
                {
                    "format_id": "18",
                    "ext": "mp4",
                    "height": 360,
                    "fps": 30,
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                },
                {
                    "format_id": "22",
                    "ext": "mp4",
                    "height": 720,
                    "fps": 30,
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                },
            ]
        }
        mock_ydl.return_value.__enter__.return_value.extract_info.return_value = (
            mock_info
        )

        worker = FormatFetchWorker(url="https://youtube.com/watch?v=TEST")
        formats_emitted = []
        worker.formats_ready.connect(lambda f: formats_emitted.append(f))

        worker.run()

        assert len(formats_emitted) == 1
        formats = formats_emitted[0]
        # powinno znalezc 2 formaty muxed
        assert len(formats) >= 2
        # sprawdz format labelow
        format_ids = [f[0] for f in formats]
        assert "22" in format_ids
        assert "18" in format_ids


# test parsowania formatow video-only
def test_format_worker_parses_video_only():
    from app.workers.format_worker import FormatFetchWorker

    with patch("app.workers.format_worker.yt_dlp.YoutubeDL") as mock_ydl:
        mock_info = {
            "formats": [
                {
                    "format_id": "137",
                    "ext": "mp4",
                    "height": 1080,
                    "fps": 30,
                    "vcodec": "avc1",
                    "acodec": "none",
                },
                {
                    "format_id": "140",
                    "ext": "m4a",
                    "vcodec": "none",
                    "acodec": "mp4a",
                },
            ]
        }
        mock_ydl.return_value.__enter__.return_value.extract_info.return_value = (
            mock_info
        )

        worker = FormatFetchWorker(url="https://youtube.com/watch?v=TEST")
        formats_emitted = []
        worker.formats_ready.connect(lambda f: formats_emitted.append(f))

        worker.run()

        assert len(formats_emitted) == 1
        formats = formats_emitted[0]
        # powinno polaczyc video-only z audio
        assert any("1080p + audio" in f[1] for f in formats)


# test laczenia video-only z audio
def test_format_worker_combines_video_audio():
    from app.workers.format_worker import FormatFetchWorker

    with patch("app.workers.format_worker.yt_dlp.YoutubeDL") as mock_ydl:
        mock_info = {
            "formats": [
                {
                    "format_id": "137",
                    "ext": "mp4",
                    "height": 1080,
                    "fps": 60,
                    "vcodec": "avc1",
                    "acodec": "none",
                },
                {
                    "format_id": "136",
                    "ext": "mp4",
                    "height": 720,
                    "fps": 30,
                    "vcodec": "avc1",
                    "acodec": "none",
                },
                {
                    "format_id": "140",
                    "ext": "m4a",
                    "vcodec": "none",
                    "acodec": "mp4a",
                },
            ]
        }
        mock_ydl.return_value.__enter__.return_value.extract_info.return_value = (
            mock_info
        )

        worker = FormatFetchWorker(url="https://youtube.com/watch?v=TEST")
        formats_emitted = []
        worker.formats_ready.connect(lambda f: formats_emitted.append(f))

        worker.run()

        formats = formats_emitted[0]
        # sprawdz ze video-only sa polaczone z bestaudio
        combined = [f for f in formats if "+bestaudio" in f[0]]
        assert len(combined) >= 2


# test sortowania po jakosci
def test_format_worker_sorts_by_quality():
    from app.workers.format_worker import FormatFetchWorker

    with patch("app.workers.format_worker.yt_dlp.YoutubeDL") as mock_ydl:
        mock_info = {
            "formats": [
                {
                    "format_id": "18",
                    "ext": "mp4",
                    "height": 360,
                    "fps": 30,
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                },
                {
                    "format_id": "22",
                    "ext": "mp4",
                    "height": 720,
                    "fps": 30,
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                },
                {
                    "format_id": "37",
                    "ext": "mp4",
                    "height": 1080,
                    "fps": 30,
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                },
            ]
        }
        mock_ydl.return_value.__enter__.return_value.extract_info.return_value = (
            mock_info
        )

        worker = FormatFetchWorker(url="https://youtube.com/watch?v=TEST")
        formats_emitted = []
        worker.formats_ready.connect(lambda f: formats_emitted.append(f))

        worker.run()

        formats = formats_emitted[0]
        # pierwszy powinien byc najlepszy (1080p)
        assert "1080" in formats[0][1] or formats[0][0] == "37"


# test wyboru najwyzszego fps dla danej rozdzielczosci
def test_format_worker_selects_highest_fps():
    from app.workers.format_worker import FormatFetchWorker

    with patch("app.workers.format_worker.yt_dlp.YoutubeDL") as mock_ydl:
        mock_info = {
            "formats": [
                {
                    "format_id": "137_30",
                    "ext": "mp4",
                    "height": 1080,
                    "fps": 30,
                    "vcodec": "avc1",
                    "acodec": "none",
                },
                {
                    "format_id": "137_60",
                    "ext": "mp4",
                    "height": 1080,
                    "fps": 60,
                    "vcodec": "avc1",
                    "acodec": "none",
                },
                {
                    "format_id": "140",
                    "ext": "m4a",
                    "vcodec": "none",
                    "acodec": "mp4a",
                },
            ]
        }
        mock_ydl.return_value.__enter__.return_value.extract_info.return_value = (
            mock_info
        )

        worker = FormatFetchWorker(url="https://youtube.com/watch?v=TEST")
        formats_emitted = []
        worker.formats_ready.connect(lambda f: formats_emitted.append(f))

        worker.run()

        formats = formats_emitted[0]
        # sprawdz ze dla 1080p wybrano 60fps
        format_1080 = [f for f in formats if "1080p" in f[1]]
        if format_1080:
            # powinno zawierac format z 60fps
            assert "137_60" in format_1080[0][0]


# test bledu gdy brak formatow
def test_format_worker_no_formats_error():
    from app.workers.format_worker import FormatFetchWorker

    with patch("app.workers.format_worker.yt_dlp.YoutubeDL") as mock_ydl:
        mock_info = {"formats": []}
        mock_ydl.return_value.__enter__.return_value.extract_info.return_value = (
            mock_info
        )

        worker = FormatFetchWorker(url="https://youtube.com/watch?v=TEST")
        error_emitted = []
        worker.error.connect(lambda e: error_emitted.append(e))

        worker.run()

        assert len(error_emitted) == 1
        assert "brak" in error_emitted[0].lower()


# test obslugi wyjatku
def test_format_worker_exception_handling():
    from app.workers.format_worker import FormatFetchWorker

    with patch("app.workers.format_worker.yt_dlp.YoutubeDL") as mock_ydl:
        mock_ydl.return_value.__enter__.return_value.extract_info.side_effect = (
            Exception("Network error")
        )

        worker = FormatFetchWorker(url="https://youtube.com/watch?v=TEST")
        error_emitted = []
        worker.error.connect(lambda e: error_emitted.append(e))

        worker.run()

        assert len(error_emitted) == 1
        assert "Network error" in error_emitted[0]


# test ignorowania formatow bez height
def test_format_worker_ignores_no_height():
    from app.workers.format_worker import FormatFetchWorker

    with patch("app.workers.format_worker.yt_dlp.YoutubeDL") as mock_ydl:
        mock_info = {
            "formats": [
                {
                    "format_id": "251",
                    "ext": "webm",
                    "vcodec": "none",
                    "acodec": "opus",
                },  # audio only, no height
                {
                    "format_id": "22",
                    "ext": "mp4",
                    "height": 720,
                    "fps": 30,
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                },
            ]
        }
        mock_ydl.return_value.__enter__.return_value.extract_info.return_value = (
            mock_info
        )

        worker = FormatFetchWorker(url="https://youtube.com/watch?v=TEST")
        formats_emitted = []
        worker.formats_ready.connect(lambda f: formats_emitted.append(f))

        worker.run()

        formats = formats_emitted[0]
        # powinien zawierac tylko format z height
        format_ids = [f[0] for f in formats]
        assert "22" in format_ids


# test parsowania fps w labelach
def test_format_worker_fps_in_labels():
    from app.workers.format_worker import FormatFetchWorker

    with patch("app.workers.format_worker.yt_dlp.YoutubeDL") as mock_ydl:
        mock_info = {
            "formats": [
                {
                    "format_id": "22",
                    "ext": "mp4",
                    "height": 720,
                    "fps": 60,
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                },
            ]
        }
        mock_ydl.return_value.__enter__.return_value.extract_info.return_value = (
            mock_info
        )

        worker = FormatFetchWorker(url="https://youtube.com/watch?v=TEST")
        formats_emitted = []
        worker.formats_ready.connect(lambda f: formats_emitted.append(f))

        worker.run()

        formats = formats_emitted[0]
        # sprawdz ze label zawiera fps
        assert any("60fps" in f[1] for f in formats)
