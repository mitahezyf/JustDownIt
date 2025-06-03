#!/usr/bin/env python
# -*- coding: utf-8 -*-

r"""
YouTube Downloader v7.9 – wybór folderu docelowego poprzez okno dialogowe

Pozwala użytkownikowi wybrać folder, do którego będą pobierane pliki.
Używa yt-dlp, imageio-ffmpeg oraz tkinter (do otwarcia standardowego okna wyboru katalogu).
"""

import os
import sys
import subprocess
import time
import tkinter as tk
from tkinter import filedialog

# -------------------------------------------------
# 1) Funkcja instalująca brakujące pakiety
# -------------------------------------------------
def instaluj_biblioteki():
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        print("Instalowanie yt-dlp...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])

    try:
        import imageio_ffmpeg  # noqa: F401
    except ImportError:
        print("Instalowanie imageio-ffmpeg...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "imageio-ffmpeg"])

    # Po instalacji – import globalny
    global yt_dlp, imageio_ffmpeg
    import yt_dlp
    import imageio_ffmpeg

# -------------------------------------------------
# 2) Pobranie ścieżki do ffmpeg (imageio-ffmpeg)
# -------------------------------------------------
def pobierz_sciezke_ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

# -------------------------------------------------
# 3) Funkcja do wyboru folderu docelowego
# -------------------------------------------------
def wybierz_folder_domyslny():
    """
    Otwiera okno dialogowe umożliwiające wybranie folderu.
    Jeśli użytkownik nic nie wybierze, zwraca None.
    """
    root = tk.Tk()
    root.withdraw()  # ukryj główne okno
    # pusty parametr initialdir wystarczy, bo użytkownik może od razu wybrać
    folder = filedialog.askdirectory(title="Wybierz folder do pobierania")
    root.destroy()
    if folder == "":
        return None
    return folder

# -------------------------------------------------
# 4) Pobranie wideo MP4 i ustawienie timestampu
# -------------------------------------------------
def pobierz_wideo_mp4(url, ffmpeg_exe, folder_docelowy):
    dokladna_sciezka = os.path.join(folder_docelowy, "%(title)s.%(ext)s")

    print(f"\n[*] Wybrany katalog docelowy: {folder_docelowy}")
    print(f"[*] outtmpl (dokładna ścieżka): {dokladna_sciezka}")
    print(f"[*] ffmpeg_location: {ffmpeg_exe}")

    def progress_hook(d):
        if d.get("status") == "finished":
            filepath = d["filename"]
            now = time.time()
            try:
                os.utime(filepath, (now, now))
                print(f"\nPlik wideo zapisano jako:\n   {filepath}")
                print(f"   → zaktualizowano mtime na aktualny czas\n")
            except Exception as e:
                print(f"(!) Nie udało się zaktualizować mtime: {e}")
                print(f"   → Plik wideo: {filepath}\n")

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
        "recode_video": "mp4",
        "merge_output_format": "mp4",
        "outtmpl": dokladna_sciezka,
        "ffmpeg_location": ffmpeg_exe,
        "no-mtime": True,
        "progress_hooks": [progress_hook],
        "quiet": False,
        "no_warnings": True,
    }

    print(f"\nRozpoczynam pobieranie wideo (MP4) → {url}\n")
    import yt_dlp
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        print(f"Błąd podczas pobierania wideo: {e}")

# -------------------------------------------------
# 5) Pobranie audio MP3 i ustawienie timestampu
# -------------------------------------------------
def pobierz_audio_mp3(url, ffmpeg_exe, folder_docelowy):
    dokladna_sciezka = os.path.join(folder_docelowy, "%(title)s.%(ext)s")

    print(f"\n[*] Wybrany katalog docelowy: {folder_docelowy}")
    print(f"[*] outtmpl (dokładna ścieżka): {dokladna_sciezka}")
    print(f"[*] ffmpeg_location: {ffmpeg_exe}")

    def progress_hook(d):
        if d.get("status") == "finished":
            filepath = d["filename"]
            now = time.time()
            try:
                os.utime(filepath, (now, now))
                print(f"\nPlik audio zapisano jako:\n   {filepath}")
                print(f"   → zaktualizowano mtime na aktualny czas\n")
            except Exception as e:
                print(f"(!) Nie udało się zaktualizować mtime: {e}")
                print(f"   → Plik audio: {filepath}\n")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": dokladna_sciezka,
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
        "quiet": False,
        "no_warnings": True,
    }

    print(f"\nRozpoczynam pobieranie audio (MP3) → {url}\n")
    import yt_dlp
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        print(f"Błąd podczas pobierania audio: {e}")

# -------------------------------------------------
# 6) Główna pętla programu
# -------------------------------------------------
def main():
    # 6.1) Zapytaj użytkownika o folder docelowy
    print("Otwieram okno wyboru folderu...")
    folder_docelowy = wybierz_folder_domyslny()
    if not folder_docelowy:
        print("Nie wybrano folderu. Kończę działanie.")
        sys.exit(0)

    # 6.2) Upewnij się, że folder istnieje (ishandle by utworzyć, jeśli trzeba)
    try:
        os.makedirs(folder_docelowy, exist_ok=True)
    except Exception as e:
        print(f"Nie udało się utworzyć folderu {folder_docelowy}: {e}")
        sys.exit(1)

    # 6.3) Instalacja bibliotek
    instaluj_biblioteki()

    # 6.4) Ścieżka do ffmpeg.exe
    ffmpeg_exe = pobierz_sciezke_ffmpeg()
    print(f"[*] ffmpeg.exe znaleziono w: {ffmpeg_exe}")

    # 6.5) Menu wyboru formatu
    print("\n" + "=" * 60)
    print("      YouTube Downloader v7.9 (Wybór folderu/MP4/MP3)")
    print("      1) Pobierz wideo (MP4)")
    print("      2) Pobierz samo audio (MP3)")
    print("      (aby wyjść, wpisz 'exit')")
    print("=" * 60)

    while True:
        print("\nWybierz opcję (1 lub 2) lub wpisz 'exit': ", end="")
        wybor = input().strip().lower()
        if wybor == "exit":
            break
        if wybor not in ("1", "2"):
            print("Nieprawidłowa opcja. Wpisz 1, 2 lub 'exit'.")
            continue

        print("\nPodaj pełny URL filmu (lub wpisz 'exit'): ", end="")
        url = input().strip()
        if url.lower() == "exit":
            break
        if not url.startswith("http"):
            print("Nieprawidłowy URL. Spróbuj ponownie.")
            continue

        if wybor == "1":
            pobierz_wideo_mp4(url, ffmpeg_exe, folder_docelowy)
        else:
            pobierz_audio_mp3(url, ffmpeg_exe, folder_docelowy)

    print("\nZakończono działanie programu. Miłego korzystania!")

if __name__ == "__main__":
    main()
