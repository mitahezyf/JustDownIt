from unittest.mock import MagicMock, patch


# test inicjalizacji playlist formats worker
def test_playlist_formats_worker_init():
    from app.workers.playlist_formats_worker import PlaylistFormatsWorker

    entries = [
        {"url": "https://youtube.com/watch?v=1"},
        {"url": "https://youtube.com/watch?v=2"},
    ]
    worker = PlaylistFormatsWorker(entries)

    assert worker.entries == entries


# test emitowania row_ready dla kazdego elementu
def test_playlist_formats_worker_emits_row_ready():
    from app.workers.playlist_formats_worker import PlaylistFormatsWorker

    mock_ydl = MagicMock()
    mock_info = {
        "duration": 120,
        "thumbnails": [
            {"url": "http://example.com/thumb.jpg", "width": 1280, "height": 720}
        ],
        "formats": [
            {
                "format_id": "18",
                "ext": "mp4",
                "vcodec": "avc1",
                "acodec": "mp4a",
                "height": 360,
                "fps": 30,
            }
        ],
    }
    mock_ydl.extract_info.return_value = mock_info

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        entries = [{"url": "https://youtube.com/watch?v=TEST"}]
        worker = PlaylistFormatsWorker(entries)

        rows = []
        worker.row_ready.connect(lambda r, t, d, o: rows.append((r, t, d, o)))
        worker.run()

        assert len(rows) == 1
        row_idx, thumb_url, duration, options = rows[0]

        assert row_idx == 0
        assert "example.com/thumb.jpg" in thumb_url
        assert duration == 120
        assert len(options) > 0


# test wybierania najlepszej miniaturki
def test_playlist_formats_worker_best_thumbnail():
    from app.workers.playlist_formats_worker import PlaylistFormatsWorker

    mock_ydl = MagicMock()
    mock_info = {
        "duration": 100,
        "thumbnails": [
            {"url": "http://small.jpg", "width": 320, "height": 180},
            {"url": "http://large.jpg", "width": 1920, "height": 1080},
            {"url": "http://medium.jpg", "width": 640, "height": 360},
        ],
        "formats": [
            {
                "format_id": "best",
                "ext": "mp4",
                "vcodec": "avc1",
                "acodec": "mp4a",
                "height": 720,
            }
        ],
    }
    mock_ydl.extract_info.return_value = mock_info

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        entries = [{"url": "https://youtube.com/watch?v=TEST"}]
        worker = PlaylistFormatsWorker(entries)

        rows = []
        worker.row_ready.connect(lambda r, t, d, o: rows.append((r, t, d, o)))
        worker.run()

        _, thumb_url, _, _ = rows[0]
        assert "large.jpg" in thumb_url


# test budowania listy formatow - muxed
def test_playlist_formats_worker_formats_muxed():
    from app.workers.playlist_formats_worker import PlaylistFormatsWorker

    mock_ydl = MagicMock()
    mock_info = {
        "duration": 100,
        "thumbnails": [],
        "formats": [
            {
                "format_id": "18",
                "ext": "mp4",
                "vcodec": "avc1",
                "acodec": "mp4a",
                "height": 360,
                "fps": 30,
            },
            {
                "format_id": "22",
                "ext": "mp4",
                "vcodec": "avc1",
                "acodec": "mp4a",
                "height": 720,
                "fps": 30,
            },
        ],
    }
    mock_ydl.extract_info.return_value = mock_info

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        entries = [{"url": "https://youtube.com/watch?v=TEST"}]
        worker = PlaylistFormatsWorker(entries)

        rows = []
        worker.row_ready.connect(lambda r, t, d, o: rows.append((r, t, d, o)))
        worker.run()

        _, _, _, options = rows[0]
        format_ids = [opt[0] for opt in options]
        assert "22" in format_ids
        assert "18" in format_ids
        assert "bestaudio" in format_ids


# test budowania listy formatow - video-only + audio
def test_playlist_formats_worker_formats_video_only():
    from app.workers.playlist_formats_worker import PlaylistFormatsWorker

    mock_ydl = MagicMock()
    mock_info = {
        "duration": 100,
        "thumbnails": [],
        "formats": [
            {
                "format_id": "137",
                "ext": "mp4",
                "vcodec": "avc1",
                "acodec": "none",
                "height": 1080,
                "fps": 30,
            },
            {
                "format_id": "136",
                "ext": "mp4",
                "vcodec": "avc1",
                "acodec": "none",
                "height": 720,
                "fps": 60,
            },
            {"format_id": "140", "ext": "m4a", "vcodec": "none", "acodec": "mp4a"},
        ],
    }
    mock_ydl.extract_info.return_value = mock_info

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        entries = [{"url": "https://youtube.com/watch?v=TEST"}]
        worker = PlaylistFormatsWorker(entries)

        rows = []
        worker.row_ready.connect(lambda r, t, d, o: rows.append((r, t, d, o)))
        worker.run()

        _, _, _, options = rows[0]
        format_ids = [opt[0] for opt in options]
        assert "137+bestaudio" in format_ids or any("+" in fid for fid in format_ids)


