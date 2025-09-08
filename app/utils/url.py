import re
from typing import Optional

# wzorce do wyciagania id filmu z roznych typow linkow youtube
_PATTERNS = [
    r"youtube\.com/watch\?v=([^&]+)",  # standardowy link
    r"youtu\.be/([^?]+)",  # krotki link
    r"youtube\.com/embed/([^/]+)",  # link wbudowany
    r"youtube\.com/v/([^?]+)",  # starszy format linku
]


# probuje wyciagnac id filmu z podanego url
def extract_video_id(url: str) -> Optional[str]:
    for p in _PATTERNS:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None
