# threads.py

import yt_dlp
from PyQt6.QtCore import QThread, pyqtSignal

from app.core.ytdown_core import instaluj_biblioteki


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
                    percent_float = float(percent_str.strip().replace("%", ""))
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
                _log(
                    f"Rozpoczynam pobieranie wideo (format_id={self.format_id}) → {self.url}"
                )
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

            muxed = []  # listowanie tylko plików audio+video w mp4
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


# threads.py  (DOPISZ NA KONIEC PLIKU)

from PyQt6.QtCore import QThread, pyqtSignal


class PlaylistFetchThread(QThread):
    """Szybko pobiera listę elementów z playlisty (id, tytuł)."""

    result = pyqtSignal(list)  # list[{'id','url','title'}]
    error = pyqtSignal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            ydl_opts = {"quiet": True, "skip_download": True, "extract_flat": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
            entries = info.get("entries", [])
            out = []
            for e in entries:
                vid = e.get("id")
                if not vid:
                    continue
                out.append(
                    {
                        "id": vid,
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "title": e.get("title") or "",
                    }
                )
            self.result.emit(out)
        except Exception as e:
            self.error.emit(str(e))


class PlaylistFormatsThread(QThread):
    """
    Dla każdego elementu playlisty pobiera pełne metadane:
      - czas trwania (duration),
      - miniaturkę (thumb_url),
      - listę formatów [(format_id,label), ...] (muxed oraz video+audio).
    Emisja per-wiersz: row_ready(row, thumb_url, duration, formats)
    """

    row_ready = pyqtSignal(int, str, int, list)
    error = pyqtSignal(str)

    def __init__(self, entries: list[dict]):
        super().__init__()
        self.entries = entries

    def run(self):
        try:
            for row, e in enumerate(self.entries):
                url = e["url"]
                with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
                    info = ydl.extract_info(url, download=False)

                # Czas
                duration = info.get("duration")

                # Miniatura – bierz pierwszą lepszą (yt-dlp daje listę)
                thumb_url = None
                thumbs = info.get("thumbnails") or []
                if thumbs:
                    # weź większą
                    thumbs = sorted(
                        thumbs,
                        key=lambda t: t.get("width", 0) * t.get("height", 0),
                        reverse=True,
                    )
                    thumb_url = thumbs[0].get("url")

                # Formaty
                formats_raw = info.get("formats", [])
                muxed = []
                video_only = {}
                audio_only = []

                for f in formats_raw:
                    ext = f.get("ext")
                    vcodec = f.get("vcodec")
                    acodec = f.get("acodec")
                    fmt_id = f.get("format_id")
                    height = f.get("height") or 0
                    fps = f.get("fps") or 0

                    # MP4 muxed
                    if (
                        vcodec != "none"
                        and acodec != "none"
                        and ext == "mp4"
                        and height
                    ):
                        label = f"{height}p" + (f" {fps}fps" if fps else "")
                        muxed.append((height, fps, fmt_id, label))
                        continue
                    # Video-only (weź najlepszy fps dla wysokości)
                    if vcodec != "none" and acodec == "none" and height:
                        ex = video_only.get(height)
                        if not ex or fps > ex[1]:
                            video_only[height] = (fmt_id, fps)
                        continue
                    # Audio-only
                    if acodec != "none" and vcodec == "none":
                        audio_only.append(fmt_id)

                options = []
                # video_only + bestaudio
                if video_only and audio_only:
                    for h in sorted(video_only.keys(), reverse=True):
                        fmt_vid, fps = video_only[h]
                        label = f"{h}p + audio"
                        options.append((f"{fmt_vid}+bestaudio", label))

                muxed.sort(key=lambda x: (x[0], x[1]), reverse=True)
                for _, _, fid, label in muxed:
                    options.append((fid, label))

                if not options:
                    options = [("best", "Auto")]

                options.append(("bestaudio", "Tylko audio (MP3)"))

                self.row_ready.emit(row, thumb_url or "", duration or 0, options)

        except Exception as e:
            self.error.emit(str(e))
