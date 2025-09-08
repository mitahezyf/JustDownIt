from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from app.core.download import download_audio_mp3, download_video_mp4
from app.core.paths import get_ffmpeg_path
from app.core.ytclient import YTClient
from app.utils.errors import CancelledError


# worker w osobnym watku do pobierania plikow
class DownloadWorker(QThread):
    # sygnaly przekazywane do interfejsu
    log_signal = pyqtSignal(str)  # komunikaty tekstowe
    progress_signal = pyqtSignal(float)  # postep w procentach 0..100
    finished_signal = pyqtSignal(bool, str)  # czy sukces i ewentualny blad
    cancel_requested = pyqtSignal()

    def __init__(
        self, url: str, folder: str, download_type: str, format_id: str | None
    ):
        """
        :param url: YouTube URL
        :param folder: katalog docelowy
        :param download_type: "mp4" lub "mp3"
        :param format_id: np. "137+bestaudio" / "22" (dla mp3 -> None)
        """
        super().__init__()
        self.url = url
        self.folder = folder
        self.download_type = download_type
        self.format_id = format_id
        self._cancelled = False

        # inicjalizacja yt-dlp przez klienta, worker nie musi znac szczegolow
        ffmpeg = get_ffmpeg_path()
        self._yt = YTClient(ffmpeg_path=ffmpeg, proxy=None)

    # api anulowania
    def cancel(self):
        self._cancelled = True
        self.cancel_requested.emit()
        self.log_signal.emit("Anulowanie pobierania...")

    # callback postepu pobierania
    def _on_progress(self, pct: float, downloaded: int, total: int):

        self.progress_signal.emit(pct)
        if total:
            self.log_signal.emit(
                f"Postęp: {pct:.1f}% ({downloaded/1_000_000:.1f}/{total/1_000_000:.1f} MB)"
            )
        else:
            self.log_signal.emit(f"Postęp: {pct:.1f}%")

    # callback sprawdzajacy czy uzytkownik anulowal
    def _is_cancelled(self) -> bool:
        return self._cancelled

    # glowna metoda uruchamiana w watku
    def run(self):
        try:
            if self.download_type == "mp3":
                self.log_signal.emit(f"Start audio → {self.url}")
                download_audio_mp3(
                    yt=self._yt,
                    url=self.url,
                    output_dir=self.folder,
                    progress_cb=self._on_progress,
                    cancel_cb=self._is_cancelled,
                )
            else:
                self.log_signal.emit(f"Start wideo (fmt={self.format_id}) → {self.url}")
                download_video_mp4(
                    yt=self._yt,
                    url=self.url,
                    output_dir=self.folder,
                    format_id=self.format_id,
                    progress_cb=self._on_progress,
                    cancel_cb=self._is_cancelled,
                )
            self.finished_signal.emit(True, "")
        except CancelledError:
            # anulowanie nie jest traktowane jako krytyczny blad
            self.finished_signal.emit(False, "Pobieranie anulowane")
        except Exception as e:
            # realny blad – przekazujemy tresc do ui lub logow
            self.finished_signal.emit(False, str(e))
