from library_exceptions import DomainInvariantViolation


class Book:
    def __init__(self, book_id, title, copies):
        self.id = book_id
        self.title = title
        self._copies = copies
        self._available = copies

    def issue(self):
        if self._available <= 0:
            raise DomainInvariantViolation(
                "Нет доступных экземпляров книги"
            )

        self._available -= 1

    def return_copy(self):
        self._available += 1