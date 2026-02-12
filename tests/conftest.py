import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# Dodaj katalog glowny projektu do sys.path, aby pytest widzial modul 'app'
# Dodaj katalog glowny projektu do sys.path, aby pytest widzial modul 'app'
root_path = str(Path(__file__).parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)


# fixture dla tymczasowego katalogu
@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# fixture dla mockowanej sciezki ffmpeg
@pytest.fixture
def mock_ffmpeg_path(tmp_path: Path) -> str:
    fake_ffmpeg = tmp_path / "ffmpeg.exe"
    fake_ffmpeg.touch()
    return str(fake_ffmpeg)


# fixture z przykladowymi url youtube
@pytest.fixture
def sample_urls() -> dict[str, str]:
    return {
        "standard": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "short": "https://youtu.be/dQw4w9WgXcQ",
        "embed": "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "v_format": "https://www.youtube.com/v/dQw4w9WgXcQ",
        "with_params": "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s",
        "invalid": "https://example.com/video",
        "playlist": "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
    }


# fixture z przykladowymi danymi video info z yt-dlp
@pytest.fixture
def sample_video_info() -> dict:
    return {
        "id": "dQw4w9WgXcQ",
        "title": "Test Video",
        "duration": 212,
        "formats": [
            {
                "format_id": "18",
                "ext": "mp4",
                "height": 360,
                "fps": 30,
                "vcodec": "avc1",
                "acodec": "mp4a",
            },
            {
                "format_id": "22",
                "ext": "mp4",
                "height": 720,
                "fps": 30,
                "vcodec": "avc1",
                "acodec": "mp4a",
            },
            {
                "format_id": "137",
                "ext": "mp4",
                "height": 1080,
                "fps": 30,
                "vcodec": "avc1",
                "acodec": "none",
            },
            {
                "format_id": "140",
                "ext": "m4a",
                "vcodec": "none",
                "acodec": "mp4a",
            },
        ],
    }


# fixtures dla testow integracyjnych


# fixture z url do krotkiego testowego wideo youtube (~10s)
# uzywamy oficjalnego testowego wideo youtube
@pytest.fixture
def test_video_url() -> str:
    # 10-sekundowe wideo testowe od youtube
    return "https://www.youtube.com/watch?v=jNQXAC9IVRw"


# fixture z url do malej testowej playlisty (kilka elementow)
@pytest.fixture
def test_playlist_url() -> str:
    # mala publiczna playlista testowa
    return "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"


# fixture przygotowujace srodowisko dla testow integracyjnych
@pytest.fixture
def setup_integration_env(tmp_path: Path) -> dict:
    output_dir = tmp_path / "downloads"
    output_dir.mkdir(parents=True, exist_ok=True)

    return {
        "output_dir": output_dir,
    }
