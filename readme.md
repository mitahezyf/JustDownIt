# JustDownIt

![Tests](https://img.shields.io/github/actions/workflow/status/mitahezyf/JustDownIt/ci.yml?style=for-the-badge&logo=github)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge&logo=python)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

YouTube downloader z GUI w PyQt6.

## Features

- 🎥 Pobieranie wideo z YouTube (różne formaty i jakości)
- 🎵 Pobieranie audio do MP3
- 📋 Obsługa playlist
- 🎨 Ciemny interfejs użytkownika (PyQt6)
- ⚡ Wielowątkowe pobieranie
- 📊 Pasek postępu

## Instalacja

```bash
# Sklonuj repozytorium
git clone https://github.com/mitahezyf/JustDownIt.git
cd JustDownIt

# Utwórz virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# lub: source .venv/bin/activate  # Linux/Mac

# Zainstaluj zależności
pip install -r requirements.txt
```

## Użycie

```bash
# Uruchom aplikację
python -m app.main
```

## Development

### Instalacja zależności deweloperskich

```bash
pip install -r requirements-test.txt
pip install pre-commit
pre-commit install
```

### Uruchomienie testów

```bash
# Testy jednostkowe (szybkie)
pytest -m "not integration and not slow" -v

# Wszystkie testy (z integracją)
pytest -v

# Z coverage
pytest --cov=app --cov-report=html
```

### Code quality

Projekt używa pre-commit hooks:
- **black** - formatowanie kodu
- **isort** - sortowanie importów
- **ruff** - linting
- **mypy** - type checking
- **bandit** - security scanning
- **vulture** - dead code detection
- **detect-secrets** - wykrywanie sekretów

```bash
# Uruchom wszystkie hooki
pre-commit run --all-files
```

## Statystyki

- **85% pokrycia** testami (bez GUI)
- **139 testów jednostkowych** ✅
- **9 testów integracyjnych** 🌐
- **Automatyczne CI/CD** via GitHub Actions

## Technologie

- Python 3.8+
- PyQt6 - GUI
- yt-dlp - pobieranie z YouTube
- FFmpeg - przetwarzanie audio/video
- pytest - testy

## Licencja

MIT
