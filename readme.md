# JustDownIt: Narzędzie do pobierania mediów z YouTube oparte na PyQt6 i yt-dlp

## Przegląd

JustDownIt to solidna i łatwa w obsłudze aplikacja desktopowa, opracowana przy użyciu PyQt6, zaprojektowana w celu płynnego pobierania treści wideo (MP4) i audio (MP3) z serwisu YouTube. Aplikacja stawia na pierwszym miejscu prostotę użytkowania, oferując intuicyjne sterowanie wyborem formatu mediów, preferencjami jakości oraz zarządzaniem katalogiem docelowym. Jej asynchroniczne działanie zapewnia responsywne środowisko użytkownika, nawet podczas aktywnych pobierań i procesów działających w tle.

## Kluczowe Funkcje

* **Dwa Tryby Pobierania**: Oferuje elastyczne opcje pobierania zarówno dla formatów wideo (MP4), jak i audio (MP3).
* **Inteligentne Wykrywanie Formatów**: Automatycznie analizuje adresy URL YouTube, aby przedstawić kompleksową listę dostępnych jakości i formatów wideo, co zapewnia użytkownikowi optymalny wybór.
* **Ekstrakcja Audio Wysokiej Jakości**: Obsługuje wyodrębnianie i konwersję strumieni audio do plików MP3 o wysokiej wierności (320 kbps).
* **Podgląd Miniatury**: Zapewnia natychmiastowe wizualne potwierdzenie, wyświetlając miniaturę filmu po wprowadzeniu adresu URL.
* **Konfigurowalny Katalog Wyjściowy**: Użytkownicy mogą łatwo określić preferowane miejsce pobierania, z rozsądnymi ścieżkami domyślnymi.
* **Monitorowanie Postępu w Czasie Rzeczywistym**: Posiada intuicyjny pasek postępu i szczegółową konsolę logów dla kompleksowej informacji zwrotnej o statusie pobierania i operacjach.
* **Zarządzanie Przerwaniami**: Umożliwia anulowanie trwających pobrań.
* **Automatyczne Zarządzanie Zależnościami**: Automatyzuje instalację niezbędnych pakietów Pythona (`yt-dlp`, `imageio-ffmpeg`, `requests`) i zarządza plikami binarnymi FFmpeg, usprawniając proces początkowej konfiguracji.


## Stos Technologiczny

* **Frontend**: PyQt6 dla natywnego i responsywnego, wieloplatformowego graficznego interfejsu użytkownika.
* **Logika Pobierania**: `yt-dlp` do wydajnego i niezawodnego parsowania i pobierania treści z YouTube.
* **Przetwarzanie Mediów**: `imageio-ffmpeg` do płynnej integracji i zarządzania plikami binarnymi FFmpeg, kluczowego dla konwersji formatów i łączenia strumieni.
* **Operacje Sieciowe**: `requests` do niezawodnej komunikacji HTTP, w szczególności do pobierania miniatur.
* **Wielowątkowość**: `QThread` z Pythona do asynchronicznego wykonywania zadań, zapobiegając zamrażaniu interfejsu użytkownika podczas intensywnych operacji.

## Wymagania Systemowe

* Python 3.x
* System Operacyjny: Windows

## Rozpoczęcie Pracy

Wykonaj poniższe kroki, aby skonfigurować i uruchomić JustDownIt na swoim komputerze.

### Instalacja

1.  **Sklonuj Repozytorium**:
    ```bash
    git clone [https://github.com/mitahezyf/JustDownIt.git]
    cd JustDownIt
    ```

2.  **Zainstaluj PyQt6**:
    ```bash
    pip install PyQt6
    ```

3.  **Uruchom Aplikację**:
    ```bash
    python main.py
    ```
    Przy pierwszym uruchomieniu JustDownIt automatycznie wykryje i zainstaluje wszelkie brakujące podstawowe zależności (`yt-dlp`, `imageio-ffmpeg`, `requests`) oraz pobierze niezbędne pliki binarne `FFmpeg`. Ta początkowa konfiguracja może zająć kilka chwil, w zależności od połączenia internetowego.

