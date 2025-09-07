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
import re
import subprocess
import sys

import requests

# Początkowo ustawiamy je na None, a potem – po instalacji – nadpisujemy
yt_dlp = None
imageio_ffmpeg = None


# ========== 1 Instalacja brakujących bibliotek==========
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

    # 1a Sprawdź / zainstaluj yt-dlp
    try:
        import yt_dlp  # noqa: F401

        _log("Pakiet yt-dlp jest zainstalowany.")
    except ImportError:
        _log("Instalowanie yt-dlp...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
        _log("yt-dlp zainstalowany pomyślnie.")

    # 1b Sprawdź / zainstaluj imageio-ffmpeg
    try:
        import imageio_ffmpeg  # noqa: F401

        _log("Pakiet imageio-ffmpeg jest zainstalowany.")
    except ImportError:
        _log("Instalowanie imageio-ffmpeg...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "imageio-ffmpeg"]
        )
        _log("imageio-ffmpeg zainstalowany pomyślnie.")

    # 1c Sprawdź / zainstaluj requests
    try:
        import requests  # noqa: F401

        _log("Pakiet requests jest zainstalowany.")
    except ImportError:
        _log("Instalowanie requests...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        _log("requests zainstalowany pomyślnie.")

    # 1d Po instalacji – importujemy globalnie
    global yt_dlp, imageio_ffmpeg
    try:
        import yt_dlp as _yt

        yt_dlp = _yt
    except ImportError:
        _log("Uwaga: Nie udało się zaimportować yt_dlp pomimo instalacji!")

    try:
        import imageio_ffmpeg as _ff

        imageio_ffmpeg = _ff
    except ImportError:
        _log("Uwaga: Nie udało się zaimportować imageio_ffmpeg pomimo instalacji!")

    _log("Instalacja i import pakietów zakończona.")


# ========== 2 Pobranie ścieżki do binarki FFmpeg ==========
def pobierz_sciezke_ffmpeg():
    """
    Korzysta z imageio_ffmpeg.get_ffmpeg_exe(), aby zwrócić ścieżkę do pliku ffmpeg.exe.
    """
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise RuntimeError("Moduł imageio_ffmpeg nie jest zainstalowany.")


# ========== 3 Pobieranie wideo (MP4) z ustawieniem mtime ==========
def pobierz_wideo_mp4(
    url: str,
    ffmpeg_exe: str,
    folder_docelowy: str,
    log_func=None,
    proxy=None,
    progress_func=None,
    cancel_flag=None,
):
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
    - cancel_flag: funkcja sprawdzająca czy anulowano (zwraca True jeśli anulowano)
    """

    def _log(msg):
        if log_func:
            log_func(msg)
        else:
            print(msg)

    global yt_dlp
    if yt_dlp is None:
        raise RuntimeError(
            "Moduł yt_dlp nie jest zaimportowany. Upewnij się, że instaluj_biblioteki() został wywołany."
        )

    dokladna_sciezka = os.path.join(folder_docelowy, "%(title)s.%(ext)s")
    _log(f" → outtmpl: {dokladna_sciezka}")
    _log(f" → ffmpeg_location: {ffmpeg_exe}")

    def progress_hook(d):
        # Czy anulowano pobieranie
        if cancel_flag and cancel_flag():
            raise Exception("Pobieranie anulowane przez użytkownika")

        if d.get("status") == "downloading":
            percent_str = d.get("_percent_str", "0%")
            try:
                percent_float = float(percent_str.strip().replace("%", ""))
            except (ValueError, AttributeError):
                percent_float = 0.0

            if progress_func:
                progress_func(percent_float)

            if log_func:
                _log(f"Postęp: {percent_str} | Szybkość: {d.get('_speed_str', 'N/A')}")

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
        "ratelimit": 25_000_000,  # limit 25 MB/s
        "retries": 3,
        "no_check_certificate": True,
        "proxy": proxy if proxy else None,
    }

    _log(f"Rozpoczynam pobieranie wideo → {url}")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        _log(f"Błąd pobierania wideo: {e}")
    except Exception as e:
        # Jeśli wyjątek nie był spowodowany anulowaniem
        if "anulowane" not in str(e).lower():
            _log(f"Nieoczekiwany błąd: {e}")


# ========== 4 Pobieranie audio (MP3) z ustawieniem mtime ==========
def pobierz_audio_mp3(
    url: str,
    ffmpeg_exe: str,
    folder_docelowy: str,
    log_func=None,
    proxy=None,
    progress_func=None,
    cancel_flag=None,
):
    """
    Pobiera najlepszy strumień audio i konwertuje do MP3 (320 kbps).
    - Po zakończeniu konwersji ręcznie ustawia timestamp (mtime i atime) na aktualny.
    - Usuwa oryginalny plik (np. .webm), zostaje tylko .mp3.

    Parametry:
    - url: pełny link do filmu
    - ffmpeg_exe: pełna ścieżka do ffmpeg.exe
    - folder_docelowy: absolutna ścieżka do folderu, gdzie zapiszemy finalne .mp3
    - log_func: opcjonalna funkcja logująca (np. przekazywana z GUI)
    - cancel_flag: funkcja sprawdzająca czy anulowano (zwraca True jeśli anulowano)
    """

    def _log(msg):
        if log_func:
            log_func(msg)
        else:
            print(msg)

    # Sprawdź, czy yt_dlp jest zaimportowane
    global yt_dlp
    if yt_dlp is None:
        raise RuntimeError(
            "Moduł yt_dlp nie jest zaimportowany. Upewnij się, że instaluj_biblioteki() został wywołany."
        )

    dokladna_sciezka = os.path.join(folder_docelowy, "%(title)s.%(ext)s")
    _log(f" → outtmpl: {dokladna_sciezka}")
    _log(f" → ffmpeg_location: {ffmpeg_exe}")

    def progress_hook(d):
        # Czy anulowano pobieranie
        if cancel_flag and cancel_flag():
            raise Exception("Pobieranie anulowane przez użytkownika")

        if d.get("status") == "downloading":
            percent_str = d.get("_percent_str", "0%")
            try:
                percent_float = float(percent_str.strip().replace("%", ""))
            except (ValueError, AttributeError):
                percent_float = 0.0

            if progress_func:
                progress_func(percent_float)

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
        "proxy": proxy if proxy else None,
    }

    _log(f"Rozpoczynam pobieranie audio → {url}")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        _log(f"Błąd pobierania audio: {e}")
    except Exception as e:
        if "anulowane" not in str(e).lower():
            _log(f"Nieoczekiwany błąd: {e}")


# ========== 5 Pobieranie URL miniatury ==========
def pobierz_miniaturke(url: str, log_func=None):
    """
    Pobiera URL miniaturki (maxresdefault lub hqdefault).
    Zwraca string z linkiem lub None, jeśli się nie uda.
    """
    try:
        video_id = extract_video_id(url)
        if video_id:
            thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"

            # Czy maxresdefault istnieje
            try:
                response = requests.head(thumbnail_url, timeout=3)
                if response.status_code == 200:
                    return thumbnail_url
            except requests.exceptions.RequestException:
                pass

            # Fallback na hqdefault
            return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    except Exception as e:
        if log_func:
            log_func(f"Błąd pobierania miniatury: {e}")
    return None


def extract_video_id(url: str):
    """
    Wyodrębnianie ID filmu z różnych formatów URL YouTube.
    Zwraca ID lub None, jeśli nie pasuje żaden wzorzec.
    """
    patterns = [
        r"youtube\.com/watch\?v=([^&]+)",
        r"youtu\.be/([^?]+)",
        r"youtube\.com/embed/([^/]+)",
        r"youtube\.com/v/([^?]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None
