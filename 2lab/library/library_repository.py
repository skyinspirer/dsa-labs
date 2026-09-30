from typing import Protocol


class BookRepository(Protocol):
    def get(self, book_id):
        ...

    def save(self, book):
        ...


class InMemoryBookRepository:
    def __init__(self):
        self._items = {}

    def get(self, book_id):
        return self._items[book_id]

    def save(self, book):
        self._items[book.id] = book