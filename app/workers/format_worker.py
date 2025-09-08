import yt_dlp
from PyQt6.QtCore import QThread, pyqtSignal


# worker w osobnym watku ktory pobiera dostepne formaty wideo i audio dla url
class FormatFetchWorker(QThread):
    formats_ready = pyqtSignal(list)  # lista par (format_id, label)
    error = pyqtSignal(str)  # sygnal bledu

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    # glowna metoda uruchamiana w watku
    def run(self):
        try:
            # pobiera metadane o formatach bez sciagania pliku
            with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
                info = ydl.extract_info(self.url, download=False)
                formats = info.get("formats", [])

            muxed, video_only, audio_only = [], {}, []

            # przechodzi po wszystkich formatach i klasyfikuje je
            for f in formats:
                ext = f.get("ext")
                vcodec = f.get("vcodec")
                acodec = f.get("acodec")
                fid = f.get("format_id")
                height = f.get("height") or 0
                fps = f.get("fps") or 0

                # format z video i audio razem (muxed)
                if vcodec != "none" and acodec != "none" and ext == "mp4" and height:
                    label = f"{height}p" + (f" @ {fps}fps" if fps else "")
                    muxed.append((height, fps, fid, label))
                    continue

                # format tylko video (bez audio)
                if vcodec != "none" and acodec == "none" and height:
                    ex = video_only.get(height)
                    # wybiera wariant z najwyzszym fps dla danej wysokosci
                    if not ex or fps > ex[1]:
                        video_only[height] = (fid, fps)
                    continue

                # format tylko audio
                if acodec != "none" and vcodec == "none":
                    audio_only.append(fid)

            options = []

            # laczy najlepsze warianty video-only z audio
            if video_only and audio_only:
                for h in sorted(video_only.keys(), reverse=True):
                    fid, _fps = video_only[h]
                    options.append((f"{fid}+bestaudio", f"{h}p + audio"))

            # dodaje warianty muxed posortowane od najlepszych
            muxed.sort(key=lambda x: (x[0], x[1]), reverse=True)
            for _, _, fid, label in muxed:
                options.append((fid, label))

            # jesli nie ma zadnych opcji to traktuje jako blad
            if not options:
                raise ValueError("Brak dostępnych formatów do pobrania.")

            # przekazuje gotowe opcje do ui
            self.formats_ready.emit(options)

        except Exception as e:
            # wysyla blad do ui
            self.error.emit(str(e))
