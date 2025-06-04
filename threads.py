# threads.py
from PyQt6.QtCore import QThread, pyqtSignal
from ytdown_core import pobierz_wideo_mp4, pobierz_audio_mp3, instaluj_biblioteki

class InstallThread(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, log_func):
        super().__init__()
        self.log_func = log_func

    def run(self):
        def _log(msg):
            self.log_signal.emit(msg)
        instaluj_biblioteki(_log)
        self.finished_signal.emit()


class DownloadThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(float)
    finished_signal = pyqtSignal(bool, str)
    cancel_requested = pyqtSignal()

    def __init__(self, url, ffmpeg_path, folder, download_type, log_func):
        super().__init__()
        self.url = url
        self.ffmpeg_path = ffmpeg_path
        self.folder = folder
        self.download_type = download_type
        self.log_func = log_func
        self.cancelled = False

    def cancel(self):
        self.cancelled = True
        self.cancel_requested.emit()
        self.log_signal.emit("Anulowanie pobierania...")

    def run(self):
        success = False
        error_msg = ""

        def _log(msg):
            self.log_signal.emit(msg)

        def _progress(percent):
            if not self.cancelled:
                self.progress_signal.emit(percent)

        try:
            if self.download_type == "mp4":
                pobierz_wideo_mp4(
                    self.url,
                    self.ffmpeg_path,
                    self.folder,
                    _log,
                    progress_func=_progress,
                    cancel_flag=lambda: self.cancelled
                )
                success = True
            else:  # "mp3"
                pobierz_audio_mp3(
                    self.url,
                    self.ffmpeg_path,
                    self.folder,
                    _log,
                    progress_func=_progress,
                    cancel_flag=lambda: self.cancelled
                )
                success = True
        except Exception as e:
            error_msg = str(e)
            _log(f"Błąd: {error_msg}")

        if self.cancelled:
            error_msg = "Pobieranie anulowane przez użytkownika"
            _log(error_msg)
            success = False

        self.finished_signal.emit(success, error_msg)
