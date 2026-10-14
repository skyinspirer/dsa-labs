from book import Book
from library_value_objects import BookId
from library_exceptions import DomainInvariantViolation


def restore_book(data):
    book = Book(
        BookId(data["id"]),
        data["title"],
        data["copies"]
    )

    if not 0 <= data["available"] <= data["copies"]:
        raise DomainInvariantViolation(
            "Некорректное количество доступных экземпляров"
        )

    book._available = data["available"]
    return book