### Instrukcje Użytkowania

**Na repozytorium zamieszczony jest plik `JustDownIt.exe` który pozwala na bezpośrednie uruchomienie aplikacji ze wszystkimi zależnościami**

1.  **Uruchom Aplikację**: Uruchom `main.py` lub `JustDownIt.exe` jeżeli korzystasz z gotowego pliku exe.
2.  **Wprowadź URL**: Wklej adres URL żądanego filmu z YouTube w polu wprowadzania "URL filmu:".
3.  **Ładowanie Miniatury i Formatów**: Aplikacja automatycznie pobierze i wyświetli miniaturę filmu. Równocześnie wypełni listę rozwijaną "Jakość wideo:" dostępnymi formatami pobierania (istotne dla pobierania MP4).
4.  **Wybierz Typ Pobierania**: Wybierz "MP4 (wideo)" dla pobierania wideo lub "MP3 (audio)" dla ekstrakcji audio.
5.  **Zdefiniuj Folder Wyjściowy**: Sprawdź domyślny katalog pobierania lub określ własny za pomocą przycisku "Przeglądaj…".
6.  **Rozpocznij Pobieranie**: Kliknij "Rozpocznij pobieranie", aby rozpocząć proces pobierania.
7.  **Monitoruj Postęp**: Śledź status pobierania za pomocą paska postępu i przeglądaj szczegółowe logi w obszarze konsoli.
8.  **Anuluj Pobieranie**: Aby zatrzymać trwające pobieranie, kliknij "Anuluj pobieranie".
9.  **Wyczyść Logi**: Użyj przycisku "Wyczyść", aby wyczyścić konsolę logów.

## Struktura Projektu

* `main.py`: Punkt wejścia aplikacji, odpowiedzialny za inicjalizację głównego okna i orkiestrację początkowych kontroli zależności i instalacji.
* `ui_mainwindow.py`: Definiuje `YouTubeDownloader` QWidget, obejmujący cały układ graficznego interfejsu użytkownika, stylizację elementów oraz logikę interakcji użytkownika, taką jak pobieranie miniatur, obsługa pól tekstowych, przycisków i aktualizacji postępu, a także zarządzanie połączeniami z wątkami backendowymi.
* `threads.py`: Zawiera klasy oparte na `QThread` (`InstallThread`, `DownloadThread`, `FormatFetchThread`), które wykonują blokujące lub długotrwałe operacje (np. instalacja pakietów, pobieranie mediów, pobieranie informacji o formatach) asynchronicznie, aby utrzymać responsywność interfejsu użytkownika.
* `ytdown_core.py`: Zawiera fundamentalną logikę biznesową do interakcji z `yt-dlp` i `imageio-ffmpeg`. Obejmuje to funkcje do instalacji zależności, rozwiązywania ścieżki FFmpeg, rzeczywistych procesów pobierania wideo i audio oraz narzędzia do pobierania miniatur wideo i wyodrębniania identyfikatorów wideo.
* `theme.py`: Dedykowany moduł do stosowania ciemnego motywu wizualnego aplikacji, zarządzający ustawieniami `QPalette` PyQt6 i niestandardowymi arkuszami stylów.
* `ytdownico.ico`: Plik ikony aplikacji, zapewniający tożsamość marki.

## Dalszy rozwój
Program wciąż jest w trakcie rozwoju więc możliwe są błędy. W neidalekiej przyszłości planowane jest dodanie kolejnych funkcjonalności takich jak kolejkowanie, wybór formatu wyjściowego, motywy, możliwość ustawienia ogranicznika pobierania (obecnie program ogranicza do 25MB/s)


## Licencja

Ten projekt jest udostępniony na licencji [MIT License](LICENSE).
