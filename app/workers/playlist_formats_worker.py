import yt_dlp
from PyQt6.QtCore import QThread, pyqtSignal


# worker w osobnym watku ktory dla kazdego elementu playlisty pobiera szczegoly
# zwraca miniaturke, czas trwania oraz liste dostepnych formatow
class PlaylistFormatsWorker(QThread):

    row_ready = pyqtSignal(int, str, int, list)  # przekazuje dane o jednym wierszu
    error = pyqtSignal(str)  # sygnal bledu

    def __init__(self, entries: list[dict]):
        super().__init__()
        self.entries = entries

    # glowna metoda uruchamiana w watku
    def run(self):
        try:
            for row, e in enumerate(self.entries):
                url = e["url"]
                with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
                    info = ydl.extract_info(url, download=False)

                # pobiera czas trwania filmu
                duration = info.get("duration") or 0

                # wybiera najlepsza miniaturke (najwieksze pole powierzchni)
                thumbs = info.get("thumbnails") or []
                thumb_url = ""
                if thumbs:
                    thumbs = sorted(
                        thumbs,
                        key=lambda t: (t.get("width", 0) * t.get("height", 0)),
                        reverse=True,
                    )
                    thumb_url = thumbs[0].get("url") or ""

                # buduje liste formatow podobnie jak w FormatFetchWorker
                formats_raw = info.get("formats", [])
                muxed, video_only, audio_only = [], {}, []
                for f in formats_raw:
                    ext = f.get("ext")
                    vcodec = f.get("vcodec")
                    acodec = f.get("acodec")
                    fid = f.get("format_id")
                    h = f.get("height") or 0
                    fps = f.get("fps") or 0

                    # format wideo z audio razem (muxed)
                    if vcodec != "none" and acodec != "none" and ext == "mp4" and h:
                        muxed.append(
                            (h, fps, fid, f"{h}p" + (f" {fps}fps" if fps else ""))
                        )
                        continue

                    # format tylko wideo
                    if vcodec != "none" and acodec == "none" and h:
                        ex = video_only.get(h)
                        if not ex or fps > ex[1]:
                            video_only[h] = (fid, fps)
                        continue

                    # format tylko audio
                    if acodec != "none" and vcodec == "none":
                        audio_only.append(fid)

                options = []
                # laczy najlepsze opcje video-only z audio
                if video_only and audio_only:
                    for h in sorted(video_only.keys(), reverse=True):
                        fid, _fps = video_only[h]
                        options.append((f"{fid}+bestaudio", f"{h}p + audio"))

                # dodaje warianty muxed posortowane od najlepszych
                muxed.sort(key=lambda x: (x[0], x[1]), reverse=True)
                for _, _, fid, label in muxed:
                    options.append((fid, label))

                # jesli nic nie znaleziono to daje auto i audio
                if not options:
                    options = [("best", "Auto")]
                options.append(("bestaudio", "Tylko audio (MP3)"))

                # przekazuje gotowe dane dla jednego elementu playlisty
                self.row_ready.emit(row, thumb_url, int(duration), options)

        except Exception as e:
            # jesli cos poszlo nie tak wysyla blad
            self.error.emit(str(e))
