from book import Book
from library_value_objects import BookId
from library_exceptions import DomainInvariantViolation


def restore_book(data):
    book = Book(
        BookId(data["id"]),
        data["title"],
        data["copies"]
    )

    if data["available"] < 0:
        raise DomainInvariantViolation(
            "Некорректное количество экземпляров"
        )

    book._available = data["available"]

    return book