#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ytdown_core.py

Moduł „core” odpowiadający za:
- Instalację brakujących bibliotek (yt-dlp, imageio-ffmpeg)
- Pobranie ścieżki do FFmpeg
- Pobieranie wideo (MP4) i audio (MP3) z ustawianiem timestampu
- Logikę, którą można zaimportować w GUI albo użyć z poziomu konsoli
"""

import os
import subprocess
import sys
import time

# -------------- 1) Instalacja brakujących bibliotek --------------
def instaluj_biblioteki(log_func=None):
    """
    Sprawdza, czy zainstalowane są pakiety `yt-dlp` i `imageio-ffmpeg`.
    Jeśli nie, instaluje je przez pip.
    Przyjmuje opcjonalny log_func, aby kierować komunikaty do GUI.
    """
    def _log(msg):
        if log_func:
            log_func(msg)
        else:
            print(msg)

    try:
        import yt_dlp  # noqa: F401
        _log("Pakiet yt-dlp jest zainstalowany.")
    except ImportError:
        _log("Instalowanie yt-dlp...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])

    try:
        import imageio_ffmpeg  # noqa: F401
        _log("Pakiet imageio-ffmpeg jest zainstalowany.")
    except ImportError:
        _log("Instalowanie imageio-ffmpeg...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "imageio-ffmpeg"])

    # Po instalacji – importujemy globalnie, aby inne funkcje w tym module mogły korzystać
    global yt_dlp, imageio_ffmpeg
    import yt_dlp
    import imageio_ffmpeg
    _log("Instalacja i import pakietów zakończona.")


# -------------- 2) Pobranie ścieżki do binarki FFmpeg --------------
def pobierz_sciezke_ffmpeg():
    """
    Korzysta z imageio_ffmpeg.get_ffmpeg_exe(), aby zwrócić ścieżkę do pliku ffmpeg.exe.
    """
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


# -------------- 3) Pobieranie wideo (MP4) z ustawieniem mtime --------------
def pobierz_wideo_mp4(url: str, ffmpeg_exe: str, folder_docelowy: str, log_func=None):
    """
    Pobiera wideo z YouTube w formacie MP4.
    - Łączy strumienie video+audio (mp4 + m4a) lub przechodzi przez recode, jeśli jedyny dostępny jest WEBM.
    - Po pobraniu ręcznie ustawia timestamp (mtime i atime) na aktualny moment.
    - Efekt: plik .mp4 w `folder_docelowy`.

    Parametry:
    - url: pełny link do filmu
    - ffmpeg_exe: pełna ścieżka do ffmpeg.exe (zwrócona przez pobierz_sciezke_ffmpeg)
    - folder_docelowy: absolutna ścieżka do katalogu, w którym zapiszemy finalne pliki
    - log_func: opcjonalna funkcja logująca (np. przekazywana z GUI)
    """
    def _log(msg):
        if log_func:
            log_func(msg)
        else:
            print(msg)

    dokladna_sciezka = os.path.join(folder_docelowy, "%(title)s.%(ext)s")
    _log(f" → outtmpl: {dokladna_sciezka}")
    _log(f" → ffmpeg_location: {ffmpeg_exe}")

    def progress_hook(d):
        if d.get("status") == "finished":
            filepath = d["filename"]
            now = time.time()
            try:
                os.utime(filepath, (now, now))
                _log(f"Zapisano wideo: {filepath}")
            except Exception as e:
                _log(f"(!) Błąd przy aktualizacji mtime: {e}")

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
        "recode_video": "mp4",
        "merge_output_format": "mp4",
        "outtmpl": dokladna_sciezka,
        "ffmpeg_location": ffmpeg_exe,
        "no-mtime": True,
        "progress_hooks": [progress_hook],
        "quiet": True,
        "no_warnings": True,
    }

    _log(f"Rozpoczynam pobieranie wideo → {url}")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        _log(f"Błąd pobierania wideo: {e}")
    except Exception as e:
        _log(f"Nieoczekiwany błąd: {e}")


# -------------- 4) Pobieranie audio (MP3) z ustawieniem mtime --------------
def pobierz_audio_mp3(url: str, ffmpeg_exe: str, folder_docelowy: str, log_func=None):
    """
    Pobiera najlepszy strumień audio i konwertuje do MP3 (320 kbps).
    - Po zakończeniu konwersji ręcznie ustawia timestamp (mtime i atime) na aktualny.
    - Usuwa oryginalny plik (np. .webm), zostaje tylko .mp3.

    Parametry:
    - url: pełny link do filmu
    - ffmpeg_exe: pełna ścieżka do ffmpeg.exe
    - folder_docelowy: absolutna ścieżka do folderu, gdzie zapiszemy finalne .mp3
    - log_func: opcjonalna funkcja logująca (np. przekazywana z GUI)
    """
    def _log(msg):
        if log_func:
            log_func(msg)
        else:
            print(msg)

    dokladna_sciezka = os.path.join(folder_docelowy, "%(title)s.%(ext)s")
    _log(f" → outtmpl: {dokladna_sciezka}")
    _log(f" → ffmpeg_location: {ffmpeg_exe}")

    def progress_hook(d):
        if d.get("status") == "finished":
            filepath = d["filename"]
            now = time.time()
            try:
                os.utime(filepath, (now, now))
                _log(f"Zapisano audio: {filepath}")
            except Exception as e:
                _log(f"(!) Błąd przy aktualizacji mtime: {e}")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": dokladna_sciezka,
        "keepvideo": False,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }
        ],
        "ffmpeg_location": ffmpeg_exe,
        "no-mtime": True,
        "progress_hooks": [progress_hook],
        "quiet": True,
        "no_warnings": True,
    }

    _log(f"Rozpoczynam pobieranie audio → {url}")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        _log(f"Błąd pobierania audio: {e}")
    except Exception as e:
        _log(f"Nieoczekiwany błąd: {e}")
