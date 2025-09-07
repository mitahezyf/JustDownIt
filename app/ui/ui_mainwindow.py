# ui_mainwindow.py

import os
import time

import requests
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QTextCursor
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.threads import PlaylistFetchThread  # szybka lista (id/tytuł)
from app.core.threads import (
    PlaylistFormatsThread,  # meta per-wideo (czas/miniatura/formaty)
)
from app.core.threads import (
    DownloadThread,
    FormatFetchThread,
)
from app.core.ytdown_core import pobierz_miniaturke

# ── Twoje moduły ────────────────────────────────────────────────────────────────
from app.ui.theme import apply_dark_theme
from app.ui.ui_playlist import PlaylistView


class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.current_url = ""
        self.ffmpeg_path = ""
        self.download_type = "mp4"
        self.available_formats = []

        # tryb inteligentnego przycisku: "download" | "show_playlist"
        self._primary_mode = "download"

        # ---- Stan / cache playlisty (utrwalany między przełączaniem widoków)
        self._pl_url: str | None = None
        self._pl_entries: list | None = None
        self._pl_meta_done: bool = False
        self._pl_fetch_thread = None
        self._pl_meta_thread = None
        self._pl_fetch_running = False
        self._pl_meta_running = False

        # Stos widoków: pojedynczy film <-> playlista
        self.stack = QStackedWidget(self)
        self.page_single = QWidget()
        self.page_playlist = PlaylistView()
        self.stack.addWidget(self.page_single)
        self.stack.addWidget(self.page_playlist)

        # Zbuduj UI pojedynczego filmu na page_single
        self.setup_ui_single()
        self.setup_connections()
        self.set_default_download_folder()

        # sygnał „← Wróć” z widoku playlisty
        self.page_playlist.back_requested.connect(self.back_to_single)

        # Główny layout klasy: tylko stack
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.stack)

    # ===========================================================================
    # UI: widok pojedynczego filmu
    # ===========================================================================
    def setup_ui_single(self):
        apply_dark_theme(self)

        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        section_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        normal_font = QFont("Segoe UI", 10)

        main_layout = QVBoxLayout(self.page_single)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Nagłówek
        header = QLabel("JustDownIt by Mitahezyf")
        header.setFont(title_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #61afef; padding: 10px;")
        main_layout.addWidget(header)

        # Sekcja URL
        url_layout = QVBoxLayout()
        url_layout.setSpacing(5)

        url_label = QLabel("URL filmu / playlisty:")
        url_label.setFont(section_font)
        url_layout.addWidget(url_label)

        self.url_input = QLineEdit()
        self.url_input.setFont(normal_font)
        self.url_input.setPlaceholderText(
            "https://www.youtube.com/watch?v=...  lub  https://www.youtube.com/playlist?list=..."
        )
        url_layout.addWidget(self.url_input)

        main_layout.addLayout(url_layout)

        # ── Wiersz: po LEWEJ opcje (jakość + typ), po PRAWEJ miniaturka ─────────
        row_opts_thumb = QHBoxLayout()
        row_opts_thumb.setSpacing(15)

        # LEWA kolumna – opcje
        opts_box = QVBoxLayout()
        opts_box.setSpacing(12)

        # Jakość wideo
        quality_label = QLabel("Jakość wideo:")
        quality_label.setFont(section_font)
        self.quality_combo = QComboBox()
        self.quality_combo.setFont(normal_font)
        self.quality_combo.addItem("Brak (brak URL)")
        self.quality_combo.setEnabled(False)
        self.quality_combo.setMaximumWidth(240)

        opts_box.addWidget(quality_label)
        opts_box.addWidget(self.quality_combo)

        # Typ pobierania
        type_label = QLabel("Typ pobierania:")
        type_label.setFont(section_font)
        type_buttons = QHBoxLayout()
        self.type_mp4 = QRadioButton("MP4 (wideo)")
        self.type_mp4.setFont(normal_font)
        self.type_mp4.setChecked(True)
        self.type_mp3 = QRadioButton("MP3 (audio)")
        self.type_mp3.setFont(normal_font)
        type_buttons.addWidget(self.type_mp4)
        type_buttons.addWidget(self.type_mp3)
        type_buttons.addStretch()

        opts_box.addWidget(type_label)
        opts_box.addLayout(type_buttons)
        opts_box.addStretch()

        row_opts_thumb.addLayout(opts_box, stretch=1)

        # PRAWA kolumna – miniaturka
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(320, 180)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet(
            """
            background-color: #2b2f3a;
            border: 1px solid #3d4351;
            border-radius: 4px;
        """
        )
        self.thumbnail_label.setText("Miniaturka pojawi się tutaj po podaniu URL")
        row_opts_thumb.addWidget(
            self.thumbnail_label, alignment=Qt.AlignmentFlag.AlignRight
        )

        main_layout.addLayout(row_opts_thumb)
        #  ────────────────────────────────────────────────────────────────────────

        # Folder docelowy
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

        # Pasek postępu i przyciski
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

        # Przycisk powrotu z widoku playlisty (opcjonalny – zostawiony)
        self.back_button = QPushButton("← Wróć do pojedynczego")
        self.back_button.setVisible(False)
        buttons_layout.addWidget(self.back_button)

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

        main_layout.addLayout(log_layout, 1)

    # ===========================================================================
    # Połączenia sygnałów
    # ===========================================================================
    def setup_connections(self):
        self.type_mp4.toggled.connect(lambda: self.set_download_type("mp4"))
        self.type_mp3.toggled.connect(lambda: self.set_download_type("mp3"))
        self.browse_button.clicked.connect(self.browse_folder)
        self.download_button.clicked.connect(
            self.on_primary_button_clicked
        )  # << inteligentny przycisk
        self.cancel_button.clicked.connect(self.cancel_download)
        self.clear_button.clicked.connect(self.clear_logs)
        self.url_input.textChanged.connect(self.on_url_changed)
        self.back_button.clicked.connect(self.back_to_single)

        # globalne przyciski z PlaylistView → logika
        self.page_playlist.btn_select_all.clicked.connect(self._playlist_select_all)
        self.page_playlist.btn_unselect_all.clicked.connect(self._playlist_unselect_all)
        self.page_playlist.btn_download.clicked.connect(
            self._playlist_download_selected
        )

    # ===========================================================================
    # Logika pojedynczego widoku
    # ===========================================================================
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

    def _set_primary_mode(self, mode: str):
        """Aktualizuje tryb i etykietę głównego przycisku."""
        if mode == self._primary_mode:
            return
        self._primary_mode = mode
        if mode == "show_playlist":
            self.download_button.setText("Wyświetl playlistę")
        else:
            self.download_button.setText("Rozpocznij pobieranie")

    def on_url_changed(self, url_text: str):
        new_url = url_text.strip()
        url_changed = new_url != self.current_url
        self.current_url = new_url

        # Playlist czy pojedynczy film?
        is_playlist = "list=" in self.current_url
        self._set_primary_mode("show_playlist" if is_playlist else "download")

        # Jeżeli zmieniłeś URL na inną playlistę/film – wyczyść cache playlisty
        if (
            url_changed
            and (self._pl_url is not None)
            and (self._pl_url != self.current_url)
        ):
            self._invalidate_playlist_cache()

        # Reset combobox dla pojedynczego filmu
        self.available_formats = []
        self.quality_combo.clear()

        if ("youtube.com/watch?v=" in self.current_url) or (
            "youtu.be/" in self.current_url
        ):
            # pojedynczy film → pobierz miniaturę + formaty
            self.quality_combo.addItem("Ładowanie formatów…")
            self.quality_combo.setEnabled(False)
            self.fetch_thumbnail(self.current_url)
            self.fetch_thread = FormatFetchThread(self.current_url)
            self.fetch_thread.formats_ready.connect(self.on_formats_ready)
            self.fetch_thread.error.connect(self.on_formats_error)
            self.fetch_thread.start()
        elif is_playlist:
            # playlisty nie mają jednego 'formatu' – wyłącz wybór jakości na tej karcie
            self.thumbnail_label.setText(
                "To jest playlista – wybierz formaty w widoku playlisty"
            )
            self.thumbnail_label.setPixmap(QPixmap())
            self.quality_combo.addItem("Niedostępne dla playlisty")
            self.quality_combo.setEnabled(False)
        else:
            self.thumbnail_label.setText("Miniaturka pojawi się tutaj po podaniu URL")
            self.thumbnail_label.setPixmap(QPixmap())
            self.quality_combo.addItem("Brak (brak URL)")
            self.quality_combo.setEnabled(False)

    def on_formats_ready(self, formats_list):
        self.available_formats = formats_list
        self.quality_combo.clear()
        for fmt_id, label in formats_list:
            self.quality_combo.addItem(label, userData=fmt_id)
        self.quality_combo.setEnabled(True)
        self.quality_combo.setCurrentIndex(0)
        self.log_message("Formaty pobrane pomyślnie.")

    def on_formats_error(self, err_msg):
        self.log_message(f"Błąd pobierania formatów: {err_msg}")
        self.quality_combo.clear()
        self.quality_combo.addItem("Brak (błąd pobierania)")
        self.quality_combo.setEnabled(False)

    def fetch_thumbnail(self, url: str):
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
                        320,
                        180,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
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
        timestamp = time.strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        self.log_output.append(formatted_msg)
        self.log_output.moveCursor(QTextCursor.MoveOperation.End)

    def set_download_type(self, download_type: str):
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

    def cancel_download(self):
        if hasattr(self, "download_thread") and self.download_thread.isRunning():
            self.download_thread.cancel()
            self.log_message("Wysyłanie żądania anulowania…")
            self.cancel_button.setEnabled(False)

    # Inteligentny przycisk
    def on_primary_button_clicked(self):
        if self._primary_mode == "show_playlist":
            self.show_playlist_view()
        else:
            self.start_download()

    def start_download(self):
        url = self.url_input.text().strip()
        folder = self.folder_input.text().strip()

        if not url:
            QMessageBox.warning(self, "Błąd", "Wprowadź URL filmu YouTube")
            return
        if "list=" in url:
            # to playlista – w tym widoku nie uruchamiamy pobierania
            self.show_playlist_view()
            return
        if not os.path.isdir(folder):
            QMessageBox.warning(self, "Błąd", "Folder docelowy nie istnieje")
            return
        if "youtube.com" not in url and "youtu.be" not in url:
            QMessageBox.warning(self, "Błąd", "Nieprawidłowy URL YouTube")
            return

        if not self.ffmpeg_path or not os.path.exists(self.ffmpeg_path):
            QMessageBox.warning(
                self,
                "Uwaga",
                "FFmpeg nie zostało odnalezione. Łączenie (jeśli video-only) może się nie powieść. "
                "Zainstaluj ffmpeg lub `pip install imageio-ffmpeg`.",
            )
            self.log_message("Ostrzeżenie: FFmpeg nie odnalezione.")

        if self.download_type == "mp4":
            if not (
                self.quality_combo.isEnabled()
                and self.quality_combo.currentIndex() >= 0
            ):
                QMessageBox.warning(
                    self, "Błąd", "Brak dostępnych formatów do pobrania"
                )
                return
            format_id = self.quality_combo.currentData()
        else:
            format_id = None

        self.set_ui_enabled(False)
        self.log_message(f"Rozpoczynanie pobierania ({self.download_type})…")
        self.progress_bar.setValue(0)

        self.download_thread = DownloadThread(
            url,
            self.ffmpeg_path,
            folder,
            self.download_type,
            format_id,
            self.log_message,
        )
        self.download_thread.log_signal.connect(self.log_message)
        self.download_thread.progress_signal.connect(
            lambda percent: self.update_progress(percent)
        )
        self.download_thread.finished_signal.connect(self.on_download_finished)
        self.download_thread.start()

    def update_progress(self, value: float):
        progress_value = int(min(max(value, 0), 100))
        self.progress_bar.setValue(progress_value)
        self.download_button.setText(
            f"Pobieranie… {progress_value}%"
            if 0 < progress_value < 100
            else (
                "Wyświetl playlistę"
                if self._primary_mode == "show_playlist"
                else "Rozpocznij pobieranie"
            )
        )

    def set_ui_enabled(self, enabled: bool):
        self.url_input.setEnabled(enabled)
        self.type_mp4.setEnabled(enabled)
        self.type_mp3.setEnabled(enabled)
        self.quality_combo.setEnabled(enabled and self.quality_combo.count() > 0)
        self.browse_button.setEnabled(enabled)
        self.download_button.setEnabled(enabled)
        self.clear_button.setEnabled(enabled)
        self.cancel_button.setEnabled(not enabled)
        self.download_button.setText(
            "Pobieranie…"
            if not enabled
            else (
                "Wyświetl playlistę"
                if self._primary_mode == "show_playlist"
                else "Rozpocznij pobieranie"
            )
        )

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
                QMessageBox.critical(
                    self, "Błąd", f"Pobieranie nie powiodło się:\n{error_msg}"
                )

    def set_ffmpeg_path(self, path: str):
        self.ffmpeg_path = path

    # ===========================================================================
    # Widok playlisty: przełączanie i akcje
    # ===========================================================================
    def show_playlist_view(self):
        """Pokaż widok playlisty. Jeśli jest w cache lub wątki działają – NIE resetuj."""
        url = self.current_url.strip()
        if not url or "list=" not in url:
            QMessageBox.warning(
                self, "Brak playlisty", "Ten URL nie wygląda na playlistę."
            )
            return

        # Jeżeli już mamy wczytaną tę samą playlistę – po prostu pokaż
        if self._pl_url == url and self._pl_entries:
            self.stack.setCurrentWidget(self.page_playlist)
            self.back_button.setVisible(True)
            self.log_message("Pokazano playlistę (z cache).")
            return

        # Jeśli to nowa playlista – zainicjuj cache i uruchom fetch (tylko raz)
        if not self._pl_fetch_running:
            self._pl_url = url
            self._pl_entries = None
            self._pl_meta_done = False

            self.log_message("Ładuję listę filmów z playlisty…")

            self._pl_fetch_thread = PlaylistFetchThread(url)
            self._pl_fetch_thread.result.connect(self._on_playlist_list_ready)
            self._pl_fetch_thread.error.connect(self._on_playlist_error)
            self._pl_fetch_thread.finished.connect(
                lambda: setattr(self, "_pl_fetch_running", False)
            )
            self._pl_fetch_running = True
            self._pl_fetch_thread.start()

        # Pokaż widok od razu (lista się wypełni, kiedy fetch zwróci)
        self.stack.setCurrentWidget(self.page_playlist)
        self.back_button.setVisible(True)

    def _on_playlist_list_ready(self, entries: list):
        """Mamy płaską listę (id/tytuł/url). Wypełniamy TYLKO gdy to nadal ta sama playlista."""
        # Jeśli w międzyczasie użytkownik zmienił URL na inną playlistę – zignoruj wynik.
        if self._pl_url != self.current_url or "list=" not in self.current_url:
            self.log_message("Odrzucono wynik – URL playlisty się zmienił.")
            return

        if not entries:
            QMessageBox.information(
                self, "Pusta playlista", "Nie znaleziono elementów."
            )
            return

        # Jeśli już mamy entries (np. wracasz do widoku) – nie resetuj tabeli.
        if not self._pl_entries:
            self._pl_entries = entries
            self.page_playlist.reset_and_fill(entries)
            self.log_message(f"Załadowano pozycje: {len(entries)}")

        # Uruchom dociąganie metadanych tylko raz dla danej playlisty
        if not self._pl_meta_running and not self._pl_meta_done:
            self._pl_meta_thread = PlaylistFormatsThread(entries)
            self._pl_meta_thread.row_ready.connect(
                lambda row, thumb, dur, formats: self.page_playlist.update_row(
                    row, thumb_url=thumb, duration=dur, formats=formats
                )
            )
            self._pl_meta_thread.error.connect(
                lambda e: self.log_message(f"Błąd metadanych playlisty: {e}")
            )
            self._pl_meta_thread.finished.connect(self._on_playlist_meta_finished)
            self._pl_meta_running = True
            self._pl_meta_thread.start()

    def _on_playlist_meta_finished(self):
        self._pl_meta_running = False
        self._pl_meta_done = True
        self.log_message("Metadane playlisty wczytane.")

    def _on_playlist_error(self, err: str):
        self._pl_fetch_running = False
        self.log_message(f"Błąd playlisty: {err}")
        QMessageBox.critical(self, "Błąd playlisty", err)

    def back_to_single(self):
        """Tylko przełącza widok. Wątki playlisty dalej działają, stan zostaje."""
        self.stack.setCurrentWidget(self.page_single)
        self.back_button.setVisible(False)
        # etykieta przycisku zostaje zgodna z URL (show/download)

    def _invalidate_playlist_cache(self):
        """Czyści cache playlisty po zmianie URL na inną playlistę/film."""
        self._pl_url = None
        self._pl_entries = None
        self._pl_meta_done = False
        # nie zabijamy działających wątków – jak dobiegną końca, wynik i tak zostanie zignorowany

    # Akcje globalne z górnego panelu PlaylistView
    def _playlist_select_all(self):
        tbl = self.page_playlist.table
        for row in range(tbl.rowCount()):
            chk = tbl.cellWidget(row, 5)
            if chk:
                chk.setChecked(True)

    def _playlist_unselect_all(self):
        tbl = self.page_playlist.table
        for row in range(tbl.rowCount()):
            chk = tbl.cellWidget(row, 5)
            if chk:
                chk.setChecked(False)

    def _playlist_download_selected(self):
        """Zaczytaj zaznaczone wiersze i uruchom pobieranie po kolei."""
        tbl = self.page_playlist.table
        folder = self.folder_input.text().strip()

        if not os.path.isdir(folder):
            QMessageBox.warning(self, "Błąd", "Folder docelowy nie istnieje")
            return
        entries = self._pl_entries or getattr(self.page_playlist, "entries", [])
        if not entries:
            QMessageBox.information(
                self, "Brak danych", "Playlista nie została jeszcze wczytana."
            )
            return

        to_download = []
        for row in range(tbl.rowCount()):
            chk = tbl.cellWidget(row, 5)
            if not (chk and chk.isChecked()):
                continue

            url_item = entries[row]["url"] if row < len(entries) else None
            if not url_item:
                continue

            fmt_combo = tbl.cellWidget(row, 4)
            fmt_id = fmt_combo.currentData() if fmt_combo else None
            if fmt_id is None:
                fmt_id = "best"

            # typ wynikowy: jeśli wybrano „bestaudio”, pobieramy MP3
            dtype = "mp4"
            if fmt_id == "bestaudio":
                dtype = "mp3"

            to_download.append((url_item, fmt_id, dtype))

        if not to_download:
            QMessageBox.information(
                self, "Brak wyboru", "Zaznacz elementy do pobrania."
            )
            return

        self.log_message(f"Start pobierania {len(to_download)} pozycji…")
        for idx, (url, fmt_id, dtype) in enumerate(to_download, 1):
            self.log_message(f"[{idx}/{len(to_download)}] {url}")
            self.set_ui_enabled(False)
            self.progress_bar.setValue(0)
            self.download_thread = DownloadThread(
                url, self.ffmpeg_path, folder, dtype, fmt_id, self.log_message
            )
            self.download_thread.log_signal.connect(self.log_message)
            self.download_thread.progress_signal.connect(
                lambda p: self.update_progress(p)
            )
            self.download_thread.finished_signal.connect(self.on_download_finished)
            self.download_thread.start()
