# ui_mainwindow.py
import os
import time
import requests

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QTextCursor, QPixmap
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QFileDialog, QRadioButton,
    QProgressBar, QMessageBox
)

from threads import InstallThread, DownloadThread
from theme import apply_dark_theme
from ytdown_core import pobierz_miniaturke, pobierz_sciezke_ffmpeg


class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.current_url = ""
        self.ffmpeg_path = ""
        self.download_type = "mp4"

        self.setup_ui()
        self.setup_connections()
        self.set_default_download_folder()
        # Proces instalacji bibliotek ruszy dopiero po wywołaniu z main.py

    def setup_ui(self):
        self.setWindowTitle("YouTube Downloader")
        self.setGeometry(300, 300, 800, 600)
        self.setMinimumSize(700, 500)

        apply_dark_theme(self)  # stosujemy ciemny motyw

        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        section_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        normal_font = QFont("Segoe UI", 10)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("YouTube Downloader")
        header.setFont(title_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #61afef; padding: 10px;")
        main_layout.addWidget(header)

        # ─── Sekcja URL ───────────────────────────────────────────────────────
        url_layout = QVBoxLayout()
        url_layout.setSpacing(5)

        url_label = QLabel("URL filmu:")
        url_label.setFont(section_font)
        url_layout.addWidget(url_label)

        self.url_input = QLineEdit()
        self.url_input.setFont(normal_font)
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        url_layout.addWidget(self.url_input)

        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(320, 180)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("""
            background-color: #2b2f3a;
            border: 1px solid #3d4351;
            border-radius: 4px;
        """)
        self.thumbnail_label.setText("Miniaturka pojawi się tutaj po podaniu URL")
        url_layout.addWidget(self.thumbnail_label, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addLayout(url_layout)

        # ─── Sekcja typu pobierania ───────────────────────────────────────────
        type_layout = QVBoxLayout()
        type_layout.setSpacing(5)

        type_label = QLabel("Typ pobierania:")
        type_label.setFont(section_font)
        type_layout.addWidget(type_label)

        type_buttons = QHBoxLayout()
        self.type_mp4 = QRadioButton("MP4 (wideo)")
        self.type_mp4.setFont(normal_font)
        self.type_mp4.setChecked(True)
        self.type_mp3 = QRadioButton("MP3 (audio)")
        self.type_mp3.setFont(normal_font)

        type_buttons.addWidget(self.type_mp4)
        type_buttons.addWidget(self.type_mp3)
        type_buttons.addStretch()
        type_layout.addLayout(type_buttons)

        main_layout.addLayout(type_layout)

        # ─── Sekcja folderu docelowego ───────────────────────────────────────
        folder_layout = QVBoxLayout()
        folder_layout.setSpacing(5)

        folder_label = QLabel("Folder docelowy:")
        folder_label.setFont(section_font)
        folder_layout.addWidget(folder_label)

        folder_input_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setFont(normal_font)
        self.folder_input.setReadOnly(True)
        folder_input_layout.addWidget(self.folder_input)

        self.browse_button = QPushButton("Przeglądaj…")
        self.browse_button.setFont(normal_font)
        folder_input_layout.addWidget(self.browse_button)
        folder_layout.addLayout(folder_input_layout)

        main_layout.addLayout(folder_layout)

        # ─── Pasek postępu i przyciski ────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setFont(normal_font)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        main_layout.addWidget(self.progress_bar)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.download_button = QPushButton("Rozpocznij pobieranie")
        self.download_button.setFont(section_font)
        self.download_button.setStyleSheet(
            "background-color: #61afef; color: #282c34; padding: 8px;"
        )
        buttons_layout.addWidget(self.download_button)

        self.cancel_button = QPushButton("Anuluj pobieranie")
        self.cancel_button.setFont(normal_font)
        self.cancel_button.setStyleSheet(
            "background-color: #e06c75; color: #282c34; padding: 8px;"
        )
        self.cancel_button.setEnabled(False)
        buttons_layout.addWidget(self.cancel_button)

        self.clear_button = QPushButton("Wyczyść")
        self.clear_button.setFont(normal_font)
        buttons_layout.addWidget(self.clear_button)

        main_layout.addLayout(buttons_layout)

        # ─── Konsola logów ────────────────────────────────────────────────────
        log_layout = QVBoxLayout()
        log_layout.setSpacing(5)

        log_label = QLabel("Logi:")
        log_label.setFont(section_font)
        log_layout.addWidget(log_label)

        self.log_output = QTextEdit()
        self.log_output.setFont(normal_font)
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)

        main_layout.addLayout(log_layout, 1)  # rozciągnięcie

        # ─── Status bar (tu: tylko placeholder, właściwy QStatusBar jest w main.py) ─
        # W tej wersji QWidget nie ma wbudowanego status baru, ale logi wyświetlamy
        # w polu tekstowym. StatusBar można dodać, gdybyśmy dziedziczyli QMainWindow.

    def setup_connections(self):
        self.type_mp4.toggled.connect(lambda: self.set_download_type("mp4"))
        self.type_mp3.toggled.connect(lambda: self.set_download_type("mp3"))
        self.browse_button.clicked.connect(self.browse_folder)
        self.download_button.clicked.connect(self.start_download)
        self.cancel_button.clicked.connect(self.cancel_download)
        self.clear_button.clicked.connect(self.clear_logs)
        self.url_input.textChanged.connect(self.check_url_and_fetch_thumbnail)

    def set_default_download_folder(self):
        home = os.path.expanduser("~")
        pobrane = os.path.join(home, "Pobrane")
        downloads = os.path.join(home, "Downloads")

        if os.path.isdir(pobrane):
            default_folder = pobrane
        elif os.path.isdir(downloads):
            default_folder = downloads
        else:
            default_folder = home

        self.folder_input.setText(default_folder)
        self.log_message(f"Domyślny folder pobierania: {default_folder}")

    def cancel_download(self):
        if hasattr(self, 'download_thread') and self.download_thread.isRunning():
            self.download_thread.cancel()
            self.log_message("Wysyłanie żądania anulowania…")
            self.cancel_button.setEnabled(False)

    def check_url_and_fetch_thumbnail(self, url):
        self.current_url = url
        try:
            if "youtube.com/watch?v=" in url or "youtu.be/" in url:
                self.fetch_thumbnail(url)
            else:
                self.thumbnail_label.setText("Podaj pełny URL filmu YouTube")
                self.thumbnail_label.setPixmap(QPixmap())
        except Exception as e:
            self.log_message(f"Krytyczny błąd: {str(e)}")

    def fetch_thumbnail(self, url):
        self.thumbnail_label.setText("Pobieranie miniatury…")
        try:
            thumb_url = pobierz_miniaturke(url)
            if thumb_url:
                self.log_message(f"Pobrano URL miniatury: {thumb_url}")
                self.download_thumbnail_image(thumb_url)
            else:
                self.thumbnail_label.setText("Nie znaleziono miniatury")
                self.log_message("Nie udało się pobrać miniatury")
        except Exception as e:
            self.log_message(f"Błąd pobierania miniatury: {e}")

    def download_thumbnail_image(self, thumb_url):
        try:
            response = requests.get(thumb_url, timeout=5)
            response.raise_for_status()
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    320, 180,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.thumbnail_label.setPixmap(pixmap)
            else:
                self.thumbnail_label.setText("Błąd ładowania miniatury")
        except Exception as e:
            self.log_message(f"Błąd pobierania miniatury: {e}")
            self.thumbnail_label.setText("Błąd pobierania miniatury")

    def log_message(self, message):
        ts = time.strftime("%H:%M:%S")
        text = f"[{ts}] {message}"
        self.log_output.append(text)
        self.log_output.moveCursor(QTextCursor.MoveOperation.End)

    def set_download_type(self, download_type):
        self.download_type = download_type
        self.log_message(f"Wybrano typ: {download_type.upper()}")

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Wybierz folder docelowy", os.path.expanduser("~")
        )
        if folder:
            self.folder_input.setText(folder)
            self.log_message(f"Wybrano folder: {folder}")

    def clear_logs(self):
        self.log_output.clear()
        self.log_message("Logi wyczyszczone")

    def start_download(self):
        url = self.url_input.text().strip()
        folder = self.folder_input.text().strip()

        if not url:
            QMessageBox.warning(self, "Błąd", "Wprowadź URL filmu YouTube")
            return
        if not os.path.isdir(folder):
            QMessageBox.warning(self, "Błąd", "Folder docelowy nie istnieje")
            return
        if not self.ffmpeg_path or not os.path.exists(self.ffmpeg_path):
            QMessageBox.warning(self, "Błąd", "FFmpeg nie jest dostępny")
            return
        if "youtube.com" not in url and "youtu.be" not in url:
            QMessageBox.warning(self, "Błąd", "Nieprawidłowy URL YouTube")
            return

        self.set_ui_enabled(False)
        self.log_message(f"Rozpoczynanie pobierania ({self.download_type})…")
        self.progress_bar.setValue(0)

        # Tworzymy i konfigurujemy wątek pobierania
        self.download_thread = DownloadThread(
            url, self.ffmpeg_path, folder, self.download_type, self.log_message
        )
        self.download_thread.log_signal.connect(self.log_message)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.finished_signal.connect(self.on_download_finished)
        self.download_thread.start()

    def update_progress(self, value):
        val = int(value)
        if val < 0: val = 0
        if val > 100: val = 100
        self.progress_bar.setValue(val)
        if 0 < val < 100:
            self.download_button.setText(f"Pobieranie… {val}%")
        else:
            self.download_button.setText("Rozpocznij pobieranie")

    def set_ui_enabled(self, enabled):
        self.url_input.setEnabled(enabled)
        self.type_mp4.setEnabled(enabled)
        self.type_mp3.setEnabled(enabled)
        self.browse_button.setEnabled(enabled)
        self.download_button.setEnabled(enabled)
        self.clear_button.setEnabled(enabled)
        self.cancel_button.setEnabled(not enabled)
        self.download_button.setText("Pobieranie…" if not enabled else "Rozpocznij pobieranie")

    def on_download_finished(self, success: bool, error_msg: str):
        self.set_ui_enabled(True)
        if success:
            self.progress_bar.setValue(100)
            self.log_message("Pobieranie zakończone pomyślnie!")
            QMessageBox.information(self, "Sukces", "Pobieranie zakończone pomyślnie!")
        else:
            if "anulowane" not in error_msg.lower():
                self.progress_bar.setValue(0)
            self.log_message(f"Błąd pobierania: {error_msg}")
            if "anulowane" not in error_msg.lower():
                QMessageBox.critical(self, "Błąd", f"Pobieranie nie powiodło się:\n{error_msg}")

    def set_ffmpeg_path(self, path):
        self.ffmpeg_path = path
