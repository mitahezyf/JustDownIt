# main.py
import os
import sys
import time

from PyQt6.QtWidgets import QApplication, QMainWindow, QStatusBar
from PyQt6.QtGui import QIcon

from ui_mainwindow import YouTubeDownloader
from threads import InstallThread
from ytdown_core import pobierz_sciezke_ffmpeg

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.downloader_widget = YouTubeDownloader()
        self.setCentralWidget(self.downloader_widget)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Po wczytaniu UI od razu startujemy temat instalacji bibliotek
        self.install_thread = InstallThread(self.log_message)
        self.install_thread.log_signal.connect(self.log_message)
        self.install_thread.finished_signal.connect(self.on_install_finished)
        self.install_thread.start()

    def log_message(self, msg: str):
        timestamp = time.strftime("%H:%M:%S")
        self.status_bar.showMessage(f"[{timestamp}] {msg}")

    def on_install_finished(self):
        try:
            ff_path = pobierz_sciezke_ffmpeg()
            self.downloader_widget.set_ffmpeg_path(ff_path)
            self.log_message(f"FFmpeg: {ff_path}")
        except Exception as e:
            self.log_message(f"Błąd FFmpeg: {e}")
            self.downloader_widget.set_ffmpeg_path("")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    if os.path.exists("ytdownico.png"):
        app.setWindowIcon(QIcon("ytdownico.png"))

    window = MainWindow()
    window.setWindowTitle("YouTube Downloader")
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec())
