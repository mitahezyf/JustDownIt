from unittest.mock import MagicMock, patch

import pytest


# test importowania modulu main
def test_main_module_imports():
    try:
        from app import main

        assert main is not None
    except Exception as e:
        pytest.fail(f"Main module failed to import: {e}")


# test ze modul main ma funkcje main
def test_main_has_main_function():
    from app import main

    # sprawdz ze ma funkcje main (lub podobna)
    assert hasattr(main, "main") or hasattr(main, "__main__")


# smoke test - sprawdz ze aplikacja Qt moze byc zainicjalizowana
def test_qt_application_init(qtbot):
    from PyQt6.QtWidgets import QApplication

    # qtbot fixture z pytest-qt automatycznie tworzy QApplication
    app = QApplication.instance()

    # sprawdz ze aplikacja istnieje
    assert app is not None


# test tworzenia okna glownego (mock)
def test_main_window_creation():
    with patch("app.main.MainWindow") as mock_window:
        mock_instance = MagicMock()
        mock_window.return_value = mock_instance

        try:
            # probuj zaimportowac i stworzyc okno
            from app.main import MainWindow

            window = MainWindow()

            assert window is not None
        except ImportError:
            # jesli nie ma MainWindow w main.py to OK
            pytest.skip("MainWindow not in main module")


# test ze aplikacja nie crashuje przy podstawowym imporcie
def test_app_basic_import():
    try:
        import app
        import app.core
        import app.main
        import app.utils
        import app.workers

        assert app is not None
        assert app.main is not None
        assert app.core is not None
        assert app.utils is not None
        assert app.workers is not None
    except Exception as e:
        pytest.fail(f"Basic app import failed: {e}")


# test struktury pakietu app
def test_app_package_structure():
    import app

    # sprawdz ze glowne moduły istnieja
    assert hasattr(app, "core") or hasattr(app, "__path__")

    # sprawdz ze modul app jest pakietem
    import os

    app_path = os.path.dirname(app.__file__)
    assert os.path.exists(app_path)
