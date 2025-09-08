# blad sygnalizujacy brak wymaganej zaleznosci w srodowisku
class DependencyMissingError(RuntimeError):
    """Brak wymaganej zależności w środowisku."""


# blad uzywany do przerwania operacji kiedy zostanie anulowana przez uzytkownika
class CancelledError(Exception):
    """Użytkownik anulował operację."""
