from __future__ import annotations

from typing import Any, Dict, Optional


# klient do obslugi yt-dlp
class YTClient:

    # inicjalizacja klienta z podana sciezka do ffmpeg i opcjonalnym proxy
    def __init__(self, ffmpeg_path: str, proxy: Optional[str] = None):
        try:
            import yt_dlp  # type: ignore
        except ImportError as e:
            from app.utils.errors import DependencyMissingError

            # jesli nie ma yt-dlp to rzuca blad zaleznosci
            raise DependencyMissingError("Brak yt-dlp w środowisku.") from e
        self._yt_dlp = yt_dlp
        self.ffmpeg_path = ffmpeg_path
        self.proxy = proxy

    # buduje podstawowe opcje dla yt-dlp, mozna rozszerzyc o dodatkowe
    def _base_opts(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        opts: Dict[str, Any] = {
            "ffmpeg_location": self.ffmpeg_path,  # sciezka do ffmpeg
            "no-mtime": True,  # nie nadpisuje czasu modyfikacji pliku
            "quiet": True,  # tryb cichy
            "no_warnings": True,  # brak ostrzezen
            "ratelimit": 25_000_000,  # limit predkosci pobierania
            "retries": 3,  # liczba ponownych prob
            "no_check_certificate": True,  # ignoruj certyfikaty ssl
        }
        if self.proxy:
            opts["proxy"] = self.proxy
        if extra:
            opts.update(extra)
        return opts

    # pobiera plik z podanego url z uzyciem opcji
    def download(self, url: str, options: Dict[str, Any]) -> None:
        with self._yt_dlp.YoutubeDL(self._base_opts(options)) as ydl:
            ydl.download([url])

    # wyciaga informacje o materiale bez pobierania (chyba ze opcje inaczej ustawia)
    def extract(self, url: str, options: Optional[Dict[str, Any]] = None) -> dict:
        with self._yt_dlp.YoutubeDL(
            self._base_opts(options or {"skip_download": True})
        ) as ydl:
            return ydl.extract_info(url, download=False)

    # zwraca modul utils z yt-dlp do obslugi bledow i innych narzedzi
    @property
    def errors(self):
        return self._yt_dlp.utils
