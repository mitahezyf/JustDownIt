# ui_playlist.py
import requests
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ui.theme import apply_dark_theme


def fmt_duration(seconds: int | None) -> str:
    if seconds is None:
        return "—"
    try:
        seconds = int(seconds)
    except Exception:
        return "—"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"


class PlaylistView(QWidget):
    """
    Widok playlisty:
      - górny panel: ← Wróć, zaznacz/odznacz wszystkie, globalna jakość (w tym „Tylko audio”), Pobierz zaznaczone
      - tabela: #, Miniaturka, Tytuł, Czas, Jakość (per-wideo), Pobierz?
    """

    back_requested = pyqtSignal()  # sygnał do powrotu

    def __init__(self):
        super().__init__()
        self.entries = []  # [{'id','url','title'}]
        apply_dark_theme(self)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Pasek tytuł + przyciski
        title = QLabel("Playlista – wybierz filmy do pobrania")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color:#61afef;")

        self.btn_back = QPushButton("← Wróć")
        self.btn_back.clicked.connect(self.back_requested.emit)

        bar = QHBoxLayout()
        bar.addWidget(self.btn_back)
        bar.addSpacing(8)
        bar.addWidget(title)
        bar.addStretch()
        layout.addLayout(bar)

        # Panel globalny
        top = QHBoxLayout()
        self.btn_select_all = QPushButton("Zaznacz wszystkie")
        self.btn_unselect_all = QPushButton("Odznacz wszystkie")
        self.global_quality = QComboBox()
        # Zawsze dostępne: Auto + Tylko audio (MP3)
        self.global_quality.addItem("Auto", userData=None)
        self.global_quality.addItem("Tylko audio (MP3)", userData="bestaudio")
        self.btn_download = QPushButton("Pobierz zaznaczone")
        top.addWidget(self.btn_select_all)
        top.addWidget(self.btn_unselect_all)
        top.addWidget(QLabel("Jakość dla wszystkich:"))
        top.addWidget(self.global_quality)
        top.addStretch()
        top.addWidget(self.btn_download)
        layout.addLayout(top)

        # Tabela
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["#", "Miniaturka", "Tytuł", "Czas", "Jakość", "Pobierz?"]
        )
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # Akcje panelu globalnego
        self.btn_select_all.clicked.connect(self.select_all)
        self.btn_unselect_all.clicked.connect(self.unselect_all)
        self.global_quality.currentIndexChanged.connect(self.apply_global_quality)

    # ---------- API wywoływane z ui_mainwindow ----------

    def reset_and_fill(self, entries: list[dict]):
        """Czyści tabelę i wstawia gołe wiersze (Auto + Audio w comboboxie)."""
        self.entries = entries
        self.table.setRowCount(0)
        for i, e in enumerate(entries):
            self.table.insertRow(i)
            # #
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))

            # miniaturka (placeholder)
            thumb = QLabel("—")
            thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(i, 1, thumb)

            # tytuł
            self.table.setItem(i, 2, QTableWidgetItem(e.get("title") or "—"))

            # czas
            self.table.setItem(i, 3, QTableWidgetItem("—"))

            # jakość (na start: Auto + Audio)
            q = QComboBox()
            q.addItem("Auto", userData=None)
            q.addItem("Tylko audio (MP3)", userData="bestaudio")
            self.table.setCellWidget(i, 4, q)

            # checkbox
            chk = QCheckBox()
            chk.setChecked(True)
            chk.setStyleSheet("margin-left:20px;")
            self.table.setCellWidget(i, 5, chk)

    def update_row(
        self,
        row: int,
        *,
        thumb_url: str | None,
        duration: int | None,
        formats: list[tuple[str, str]],
    ):
        """Uzupełnia pojedynczy wiersz (miniaturka, czas, formaty)."""
        if row < 0 or row >= self.table.rowCount():
            return

        # miniaturka
        if thumb_url:
            try:
                r = requests.get(thumb_url, timeout=5)
                p = QPixmap()
                p.loadFromData(r.content)
                if not p.isNull():
                    p = p.scaled(
                        120,
                        68,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    lbl = QLabel()
                    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl.setPixmap(p)
                    self.table.setCellWidget(row, 1, lbl)
            except Exception:
                pass

        # czas
        self.table.setItem(row, 3, QTableWidgetItem(fmt_duration(duration)))

        # jakość – Auto + Audio + konkretne opcje
        combo: QComboBox = self.table.cellWidget(row, 4)  # type: ignore
        if combo:
            current_ud = combo.currentData()
            combo.clear()
            combo.addItem("Auto", userData=None)
            combo.addItem("Tylko audio (MP3)", userData="bestaudio")
            for fmt_id, label in formats:
                combo.addItem(label, userData=fmt_id)
            # spróbuj zachować poprzedni wybór
            if current_ud is not None:
                idx = combo.findData(current_ud)
                if idx >= 0:
                    combo.setCurrentIndex(idx)

        # uzupełnij globalny combobox o nowe etykiety (unikalne po labelu)
        self._sync_global_quality(formats)

    # ---------- Akcje lokalne / globalne ----------

    def select_all(self):
        for r in range(self.table.rowCount()):
            chk = self.table.cellWidget(r, 5)
            if chk:
                chk.setChecked(True)

    def unselect_all(self):
        for r in range(self.table.rowCount()):
            chk = self.table.cellWidget(r, 5)
            if chk:
                chk.setChecked(False)

    def apply_global_quality(self):
        """Ustaw wybraną jakość wszystkim wierszom."""
        ud = self.global_quality.currentData()
        txt = self.global_quality.currentText()
        for r in range(self.table.rowCount()):
            combo = self.table.cellWidget(r, 4)
            if not combo:
                continue
            combo: QComboBox
            if ud is None:
                combo.setCurrentIndex(0)  # Auto
            else:
                i = combo.findData(ud)
                if i < 0:
                    i = combo.findText(txt)
                if i >= 0:
                    combo.setCurrentIndex(i)

    def _sync_global_quality(self, formats: list[tuple[str, str]]):
        """Dorzuca brakujące opcje do globalnego comboboxa (unikalne po labelu)."""
        have = {
            self.global_quality.itemText(i) for i in range(self.global_quality.count())
        }
        # Audio jest już domyślnie – dokładamy tylko nowe etykiety wideo
        for _, label in formats:
            if label not in have:
                self.global_quality.addItem(label)
