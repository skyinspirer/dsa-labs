from library_exceptions import DomainInvariantViolation


class Book:
    def __init__(self, book_id, title, copies):
        if copies < 0:
            raise DomainInvariantViolation(
                "Количество экземпляров не может быть отрицательным"
            )

        self.id = book_id
        self.title = title
        self._copies = copies
        self._available = copies

    @property
    def available(self):
        return self._available

    def issue(self):
        if self._available <= 0:
            raise DomainInvariantViolation(
                "Нет доступных экземпляров книги"
            )

        self._available -= 1

    def return_copy(self):
        if self._available >= self._copies:
            raise DomainInvariantViolation(
                "Все экземпляры уже находятся в библиотеке"
            )

        self._available += 1