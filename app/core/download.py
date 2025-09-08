from __future__ import annotations

from typing import Callable, Optional

from app.core.paths import outtmpl_for
from app.core.ytclient import YTClient
from app.utils.errors import CancelledError

# definicja typow dla callbackow
# progressCb przyjmuje procent postepu, liczbe pobranych bajtow i calkowita liczbe bajtow
# CancelCb to funkcja ktora zwraca bool czy anulowac pobieranie
ProgressCb = Callable[[float, int, int], None]  # percent, downloaded, total
CancelCb = Callable[[], bool]


# funkcja pomocnicza tworzaca hook do sledzenia postepu i obslugi anulowania
def _hook(progress_cb: Optional[ProgressCb], cancel_cb: Optional[CancelCb]):
    def progress_hook(d: dict):
        # jesli callback anulowania zwroci True to przerwij pobieranie
        if cancel_cb and cancel_cb():
            raise CancelledError("Pobieranie anulowane przez użytkownika.")
        # sprawdz status przekazany przez yt-dlp
        if d.get("status") == "downloading":
            downloaded = int(d.get("downloaded_bytes") or 0)
            total = int(d.get("total_bytes") or d.get("total_bytes_estimate") or 0)
            pct = (downloaded / total * 100.0) if total else 0.0
            # jesli podano callback postepu to wywolaj go
            if progress_cb:
                progress_cb(pct, downloaded, total)

    return progress_hook


# funkcja do pobierania wideo w formacie mp4
def download_video_mp4(
    yt: YTClient,
    url: str,
    output_dir: str,
    format_id: Optional[str] = None,
    progress_cb: Optional[ProgressCb] = None,
    cancel_cb: Optional[CancelCb] = None,
):
    # jesli nie podano formatu to uzyj najlepszego video mp4 z audio
    fmt = format_id or "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
    opts = {
        "format": fmt,
        "recode_video": "mp4",  # wymus konwersje do mp4
        "merge_output_format": "mp4",  # format wynikowy mp4
        "outtmpl": outtmpl_for(output_dir),  # sciezka do pliku wynikowego
        "progress_hooks": [_hook(progress_cb, cancel_cb)],
        "restrictfilenames": True,  # bezpieczne nazwy plikow
    }
    yt.download(url, opts)


# funkcja do pobierania audio w formacie mp3
def download_audio_mp3(
    yt: YTClient,
    url: str,
    output_dir: str,
    progress_cb: Optional[ProgressCb] = None,
    cancel_cb: Optional[CancelCb] = None,
):
    opts = {
        "format": "bestaudio/best",  # wybierz najlepsze audio
        "outtmpl": outtmpl_for(output_dir),
        "keepvideo": False,  # nie zachowuj oryginalnego video
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",  # uzyj ffmpeg do wyciagniecia audio
                "preferredcodec": "mp3",  # konwertuj do mp3
                "preferredquality": "320",  # jakosc 320 kbps
            }
        ],
        "progress_hooks": [_hook(progress_cb, cancel_cb)],
        "restrictfilenames": True,
    }
    yt.download(url, opts)
