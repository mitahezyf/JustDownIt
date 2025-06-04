# ui_mainwindow.py

import os
import time

import requests
import yt_dlp

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QTextCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QFileDialog, QRadioButton,
    QProgressBar, QMessageBox, QComboBox
)

from threads import InstallThread, DownloadThread, FormatFetchThread
from theme import apply_dark_theme
from ytdown_core import pobierz_miniaturke, pobierz_sciezke_ffmpeg


class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.current_url = ""
        self.ffmpeg_path = ""
        self.download_type = "mp4"
        # Lista dostępnych formatów
        self.available_formats = []

        self.setup_ui()
        self.setup_connections()
        self.set_default_download_folder()

    def setup_ui(self):
        """Konfiguracja interfejsu użytkownika"""
        self.setWindowTitle("YouTube Downloader")
        self.setGeometry(300, 300, 800, 600)
        self.setMinimumSize(700, 500)

        apply_dark_theme(self)

        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        section_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        normal_font = QFont("Segoe UI", 10)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ==========Nagłówek==========
        header = QLabel("YouTube Downloader")
        header.setFont(title_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #61afef; padding: 10px;")
        main_layout.addWidget(header)

        # ==========Sekcja URL + Miniaturka==========
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

        # ==========Dropdown z jakoscia==========
        quality_layout = QVBoxLayout()
        quality_layout.setSpacing(5)

        quality_label = QLabel("Jakość wideo:")
        quality_label.setFont(section_font)
        quality_layout.addWidget(quality_label)

        self.quality_combo = QComboBox()
        self.quality_combo.setFont(normal_font)
        self.quality_combo.addItem("Brak (brak URL)")
        self.quality_combo.setEnabled(False)

        self.quality_combo.setMaximumWidth(200)
        quality_layout.addWidget(self.quality_combo, alignment=Qt.AlignmentFlag.AlignLeft)

        main_layout.addLayout(quality_layout)

        # ==========Sekcja typu pobierania ==========
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

        # ==========Sekcja folderu docelowego==========
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

        # ==========Pasek postępu i przyciski==========
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

        # ==========Konsola logów==========
        log_layout = QVBoxLayout()
        log_layout.setSpacing(5)

        log_label = QLabel("Logi:")
        log_label.setFont(section_font)
        log_layout.addWidget(log_label)

        self.log_output = QTextEdit()
        self.log_output.setFont(normal_font)
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)

        main_layout.addLayout(log_layout, 1)

    def setup_connections(self):
        """Konfiguracja sygnałów i slotów"""
        self.type_mp4.toggled.connect(lambda: self.set_download_type("mp4"))
        self.type_mp3.toggled.connect(lambda: self.set_download_type("mp3"))
        self.browse_button.clicked.connect(self.browse_folder)
        self.download_button.clicked.connect(self.start_download)
        self.cancel_button.clicked.connect(self.cancel_download)
        self.clear_button.clicked.connect(self.clear_logs)
        self.url_input.textChanged.connect(self.on_url_changed)

    def set_default_download_folder(self):
        """
        Ustawia domyślny folder pobierania:
        1) ~/Pobrane
        2) ~/Downloads
        3) katalog domowy (~)
        """
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

    def on_url_changed(self, url_text: str):
        """
        Jeśli URL wygląda na YouTube, pobierz miniaturkę i asynchronicznie listę formatów.
        W przeciwnym razie zablokuj dropdown.
        """
        self.current_url = url_text.strip()

        # Reset combobox
        self.quality_combo.clear()
        self.quality_combo.addItem("Ładowanie formatów…")
        self.quality_combo.setEnabled(False)
        self.available_formats = []

        if "youtube.com/watch?v=" in self.current_url or "youtu.be/" in self.current_url:
            # 1) Pobierz miniaturkę
            self.fetch_thumbnail(self.current_url)
            # 2) Uruchom FormatFetchThread
            self.fetch_thread = FormatFetchThread(self.current_url)
            self.fetch_thread.formats_ready.connect(self.on_formats_ready)
            self.fetch_thread.error.connect(self.on_formats_error)
            self.fetch_thread.start()
        else:
            self.thumbnail_label.setText("Podaj pełny URL filmu YouTube")
            self.thumbnail_label.setPixmap(QPixmap())
            self.quality_combo.clear()
            self.quality_combo.addItem("Brak (brak URL)")
            self.quality_combo.setEnabled(False)

    def on_formats_ready(self, formats_list):
        """
        Gdy FormatFetchThreads zwróci listę [(format_id, label), ...], wypełniamy combobox.
        """
        self.available_formats = formats_list
        self.quality_combo.clear()
        for fmt_id, label in formats_list:
            self.quality_combo.addItem(label, userData=fmt_id)

        self.quality_combo.setEnabled(True)
        self.quality_combo.setCurrentIndex(0)
        self.log_message("Formaty pobrane pomyślnie.")

    def on_formats_error(self, err_msg):
        """Gdy pobieranie formatów się nie powiedzie"""
        self.log_message(f"Błąd pobierania formatów: {err_msg}")
        self.quality_combo.clear()
        self.quality_combo.addItem("Brak (błąd pobierania)")
        self.quality_combo.setEnabled(False)

    def fetch_thumbnail(self, url: str):
        """Pobiera miniaturkę i wyświetla ją"""
        self.thumbnail_label.setText("Pobieranie miniatury…")
        try:
            thumb_url = pobierz_miniaturke(url)
            if thumb_url:
                self.log_message(f"Pobrano URL miniatury: {thumb_url}")
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
            else:
                self.thumbnail_label.setText("Nie znaleziono miniatury")
                self.log_message("Nie udało się pobrać miniatury")
        except Exception as e:
            self.thumbnail_label.setText("Błąd pobierania miniatury")
            self.log_message(f"Błąd pobierania miniatury: {e}")

    def log_message(self, message: str):
        """Wyświetla komunikat w konsoli logów"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        self.log_output.append(formatted_msg)
        self.log_output.moveCursor(QTextCursor.MoveOperation.End)

    def set_download_type(self, download_type: str):
        """Ustawia typ pobierania (mp4/mp3)"""
        self.download_type = download_type
        self.log_message(f"Wybrano typ: {download_type.upper()}")

    def browse_folder(self):
        """Otwiera dialog wyboru folderu"""
        folder = QFileDialog.getExistingDirectory(
            self, "Wybierz folder docelowy", os.path.expanduser("~")
        )
        if folder:
            self.folder_input.setText(folder)
            self.log_message(f"Wybrano folder: {folder}")

    def clear_logs(self):
        """Czyści konsolę logów"""
        self.log_output.clear()
        self.log_message("Logi wyczyszczone")

    def cancel_download(self):
        """Anuluje bieżące pobieranie"""
        if hasattr(self, 'download_thread') and self.download_thread.isRunning():
            self.download_thread.cancel()
            self.log_message("Wysyłanie żądania anulowania…")
            self.cancel_button.setEnabled(False)

    def start_download(self):
        """Rozpoczyna pobieranie w wybranym formacie (może to być muxed lub video+audio)"""
        url = self.url_input.text().strip()
        folder = self.folder_input.text().strip()

        if not url:
            QMessageBox.warning(self, "Błąd", "Wprowadź URL filmu YouTube")
            return
        if not os.path.isdir(folder):
            QMessageBox.warning(self, "Błąd", "Folder docelowy nie istnieje")
            return
        if "youtube.com" not in url and "youtu.be" not in url:
            QMessageBox.warning(self, "Błąd", "Nieprawidłowy URL YouTube")
            return

        # Sprawdź ffmpeg
        if not self.ffmpeg_path or not os.path.exists(self.ffmpeg_path):
            QMessageBox.warning(
                self,
                "Uwaga",
                "FFmpeg nie zostało odnalezione. Łączenie (jeśli video-only) może się nie powieść. "
                "Zainstaluj ffmpeg lub `pip install imageio-ffmpeg`."
            )
            self.log_message("Ostrzeżenie: FFmpeg nie odnalezione.")

        if self.download_type == "mp4":
            if not (self.quality_combo.isEnabled() and self.quality_combo.currentIndex() >= 0):
                QMessageBox.warning(self, "Błąd", "Brak dostępnych formatów do pobrania")
                return
            format_id = self.quality_combo.currentData()
        else:
            format_id = None

        # Blokujemy UI i ruszamy wątek
        self.set_ui_enabled(False)
        self.log_message(f"Rozpoczynanie pobierania ({self.download_type})…")
        self.progress_bar.setValue(0)

        self.download_thread = DownloadThread(
            url,
            self.ffmpeg_path,
            folder,
            self.download_type,
            format_id,
            self.log_message
        )
        self.download_thread.log_signal.connect(self.log_message)
        self.download_thread.progress_signal.connect(lambda percent: self.update_progress(percent))
        self.download_thread.finished_signal.connect(self.on_download_finished)
        self.download_thread.start()

    def update_progress(self, value: float):
        """Aktualizuje pasek postępu"""
        progress_value = int(value)
        if progress_value < 0:
            progress_value = 0
        elif progress_value > 100:
            progress_value = 100

        self.progress_bar.setValue(progress_value)
        if 0 < progress_value < 100:
            self.download_button.setText(f"Pobieranie… {progress_value}%")
        else:
            self.download_button.setText("Rozpocznij pobieranie")

    def set_ui_enabled(self, enabled: bool):
        """Włącza/wyłącza UI podczas pobierania"""
        self.url_input.setEnabled(enabled)
        self.type_mp4.setEnabled(enabled)
        self.type_mp3.setEnabled(enabled)
        self.quality_combo.setEnabled(enabled and self.quality_combo.count() > 0)
        self.browse_button.setEnabled(enabled)
        self.download_button.setEnabled(enabled)
        self.clear_button.setEnabled(enabled)
        self.cancel_button.setEnabled(not enabled)

        self.download_button.setText("Pobieranie…" if not enabled else "Rozpocznij pobieranie")

    def on_download_finished(self, success: bool, error_msg: str):
        """Obsługa zakończenia pobierania"""
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

    def set_ffmpeg_path(self, path: str):
        """Ustawia ścieżkę do ffmpeg po instalacji"""
        self.ffmpeg_path = path
