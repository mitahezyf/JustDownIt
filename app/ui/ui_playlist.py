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


# formatuje czas trwania w sekundach do postaci mm:ss lub hh:mm:ss
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


# widok playlisty: tabela elementow + akcje globalne
class PlaylistView(QWidget):

    back_requested = pyqtSignal()  # sygnal do powrotu do ekranu glownego

    def __init__(self):
        super().__init__()
        self.entries = []  # lista elementow playlisty: {'id','url','title'}
        apply_dark_theme(self)  # stosuje ciemny motyw
        self._build()  # buduje interfejs

    # tworzy uklad widoku, pasek tytulu, panel globalny i tabele
    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # pasek tytulu z przyciskiem powrotu
        title = QLabel("Playlista – wybierz filmy do pobrania")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color:#61afef;")

        self.btn_back = QPushButton("Wróć")
        self.btn_back.clicked.connect(self.back_requested.emit)

        bar = QHBoxLayout()
        bar.addWidget(self.btn_back)
        bar.addSpacing(8)
        bar.addWidget(title)
        bar.addStretch()
        layout.addLayout(bar)

        # panel globalny: zaznaczanie, jakosc dla wszystkich, start pobierania
        top = QHBoxLayout()
        self.btn_select_all = QPushButton("Zaznacz wszystkie")
        self.btn_unselect_all = QPushButton("Odznacz wszystkie")
        self.global_quality = QComboBox()
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

        # tabela elementow playlisty
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

        # podpina akcje globalne do przyciskow i comboboxa
        self.btn_select_all.clicked.connect(self.select_all)
        self.btn_unselect_all.clicked.connect(self.unselect_all)
        self.global_quality.currentIndexChanged.connect(self.apply_global_quality)

    # api wywolywane z ui_mainwindow

    # resetuje tabele i wypelnia wiersze nowymi elementami playlisty
    def reset_and_fill(self, entries: list[dict]):
        self.entries = entries
        self.table.setRowCount(0)
        for i, e in enumerate(entries):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))

            # placeholder miniaturki do czasu az przyjdzie prawdziwa
            thumb = QLabel("—")
            thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(i, 1, thumb)

            # tytul i czas trwania
            self.table.setItem(i, 2, QTableWidgetItem(e.get("title") or "—"))
            self.table.setItem(i, 3, QTableWidgetItem("—"))

            # wybor jakosci dla pojedynczego elementu
            q = QComboBox()
            q.addItem("Auto", userData=None)
            q.addItem("Tylko audio (MP3)", userData="bestaudio")
            self.table.setCellWidget(i, 4, q)

            # checkbox do wyboru czy pobierac
            chk = QCheckBox()
            chk.setChecked(True)
            chk.setStyleSheet("margin-left:20px;")
            self.table.setCellWidget(i, 5, chk)

    # aktualizuje pojedynczy wiersz danymi: miniaturka, czas, formaty
    def update_row(
        self,
        row: int,
        *,
        thumb_url: str | None,
        duration: int | None,
        formats: list[tuple[str, str]],
    ):
        if row < 0 or row >= self.table.rowCount():
            return

        # laduje miniaturke jesli url jest dostepny
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

        # ustawia sformatowany czas w kolumnie
        self.table.setItem(row, 3, QTableWidgetItem(fmt_duration(duration)))

        # uzupelnia combobox formatow i stara sie zachowac poprzedni wybor
        combo: QComboBox = self.table.cellWidget(row, 4)
        if combo:
            current_ud = combo.currentData()
            combo.clear()
            combo.addItem("Auto", userData=None)
            combo.addItem("Tylko audio (MP3)", userData="bestaudio")
            for fmt_id, label in formats:
                combo.addItem(label, userData=fmt_id)
            if current_ud is not None:
                idx = combo.findData(current_ud)
                if idx >= 0:
                    combo.setCurrentIndex(idx)

        # dopelnia globalny combobox o brakujace etykiety
        self._sync_global_quality(formats)

    # akcje lokalne / globalne

    # zaznacza checkbox we wszystkich wierszach
    def select_all(self):
        for r in range(self.table.rowCount()):
            chk = self.table.cellWidget(r, 5)
            if chk:
                chk.setChecked(True)

    # odznacza checkbox we wszystkich wierszach
    def unselect_all(self):
        for r in range(self.table.rowCount()):
            chk = self.table.cellWidget(r, 5)
            if chk:
                chk.setChecked(False)

    # stosuje wybor globalnej jakosci do wszystkich wierszy
    def apply_global_quality(self):
        ud = self.global_quality.currentData()
        txt = self.global_quality.currentText()
        for r in range(self.table.rowCount()):
            combo = self.table.cellWidget(r, 4)
            if not combo:
                continue
            combo: QComboBox
            if ud is None:
                combo.setCurrentIndex(0)  # auto
            else:
                i = combo.findData(ud)
                if i < 0:
                    i = combo.findText(txt)
                if i >= 0:
                    combo.setCurrentIndex(i)

    # uzgadnia opcje w globalnym comboboxie z nowo dostepnymi etykietami
    def _sync_global_quality(self, formats: list[tuple[str, str]]):
        have = {
            self.global_quality.itemText(i) for i in range(self.global_quality.count())
        }
        for _, label in formats:
            if label not in have:
                self.global_quality.addItem(label)
