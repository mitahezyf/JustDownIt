#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ytdown_gui.py

Nowoczesny interfejs graficzny dla ytdown_core.py
Wymagane biblioteki: PyQt6
"""

import os
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QFileDialog, QButtonGroup, QRadioButton,
    QProgressBar, QFrame, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QTextCursor, QPalette, QColor

# Import modułu core
from ytdown_core import (
    instaluj_biblioteki,
    pobierz_sciezke_ffmpeg,
    pobierz_wideo_mp4,
    pobierz_audio_mp3
)


# Klasa wątku do instalacji bibliotek
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


# Klasa wątku do pobierania
class DownloadThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, url, ffmpeg_path, folder, download_type, log_func):
        super().__init__()
        self.url = url
        self.ffmpeg_path = ffmpeg_path
        self.folder = folder
        self.download_type = download_type
        self.log_func = log_func

    def run(self):
        success = False
        error_msg = ""

        def _log(msg):
            self.log_signal.emit(msg)

        try:
            if self.download_type == "mp4":
                pobierz_wideo_mp4(
                    self.url,
                    self.ffmpeg_path,
                    self.folder,
                    _log
                )
                success = True
            elif self.download_type == "mp3":
                pobierz_audio_mp3(
                    self.url,
                    self.ffmpeg_path,
                    self.folder,
                    _log
                )
                success = True
        except Exception as e:
            error_msg = str(e)
            _log(f"Błąd: {error_msg}")

        self.finished_signal.emit(success, error_msg)


# Główne okno aplikacji
class YouTubeDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()
        self.ffmpeg_path = ""
        self.download_type = "mp4"
        self.check_dependencies()

    def setup_ui(self):
        """Konfiguracja interfejsu użytkownika"""
        self.setWindowTitle("YouTube Downloader")
        self.setGeometry(300, 300, 800, 600)
        self.setMinimumSize(700, 500)

        # Główny kontener
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.setCentralWidget(main_widget)

        # Styl ciemnego motywu
        self.apply_dark_theme()

        # Fonty
        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        section_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        normal_font = QFont("Segoe UI", 10)

        # Nagłówek
        header = QLabel("YouTube Downloader")
        header.setFont(title_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #61afef; padding: 10px;")
        main_layout.addWidget(header)

        # Sekcja URL
        url_layout = QVBoxLayout()
        url_layout.setSpacing(5)

        url_label = QLabel("URL filmu:")
        url_label.setFont(section_font)
        url_layout.addWidget(url_label)

        self.url_input = QLineEdit()
        self.url_input.setFont(normal_font)
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        url_layout.addWidget(self.url_input)

        main_layout.addLayout(url_layout)

        # Sekcja typu pobierania
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

        # Sekcja folderu docelowego
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

        self.browse_button = QPushButton("Przeglądaj...")
        self.browse_button.setFont(normal_font)
        folder_input_layout.addWidget(self.browse_button)
        folder_layout.addLayout(folder_input_layout)

        main_layout.addLayout(folder_layout)

        # Pasek postępu
        self.progress_bar = QProgressBar()
        self.progress_bar.setFont(normal_font)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        main_layout.addWidget(self.progress_bar)

        # Przyciski akcji
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.download_button = QPushButton("Rozpocznij pobieranie")
        self.download_button.setFont(section_font)
        self.download_button.setStyleSheet(
            "background-color: #61afef; color: #282c34; padding: 8px;"
        )
        buttons_layout.addWidget(self.download_button)

        self.clear_button = QPushButton("Wyczyść")
        self.clear_button.setFont(normal_font)
        buttons_layout.addWidget(self.clear_button)

        main_layout.addLayout(buttons_layout)

        # Konsola logów
        log_layout = QVBoxLayout()
        log_layout.setSpacing(5)

        log_label = QLabel("Logi:")
        log_label.setFont(section_font)
        log_layout.addWidget(log_label)

        self.log_output = QTextEdit()
        self.log_output.setFont(normal_font)
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)

        main_layout.addLayout(log_layout, 1)  # Rozciągnij obszar logów

        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.setFont(normal_font)
        self.status_bar.showMessage("Gotowy")

    def setup_connections(self):
        """Konfiguracja połączeń sygnałów"""
        self.type_mp4.toggled.connect(
            lambda: self.set_download_type("mp4")
        )
        self.type_mp3.toggled.connect(
            lambda: self.set_download_type("mp3")
        )
        self.browse_button.clicked.connect(self.browse_folder)
        self.download_button.clicked.connect(self.start_download)
        self.clear_button.clicked.connect(self.clear_logs)

    def apply_dark_theme(self):
        """Stosuje ciemny motyw do aplikacji"""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(40, 44, 52))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(171, 178, 191))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 38, 45))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(46, 50, 60))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(40, 44, 52))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(171, 178, 191))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(171, 178, 191))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(61, 67, 81))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(171, 178, 191))
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(97, 175, 239))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)

        self.setPalette(dark_palette)

        # Dodatkowe style
        self.setStyleSheet("""
            QLineEdit, QTextEdit {
                background-color: #2b2f3a;
                border: 1px solid #3d4351;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background-color: #3d4351;
                border: 1px solid #3d4351;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #4a5060;
                border: 1px solid #61afef;
            }
            QRadioButton {
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QProgressBar {
                border: 1px solid #3d4351;
                border-radius: 4px;
                background: #2b2f3a;
            }
            QProgressBar::chunk {
                background-color: #61afef;
                border-radius: 3px;
            }
        """)

    def log_message(self, message):
        """Wyświetla wiadomość w konsoli logów"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        self.log_output.append(formatted_msg)

        # Autoscroll
        self.log_output.moveCursor(QTextCursor.MoveOperation.End)

        # Aktualizacja status bar
        self.status_bar.showMessage(message)

    def set_download_type(self, download_type):
        """Ustawia typ pobierania"""
        self.download_type = download_type
        self.log_message(f"Wybrano typ: {download_type.upper()}")

    def browse_folder(self):
        """Otwiera dialog wyboru folderu"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Wybierz folder docelowy",
            os.path.expanduser("~")
        )

        if folder:
            self.folder_input.setText(folder)
            self.log_message(f"Wybrano folder: {folder}")

    def clear_logs(self):
        """Czyści konsolę logów"""
        self.log_output.clear()
        self.log_message("Logi wyczyszczone")

    def check_dependencies(self):
        """Sprawdza i instaluje wymagane zależności"""
        self.log_message("Sprawdzanie wymaganych bibliotek...")
        self.install_thread = InstallThread(self.log_message)
        self.install_thread.log_signal.connect(self.log_message)
        self.install_thread.finished_signal.connect(self.on_install_finished)
        self.install_thread.start()

    def on_install_finished(self):
        """Obsługa zakończenia instalacji bibliotek"""
        self.log_message("Biblioteki gotowe")
        try:
            self.ffmpeg_path = pobierz_sciezke_ffmpeg()
            self.log_message(f"Znaleziono FFmpeg: {self.ffmpeg_path}")
        except Exception as e:
            self.log_message(f"Błąd FFmpeg: {str(e)}")
            self.ffmpeg_path = ""

    def start_download(self):
        """Rozpoczyna proces pobierania"""
        url = self.url_input.text().strip()
        folder = self.folder_input.text().strip()

        # Walidacja
        if not url:
            QMessageBox.warning(self, "Błąd", "Wprowadź URL filmu YouTube")
            return

        if not folder:
            QMessageBox.warning(self, "Błąd", "Wybierz folder docelowy")
            return

        if not os.path.exists(folder):
            QMessageBox.warning(self, "Błąd", "Wybrany folder nie istnieje")
            return

        if not self.ffmpeg_path or not os.path.exists(self.ffmpeg_path):
            QMessageBox.warning(self, "Błąd", "FFmpeg nie jest dostępny")
            return

        # Blokowanie UI podczas pobierania
        self.set_ui_enabled(False)
        self.log_message(f"Rozpoczynanie pobierania ({self.download_type})...")
        self.progress_bar.setValue(0)

        # Uruchom wątek pobierania
        self.download_thread = DownloadThread(
            url,
            self.ffmpeg_path,
            folder,
            self.download_type,
            self.log_message
        )
        self.download_thread.log_signal.connect(self.log_message)
        self.download_thread.finished_signal.connect(self.on_download_finished)
        self.download_thread.start()

    def set_ui_enabled(self, enabled):
        """Włącza/wyłącza elementy UI"""
        self.url_input.setEnabled(enabled)
        self.type_mp4.setEnabled(enabled)
        self.type_mp3.setEnabled(enabled)
        self.browse_button.setEnabled(enabled)
        self.download_button.setEnabled(enabled)
        self.clear_button.setEnabled(enabled)
        self.download_button.setText(
            "Pobieranie..." if not enabled else "Rozpocznij pobieranie"
        )

    def on_download_finished(self, success, error_msg):
        """Obsługa zakończenia pobierania"""
        self.set_ui_enabled(True)
        self.progress_bar.setValue(100)

        if success:
            self.log_message("Pobieranie zakończone pomyślnie!")
            QMessageBox.information(
                self,
                "Sukces",
                "Pobieranie zakończone pomyślnie!"
            )
        else:
            self.log_message(f"Błąd pobierania: {error_msg}")
            QMessageBox.critical(
                self,
                "Błąd",
                f"Pobieranie nie powiodło się:\n{error_msg}"
            )


if __name__ == "__main__":
    import time

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Ustaw ikonę aplikacji (wymaga pliku icon.png)
    if os.path.exists("icon.png"):
        app.setWindowIcon(QIcon("icon.png"))

    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec())