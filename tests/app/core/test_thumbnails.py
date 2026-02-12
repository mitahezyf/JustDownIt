from unittest.mock import MagicMock, patch

import pytest

from app.core.thumbnails import get_thumbnail_url


# test pobierania url maxresdefault (najwyzsza jakosc)
def test_get_thumbnail_url_maxres():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    with patch("app.core.thumbnails.requests.head") as mock_head:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        result = get_thumbnail_url(url)

        assert result == "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
        mock_head.assert_called_once()


# test fallback na hqdefault gdy maxres nie istnieje
def test_get_thumbnail_url_fallback():
    url = "https://www.youtube.com/watch?v=ABC123"

    with patch("app.core.thumbnails.requests.head") as mock_head:
        mock_response = MagicMock()
        mock_response.status_code = 404  # maxres nie istnieje
        mock_head.return_value = mock_response

        result = get_thumbnail_url(url)

        assert result == "https://i.ytimg.com/vi/ABC123/hqdefault.jpg"


# test fallback przy wyjatku z requests
def test_get_thumbnail_url_exception_fallback():
    url = "https://www.youtube.com/watch?v=XYZ789"

    with patch("app.core.thumbnails.requests.head") as mock_head:
        mock_head.side_effect = Exception("Network error")

        result = get_thumbnail_url(url)

        # powinien zwrocic fallback mimo bledu
        assert result == "https://i.ytimg.com/vi/XYZ789/hqdefault.jpg"


# test None dla nieprawidlowego url (bez id)
def test_get_thumbnail_url_invalid_url():
    url = "https://example.com/video"
    result = get_thumbnail_url(url)
    assert result is None


# test None dla pustego url
def test_get_thumbnail_url_empty():
    result = get_thumbnail_url("")
    assert result is None


# test callback logowania
def test_get_thumbnail_url_with_log():
    url = "https://www.youtube.com/watch?v=TEST"
    log_messages = []

    def log_callback(msg):
        log_messages.append(msg)

    with patch("app.core.thumbnails.requests.head") as mock_head:
        mock_head.side_effect = Exception("Timeout")
        get_thumbnail_url(url, log=log_callback)

        # powinno zalogowac blad
        assert len(log_messages) > 0
        assert "błąd" in log_messages[0].lower()


# test customowego timeout
def test_get_thumbnail_url_custom_timeout():
    url = "https://www.youtube.com/watch?v=ABC"

    with patch("app.core.thumbnails.requests.head") as mock_head:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        get_thumbnail_url(url, timeout=5.0)

        # sprawdz ze timeout zostal przekazany
        mock_head.assert_called_once()
        assert mock_head.call_args[1]["timeout"] == 5.0


# test dla roznych formatow url
@pytest.mark.parametrize(
    "url,expected_id",
    [
        ("https://www.youtube.com/watch?v=ABC123", "ABC123"),
        ("https://youtu.be/XYZ789", "XYZ789"),
        ("https://www.youtube.com/embed/TEST", "TEST"),
        ("youtube.com/watch?v=NoHTTP", "NoHTTP"),
    ],
)
def test_get_thumbnail_url_various_formats(url, expected_id):
    with patch("app.core.thumbnails.requests.head") as mock_head:
        mock_response = MagicMock()
        mock_response.status_code = 404  # uzyj fallback
        mock_head.return_value = mock_response

        result = get_thumbnail_url(url)
        assert f"/{expected_id}/hqdefault.jpg" in result


# test bez logowania (None callback)
def test_get_thumbnail_url_no_log():
    url = "https://www.youtube.com/watch?v=TEST"

    with patch("app.core.thumbnails.requests.head") as mock_head:
        mock_head.side_effect = Exception("Error")
        # nie powinno crashnac gdy log=None
        result = get_thumbnail_url(url, log=None)
        assert result is not None
