import pytest

from app.utils.url import extract_video_id


# test dla standardowego url youtube.com/watch?v=ID
def test_extract_video_id_standard():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"


# test dla krotkiego url youtu.be/ID
def test_extract_video_id_short():
    url = "https://youtu.be/dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"


# test dla url embed youtube.com/embed/ID
def test_extract_video_id_embed():
    url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"


# test dla starego formatu youtube.com/v/ID
def test_extract_video_id_v_format():
    url = "https://www.youtube.com/v/dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"


# test dla url z dodatkowymi parametrami
def test_extract_video_id_with_params():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s&list=PLxxx"
    assert extract_video_id(url) == "dQw4w9WgXcQ"


# test dla nieprawidlowego url (nie youtube)
def test_extract_video_id_invalid():
    url = "https://example.com/video"
    assert extract_video_id(url) is None


# test dla pustego stringa
def test_extract_video_id_empty():
    assert extract_video_id("") is None


# test dla url bez id
def test_extract_video_id_no_id():
    url = "https://www.youtube.com"
    assert extract_video_id(url) is None


# test dla url bez protokolu
def test_extract_video_id_no_protocol():
    url = "youtube.com/watch?v=ABC123"
    assert extract_video_id(url) == "ABC123"


# test parametryzowany dla wszystkich formatow
@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.youtube.com/watch?v=ABC123", "ABC123"),
        ("https://youtu.be/XYZ789", "XYZ789"),
        ("https://www.youtube.com/embed/Test123", "Test123"),
        ("https://www.youtube.com/v/Video456", "Video456"),
        ("youtube.com/watch?v=NoHTTPS", "NoHTTPS"),
        ("https://vimeo.com/123456", None),
        ("not a url", None),
    ],
)
def test_extract_video_id_parametrized(url, expected):
    assert extract_video_id(url) == expected
