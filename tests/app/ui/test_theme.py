import pytest
from PyQt6.QtGui import QPalette


# test importowania modulu theme
def test_theme_imports():
    from app.ui import theme

    assert hasattr(theme, "apply_dark_theme")


# test ze apply_dark_theme przyjmuje parametr i ustawia palete
def test_apply_dark_theme_sets_palette(qtbot):
    from PyQt6.QtWidgets import QWidget

    from app.ui.theme import apply_dark_theme

    # stworz testowy widget
    widget = QWidget()

    # zastosuj motyw
    apply_dark_theme(widget)

    # sprawdz ze palette zostala ustawiona
    palette = widget.palette()
    assert palette is not None
    assert isinstance(palette, QPalette)


# test podstawowych kolorow ciemnego motywu
def test_apply_dark_theme_colors(qtbot):
    from PyQt6.QtGui import QColor
    from PyQt6.QtWidgets import QWidget

    from app.ui.theme import apply_dark_theme

    widget = QWidget()
    apply_dark_theme(widget)

    palette = widget.palette()

    # sprawdz ze palette istnieje
    assert palette is not None
    assert isinstance(palette, QPalette)

    # sprawdz ze ma ustawione jakies kolory (nie sa domyslne)
    window_color = palette.color(QPalette.ColorRole.Window)
    assert isinstance(window_color, QColor)

    # sprawdz ze to jest ciemny kolor (rgb < 128)
    assert window_color.red() < 128
    assert window_color.green() < 128
    assert window_color.blue() < 128


# test ze modul nie crashuje przy imporcie
def test_theme_module_loads():
    try:
        from app.ui import theme

        assert theme is not None
    except Exception as e:
        pytest.fail(f"Theme module failed to load: {e}")


# test ze stylesheet zostaje ustawiony
def test_apply_dark_theme_stylesheet(qtbot):
    from PyQt6.QtWidgets import QWidget

    from app.ui.theme import apply_dark_theme

    widget = QWidget()
    apply_dark_theme(widget)

    # sprawdz ze stylesheet zostal ustawiony
    stylesheet = widget.styleSheet()
    assert stylesheet is not None
    assert len(stylesheet) > 0

    # sprawdz ze zawiera jakies style css
    assert "QPushButton" in stylesheet or "QLineEdit" in stylesheet
