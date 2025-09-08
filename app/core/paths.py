from __future__ import annotations

import os
from pathlib import Path


# zwraca sciezke do programu ffmpeg
def get_ffmpeg_path() -> str:

    # sprawdza zmienna srodowiskowa FFMPEG_PATH i czy plik istnieje
    env = os.getenv("FFMPEG_PATH")
    if env and Path(env).exists():
        return env
    try:
        import imageio_ffmpeg  # biblioteka dostarczajaca ffmpeg
    except ImportError as e:
        from app.utils.errors import DependencyMissingError

        # jesli nie ma biblioteki to rzuca blad informujacy o braku zaleznosci
        raise DependencyMissingError() from e
    # jesli import sie udal to zwraca sciezke do ffmpeg od imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


# upewnia sie ze katalog wyjsciowy istnieje, w razie potrzeby go tworzy
def ensure_output_dir(path: str | Path) -> Path:
    p = Path(path).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


# tworzy wzor nazwy pliku dla yt-dlp w podanym katalogu
# %(title)s i %(ext)s beda podstawiane przez yt-dlp
def outtmpl_for(dirpath: str | Path) -> str:
    return str(ensure_output_dir(dirpath) / "%(title)s.%(ext)s")
