import re
from pathlib import Path

# wzorce do czyszczenia nazw plikow
_ILLEGAL = r'[<>:"/\\|?*\x00-\x1F]'  # niedozwolone znaki w systemie plikow
_WS = r"\s+"  # ciag spacji i bialych znakow


# zwraca bezpieczna nazwe pliku pozbawiona niedozwolonych znakow
def safe_filename(name: str, max_len: int = 180) -> str:

    # zamienia znaki nielegalne na spacje
    n = re.sub(_ILLEGAL, " ", name)
    # zamienia wiele spacji na jedna i usuwa kropki oraz spacje z poczatku i konca
    n = re.sub(_WS, " ", n).strip(". ").strip()
    # jesli nazwa jest za dluga to skraca do maksymalnej dlugosci
    if len(n) > max_len:
        n = n[:max_len].rsplit(" ", 1)[0].rstrip(". ")
    # jesli po czyszczeniu nic nie zostalo to zwraca "untitled"
    return n or "untitled"


# laczy katalog z nazwa pliku i rozszerzeniem, tworzac pelna sciezke
def with_dir(dirpath: str | Path, basename: str, ext: str) -> Path:
    p = Path(dirpath).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p / f"{safe_filename(basename)}.{ext.lstrip('.')}"
