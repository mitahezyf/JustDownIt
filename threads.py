# threads.py

from PyQt6.QtCore import QThread, pyqtSignal
import yt_dlp
from ytdown_core import instaluj_biblioteki


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

    def __init__(self, url, ffmpeg_path, folder, download_type, format_id, log_func):
        super().__init__()
        self.url = url
        self.ffmpeg_path = ffmpeg_path
        self.folder = folder
        self.download_type = download_type
        self.format_id = format_id
        self.log_func = log_func
        self.cancelled = False

    def cancel(self):
        """Anuluje bieżące pobieranie"""
        self.cancelled = True
        self.cancel_requested.emit()
        self.log_signal.emit("Anulowanie pobierania...")

    def run(self):
        success = False
        error_msg = ""

        def _log(msg):
            self.log_signal.emit(msg)

        def _progress(d):
            if self.cancelled:
                raise Exception("Pobieranie anulowane przez użytkownika")
            if d.get("status") == "downloading":
                percent_str = d.get("_percent_str", "0%")
                try:
                    percent_float = float(percent_str.strip().replace('%', ''))
                except (ValueError, AttributeError):
                    percent_float = 0.0
                self.progress_signal.emit(percent_float)
                _log(f"Postęp: {percent_str} | Szybkość: {d.get('_speed_str', 'N/A')}")

        try:
            if self.download_type == "mp4":
                # Wersja „progressive” – audio+video
                ydl_opts = {
                    "format": self.format_id,
                    "outtmpl": f"{self.folder}/%(title)s.%(ext)s",
                    "ffmpeg_location": self.ffmpeg_path,
                    "no-mtime": True,
                    "progress_hooks": [_progress],
                    "quiet": True,
                    "no_warnings": True,
                    "ratelimit": 25_000_000,
                    "retries": 3,
                    "no_check_certificate": True,
                }
                _log(f"Rozpoczynam pobieranie wideo (format_id={self.format_id}) → {self.url}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([self.url])
                success = True
            # "mp3"
            else:
                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": f"{self.folder}/%(title)s.%(ext)s",
                    "keepvideo": False,
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "320",
                        }
                    ],
                    "ffmpeg_location": self.ffmpeg_path,
                    "no-mtime": True,
                    "progress_hooks": [_progress],
                    "quiet": True,
                    "no_warnings": True,
                }
                _log(f"Rozpoczynam pobieranie audio → {self.url}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([self.url])
                success = True

        except Exception as e:
            error_msg = str(e)
            _log(f"Błąd: {error_msg}")

        if self.cancelled:
            error_msg = "Pobieranie anulowane przez użytkownika"
            _log(error_msg)
            success = False

        self.finished_signal.emit(success, error_msg)

class FormatFetchThread(QThread):

    formats_ready = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            # Pobierz wszystkie dostępne formaty metadanych
            ydl_opts = {"quiet": True, "skip_download": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                formats = info.get("formats", [])

            muxed = []       # listowanie tylko plików audio+video w mp4
            video_only = {}  # dict height -> (format_id, fps)
            audio_only = []  # lista audio-only

            for f in formats:
                ext = f.get("ext")
                vcodec = f.get("vcodec")
                acodec = f.get("acodec")
                fmt_id = f.get("format_id")
                height = f.get("height") or 0
                fps = f.get("fps") or 0

                # MUXED MP4
                if vcodec != "none" and acodec != "none" and ext == "mp4" and height:
                    label = f"{height}p{' @'+str(fps)+'fps' if fps else ''} (muxed)"
                    muxed.append((height, fps, fmt_id, label))
                    continue

                # 2) VIDEO-ONLY (mp4 lub webm)
                if vcodec != "none" and acodec == "none" and height:
                    existing = video_only.get(height)
                    if not existing or fps > existing[1]:
                        video_only[height] = (fmt_id, fps)
                    continue

                # AUDIO-ONLY
                if acodec != "none" and vcodec == "none":
                    audio_only.append(fmt_id)
                    continue

            options = []

            # Opcje video-only + bestaudio (sortowane malejąco po height)
            if video_only and audio_only:
                audio_fmt = "bestaudio"
                for height in sorted(video_only.keys(), reverse=True):
                    fmt_vid, fps = video_only[height]
                    label = f"{height}p + audio"
                    combo = f"{fmt_vid}+{audio_fmt}"
                    options.append((combo, label))

            muxed.sort(key=lambda x: (x[0], x[1]), reverse=True)
            for _, _, fmt_id, label in muxed:
                clean_label = label.replace(" (muxed)", "")
                options.append((fmt_id, clean_label))

            if not options:
                raise ValueError("Brak dostępnych formatów do pobrania.")

            self.formats_ready.emit(options)

        except Exception as e:
            self.error.emit(str(e))