# test fallback na "Auto" gdy brak formatow
def test_playlist_formats_worker_fallback_auto():
    from app.workers.playlist_formats_worker import PlaylistFormatsWorker

    mock_ydl = MagicMock()
    mock_info = {
        "duration": 100,
        "thumbnails": [],
        "formats": [],
    }
    mock_ydl.extract_info.return_value = mock_info

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        entries = [{"url": "https://youtube.com/watch?v=TEST"}]
        worker = PlaylistFormatsWorker(entries)

        rows = []
        worker.row_ready.connect(lambda r, t, d, o: rows.append((r, t, d, o)))
        worker.run()

        _, _, _, options = rows[0]
        format_ids = [opt[0] for opt in options]
        assert "best" in format_ids
        assert "bestaudio" in format_ids


# test obslugi bledu
def test_playlist_formats_worker_emits_error():
    from app.workers.playlist_formats_worker import PlaylistFormatsWorker

    mock_ydl = MagicMock()
    mock_ydl.extract_info.side_effect = Exception("Network error")

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        entries = [{"url": "https://youtube.com/watch?v=TEST"}]
        worker = PlaylistFormatsWorker(entries)

        errors = []
        worker.error.connect(lambda e: errors.append(e))
        worker.run()

        assert len(errors) == 1
        assert "Network error" in errors[0]


# test przetwarzania wielu elementow
def test_playlist_formats_worker_multiple_entries():
    from app.workers.playlist_formats_worker import PlaylistFormatsWorker

    mock_ydl = MagicMock()
    mock_info = {
        "duration": 100,
        "thumbnails": [],
        "formats": [
            {
                "format_id": "18",
                "ext": "mp4",
                "vcodec": "avc1",
                "acodec": "mp4a",
                "height": 360,
            }
        ],
    }
    mock_ydl.extract_info.return_value = mock_info

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        entries = [
            {"url": "https://youtube.com/watch?v=1"},
            {"url": "https://youtube.com/watch?v=2"},
            {"url": "https://youtube.com/watch?v=3"},
        ]
        worker = PlaylistFormatsWorker(entries)

        rows = []
        worker.row_ready.connect(lambda r, t, d, o: rows.append((r, t, d, o)))
        worker.run()

        assert len(rows) == 3
        assert rows[0][0] == 0
        assert rows[1][0] == 1
        assert rows[2][0] == 2


# test obslugi braku miniaturek
def test_playlist_formats_worker_no_thumbnails():
    from app.workers.playlist_formats_worker import PlaylistFormatsWorker

    mock_ydl = MagicMock()
    mock_info = {
        "duration": 100,
        "thumbnails": None,
        "formats": [
            {
                "format_id": "18",
                "ext": "mp4",
                "vcodec": "avc1",
                "acodec": "mp4a",
                "height": 360,
            }
        ],
    }
    mock_ydl.extract_info.return_value = mock_info

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        entries = [{"url": "https://youtube.com/watch?v=TEST"}]
        worker = PlaylistFormatsWorker(entries)

        rows = []
        worker.row_ready.connect(lambda r, t, d, o: rows.append((r, t, d, o)))
        worker.run()

        _, thumb_url, _, _ = rows[0]
        assert thumb_url == ""


# test obslugi duration = None
def test_playlist_formats_worker_no_duration():
    from app.workers.playlist_formats_worker import PlaylistFormatsWorker

    mock_ydl = MagicMock()
    mock_info = {
        "duration": None,
        "thumbnails": [],
        "formats": [
            {
                "format_id": "18",
                "ext": "mp4",
                "vcodec": "avc1",
                "acodec": "mp4a",
                "height": 360,
            }
        ],
    }
    mock_ydl.extract_info.return_value = mock_info

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        entries = [{"url": "https://youtube.com/watch?v=TEST"}]
        worker = PlaylistFormatsWorker(entries)

        rows = []
        worker.row_ready.connect(lambda r, t, d, o: rows.append((r, t, d, o)))
        worker.run()

        _, _, duration, _ = rows[0]
        assert duration == 0
