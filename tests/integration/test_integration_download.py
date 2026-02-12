import os

import pytest

from app.core.download import download_audio_mp3, download_video_mp4
from app.core.paths import get_ffmpeg_path
from app.core.thumbnails import get_thumbnail_url
from app.core.ytclient import YTClient

# testy integracyjne - oznaczone jako slow i integration
# te testy faktycznie lacza sie z youtube i pobieraja prawdziwe pliki

pytestmark = [pytest.mark.integration, pytest.mark.slow]


# test prawdziwego polaczenia z youtube i pobrania informacji o wideo
def test_integration_extract_video_info(test_video_url):
    ffmpeg = get_ffmpeg_path()
    yt = YTClient(ffmpeg_path=ffmpeg)

    # prawdziwe wywolanie do youtube
    info = yt.extract(test_video_url)

    # sprawdz ze otrzymalismy podstawowe informacje
    assert info is not None
    assert "id" in info
    assert "title" in info
    assert "duration" in info
    assert info["duration"] > 0
    assert "formats" in info
    assert len(info["formats"]) > 0


# test prawdziwego pobrania miniatury
def test_integration_get_thumbnail(test_video_url):
    thumb_url = get_thumbnail_url(test_video_url)

    # sprawdz ze otrzymalismy prawidlowy url
    assert thumb_url is not None
    assert "ytimg.com" in thumb_url
    assert thumb_url.startswith("http")


# test prawdziwego pobrania audio do mp3
def test_integration_download_audio_mp3(test_video_url, setup_integration_env):
    output_dir = setup_integration_env["output_dir"]
    ffmpeg = get_ffmpeg_path()
    yt = YTClient(ffmpeg_path=ffmpeg)

    # zmienne do sledzenia postepu
    progress_calls = []

    def progress_cb(pct, downloaded, total):
        progress_calls.append(pct)

    # prawdziwe pobranie mp3 (krotkie wideo ~10s)
    download_audio_mp3(
        yt=yt,
        url=test_video_url,
        output_dir=str(output_dir),
        progress_cb=progress_cb,
    )

    # sprawdz ze callback postepu byl wywolywany
    assert len(progress_calls) > 0

    # sprawdz ze plik mp3 zostal utworzony
    mp3_files = list(output_dir.glob("*.mp3"))
    assert len(mp3_files) > 0, "Brak pobranych plikow MP3"

    # sprawdz ze plik ma rozsadny rozmiar (wiekszy niz 1KB)
    mp3_file = mp3_files[0]
    assert mp3_file.stat().st_size > 1024


# test prawdziwego pobrania wideo mp4
def test_integration_download_video_mp4(test_video_url, setup_integration_env):
    output_dir = setup_integration_env["output_dir"]
    ffmpeg = get_ffmpeg_path()
    yt = YTClient(ffmpeg_path=ffmpeg)

    progress_calls = []

    def progress_cb(pct, downloaded, total):
        progress_calls.append(pct)

    # prawdziwe pobranie wideo w niskiej rozdzielczosci (szybsze)
    # uzyj formatu 18 = 360p (maly rozmiar)
    download_video_mp4(
        yt=yt,
        url=test_video_url,
        output_dir=str(output_dir),
        format_id="18",  # 360p - szybkie do testow
        progress_cb=progress_cb,
    )

    # sprawdz ze callback byl wywolywany
    assert len(progress_calls) > 0

    # sprawdz ze plik mp4 zostal utworzony
    mp4_files = list(output_dir.glob("*.mp4"))
    assert len(mp4_files) > 0, "Brak pobranych plikow MP4"

    # sprawdz rozmiar pliku
    mp4_file = mp4_files[0]
    assert mp4_file.stat().st_size > 10_000  # powinien byc wiekszy niz 10KB


# test prawdziwego pobrania playlist (tylko ekstraktowanie listy, bez pobierania)
def test_integration_extract_playlist_info(test_playlist_url):
    ffmpeg = get_ffmpeg_path()
    yt = YTClient(ffmpeg_path=ffmpeg)

    # extract_flat=True pobiera tylko liste bez pobierania filmow
    info = yt.extract(test_playlist_url, {"extract_flat": True})

    # sprawdz ze otrzymalismy informacje o playliscie
    assert info is not None
    assert "entries" in info
    entries = info["entries"] or []

    # playlista powinna miec przynajmniej 1 element
    assert len(entries) > 0

    # sprawdz strukture pierwszego elementu
    first = entries[0]
    assert "id" in first or "url" in first


# test anulowania pobierania
def test_integration_download_cancel(test_video_url, setup_integration_env):
    output_dir = setup_integration_env["output_dir"]
    ffmpeg = get_ffmpeg_path()
    yt = YTClient(ffmpeg_path=ffmpeg)

    # flaga do anulowania po pierwszym callbacku
    cancel_after_first = {"called": False, "should_cancel": False}

    def progress_cb(pct, downloaded, total):
        if not cancel_after_first["called"]:
            cancel_after_first["called"] = True
            cancel_after_first["should_cancel"] = True

    def cancel_cb():
        return cancel_after_first["should_cancel"]

    # probuj pobrac i anuluj
    from app.utils.errors import CancelledError

    with pytest.raises(CancelledError):
        download_video_mp4(
            yt=yt,
            url=test_video_url,
            output_dir=str(output_dir),
            format_id="18",
            progress_cb=progress_cb,
            cancel_cb=cancel_cb,
        )

    # sprawdz ze callback byl wywolany (czyli pobieranie sie zaczelo)
    assert cancel_after_first["called"]


# test ze ffmpeg faktycznie istnieje i dziala
def test_integration_ffmpeg_available():
    ffmpeg_path = get_ffmpeg_path()

    assert ffmpeg_path is not None
    assert len(ffmpeg_path) > 0

    # sprawdz ze plik istnieje (jesli to sciezka lokalna)
    if os.path.exists(ffmpeg_path):
        assert os.path.isfile(ffmpeg_path)


# test formatu dla roznych rozdzielczosci
@pytest.mark.parametrize(
    "format_id,desc",
    [
        ("18", "360p"),
        ("best", "auto"),
    ],
)
def test_integration_download_different_formats(
    test_video_url, setup_integration_env, format_id, desc
):
    output_dir = setup_integration_env["output_dir"] / desc
    output_dir.mkdir(exist_ok=True)

    ffmpeg = get_ffmpeg_path()
    yt = YTClient(ffmpeg_path=ffmpeg)

    # pobierz w roznym formacie
    download_video_mp4(
        yt=yt,
        url=test_video_url,
        output_dir=str(output_dir),
        format_id=format_id,
    )

    # sprawdz ze plik zostal pobrany
    mp4_files = list(output_dir.glob("*.mp4"))
    assert len(mp4_files) > 0, f"Brak pliku dla formatu {desc}"
