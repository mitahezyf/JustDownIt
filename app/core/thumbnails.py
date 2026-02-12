from __future__ import annotations

from typing import Callable, Optional

import requests

from app.utils.url import extract_video_id


# zwraca url miniatury dla podanego linku do wideo
def get_thumbnail_url(
    video_url: str, timeout: float = 3.0, log: Optional[Callable] = None
) -> Optional[str]:

    # probuje wyciagnac id filmu z url
    vid = extract_video_id(video_url)
    if not vid:
        return None

    # wewnetrzna funkcja do logowania komunikatow
    def _log(msg: str):
        if log:
            log(msg)

    # najpierw sprawdza czy istnieje miniatura w najwyzszej rozdzielczosci
    maxres = f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg"
    try:
        r = requests.head(maxres, timeout=timeout)
        if r.status_code == 200:
            return maxres
    except Exception as e:
        # jesli nie udalo sie sprawdzic to zapisuje komunikat
        _log(f"HEAD maxres błąd: {e}")

    # jesli nie ma maxres to zwraca standardowa miniature hq
    return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
