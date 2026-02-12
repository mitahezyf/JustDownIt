from unittest.mock import MagicMock, patch


# test inicjalizacji playlist fetch worker
def test_playlist_fetch_worker_init():
    from app.workers.playlist_fetch_worker import PlaylistFetchWorker

    url = "https://www.youtube.com/playlist?list=TEST"
    worker = PlaylistFetchWorker(url)

    assert worker.url == url


# test emitowania sygnalu result z lista wideo
def test_playlist_fetch_worker_emits_result():
    from app.workers.playlist_fetch_worker import PlaylistFetchWorker

    mock_ydl = MagicMock()
    mock_info = {
        "entries": [
            {"id": "video1", "title": "Test Video 1"},
            {"id": "video2", "title": "Test Video 2"},
        ]
    }
    mock_ydl.extract_info.return_value = mock_info

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        worker = PlaylistFetchWorker("https://youtube.com/playlist?list=TEST")
        results = []
        worker.result.connect(lambda r: results.append(r))
        worker.run()

        assert len(results) == 1
        playlist = results[0]
        assert len(playlist) == 2
        assert playlist[0]["id"] == "video1"
        assert playlist[0]["url"] == "https://www.youtube.com/watch?v=video1"
        assert playlist[0]["title"] == "Test Video 1"


# test pomijania elementow bez id
def test_playlist_fetch_worker_skips_no_id():
    from app.workers.playlist_fetch_worker import PlaylistFetchWorker

    mock_ydl = MagicMock()
    mock_info = {
        "entries": [
            {"id": "video1", "title": "Valid"},
            {"title": "No ID"},
            {"id": "video2", "title": "Valid 2"},
        ]
    }
    mock_ydl.extract_info.return_value = mock_info

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        worker = PlaylistFetchWorker("https://youtube.com/playlist?list=TEST")
        results = []
        worker.result.connect(lambda r: results.append(r))
        worker.run()

        playlist = results[0]
        assert len(playlist) == 2
        assert playlist[0]["id"] == "video1"
        assert playlist[1]["id"] == "video2"


# test obslugi pustej playlisty
def test_playlist_fetch_worker_empty_playlist():
    from app.workers.playlist_fetch_worker import PlaylistFetchWorker

    mock_ydl = MagicMock()
    mock_info = {"entries": []}
    mock_ydl.extract_info.return_value = mock_info

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        worker = PlaylistFetchWorker("https://youtube.com/playlist?list=TEST")
        results = []
        worker.result.connect(lambda r: results.append(r))
        worker.run()

        assert len(results) == 1
        assert results[0] == []


# test obslugi entries = None
def test_playlist_fetch_worker_none_entries():
    from app.workers.playlist_fetch_worker import PlaylistFetchWorker

    mock_ydl = MagicMock()
    mock_info = {"entries": None}
    mock_ydl.extract_info.return_value = mock_info

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        worker = PlaylistFetchWorker("https://youtube.com/playlist?list=TEST")
        results = []
        worker.result.connect(lambda r: results.append(r))
        worker.run()

        assert len(results) == 1
        assert results[0] == []


# test emitowania sygnalu error przy wyjatku
def test_playlist_fetch_worker_emits_error():
    from app.workers.playlist_fetch_worker import PlaylistFetchWorker

    mock_ydl = MagicMock()
    mock_ydl.extract_info.side_effect = Exception("Network error")

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        worker = PlaylistFetchWorker("https://youtube.com/playlist?list=TEST")
        errors = []
        worker.error.connect(lambda e: errors.append(e))
        worker.run()

        assert len(errors) == 1
        assert "Network error" in errors[0]


# test domyslnego tytulu gdy brak title
def test_playlist_fetch_worker_missing_title():
    from app.workers.playlist_fetch_worker import PlaylistFetchWorker

    mock_ydl = MagicMock()
    mock_info = {
        "entries": [
            {"id": "video1"},
        ]
    }
    mock_ydl.extract_info.return_value = mock_info

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        worker = PlaylistFetchWorker("https://youtube.com/playlist?list=TEST")
        results = []
        worker.result.connect(lambda r: results.append(r))
        worker.run()

        playlist = results[0]
        assert playlist[0]["title"] == ""


# test opcji przekazanych do yt-dlp
def test_playlist_fetch_worker_ytdlp_options():
    from app.workers.playlist_fetch_worker import PlaylistFetchWorker

    mock_ydl = MagicMock()
    mock_ydl.extract_info.return_value = {"entries": []}

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl

        worker = PlaylistFetchWorker("https://youtube.com/playlist?list=TEST")
        worker.run()

        # sprawdz ze YoutubeDL zostal wywolany z poprawnymi opcjami
        call_args = mock_ytdlp.call_args[0][0]
        assert call_args["quiet"] is True
        assert call_args["skip_download"] is True
        assert call_args["extract_flat"] is True
