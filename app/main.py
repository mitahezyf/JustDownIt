from __future__ import annotations

import os
import sys
import time

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QStatusBar

from app.core.paths import get_ffmpeg_path
from app.ui.ui_mainwindow import YouTubeDownloader


# glowne okno aplikacji
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        # glowny widget aplikacji (twoj ui)
        self.downloader_widget = YouTubeDownloader()
        self.setCentralWidget(self.downloader_widget)

        # pasek statusu
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # ustawia sciezke do ffmpeg podczas startu
        try:
            ff_path = get_ffmpeg_path()
            self.downloader_widget.set_ffmpeg_path(ff_path)
            self.log_message(f"FFmpeg: {ff_path}")
        except Exception as e:
            # aplikacja moze dzialac bez ffmpeg, ale konwersje beda problematyczne
            self.downloader_widget.set_ffmpeg_path("")
            self.log_message(f"Nie wykryto FFmpeg: {e}")

    # metoda do logowania komunikatow w pasku statusu
    def log_message(self, msg: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.status_bar.showMessage(f"[{timestamp}] {msg}")


# funkcja startowa aplikacji
def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # ustawia ikone aplikacji jesli istnieje plik
    icon_path = os.path.join("images", "ytdownico.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.setWindowTitle("JustDownIt")
    window.resize(900, 650)
    window.show()
    return app.exec()


# standardowy punkt wejscia
if __name__ == "__main__":
    sys.exit(main())
