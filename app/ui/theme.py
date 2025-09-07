# theme.py
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette


def apply_dark_theme(app_or_window):
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

    app_or_window.setPalette(dark_palette)
    app_or_window.setStyleSheet(
        """
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
    """
    )
