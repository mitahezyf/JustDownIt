import pytest

from app.utils.errors import CancelledError, DependencyMissingError


# test tworzenia wyjatku DependencyMissingError
def test_dependency_missing_error_creation():
    error = DependencyMissingError("Test message")
    assert isinstance(error, Exception)
    assert str(error) == "Test message"


# test rzucania i lapania DependencyMissingError
def test_dependency_missing_error_raise():
    with pytest.raises(DependencyMissingError) as exc_info:
        raise DependencyMissingError("Missing dependency")
    assert "Missing dependency" in str(exc_info.value)


# test tworzenia wyjatku CancelledError
def test_cancelled_error_creation():
    error = CancelledError("Cancelled by user")
    assert isinstance(error, Exception)
    assert str(error) == "Cancelled by user"


# test rzucania i lapania CancelledError
def test_cancelled_error_raise():
    with pytest.raises(CancelledError) as exc_info:
        raise CancelledError("Operation cancelled")
    assert "Operation cancelled" in str(exc_info.value)


# test pustego komunikatu
def test_errors_empty_message():
    error1 = DependencyMissingError()
    error2 = CancelledError()
    assert isinstance(error1, Exception)
    assert isinstance(error2, Exception)


# test dziedziczenia po Exception
def test_errors_inheritance():
    assert issubclass(DependencyMissingError, Exception)
    assert issubclass(CancelledError, Exception)


# test rozrozniania bledow
def test_errors_are_different():
    try:
        raise DependencyMissingError("test")
    except CancelledError:
        pytest.fail("Should not catch CancelledError")
    except DependencyMissingError:
        pass  # oczekiwane


# test Context managera z bledami
def test_errors_in_context():
    with pytest.raises(DependencyMissingError):
        with pytest.raises(CancelledError):
            # to nie powinno sie wykonac
            raise DependencyMissingError("outer")
        raise CancelledError("inner")
