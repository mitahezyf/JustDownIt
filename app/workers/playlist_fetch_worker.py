import yt_dlp
from PyQt6.QtCore import QThread, pyqtSignal


# worker w osobnym watku ktory pobiera liste filmow z playlisty youtube
class PlaylistFetchWorker(QThread):
    result = pyqtSignal(list)  # lista slownikow {'id','url','title'}
    error = pyqtSignal(str)  # sygnal bledu

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    # glowna metoda uruchamiana w watku
    def run(self):
        try:
            # extract_flat = True sprawia ze yt-dlp pobiera tylko metadane playlisty
            opts = {"quiet": True, "skip_download": True, "extract_flat": True}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=False)

            # entries zawiera liste elementow playlisty
            entries = info.get("entries", []) or []
            out = []
            for e in entries:
                vid = e.get("id")
                if not vid:
                    continue
                # buduje slownik z podstawowymi informacjami
                out.append(
                    {
                        "id": vid,
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "title": e.get("title") or "",
                    }
                )

            # przekazuje gotowa liste do ui
            self.result.emit(out)

        except Exception as e:
            # w razie bledu przekazuje komunikat do ui
            self.error.emit(str(e))
