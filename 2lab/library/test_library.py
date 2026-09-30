import unittest
from datetime import date

from library_value_objects import BookId, ReaderId, LoanPeriod
from book import Book
from loan import Loan
from library_service import LibraryService


class TestLibrary(unittest.TestCase):

    def setUp(self):
        self.book = Book(
            BookId(1),
            "Война и мир",
            2
        )

        self.loan = Loan(
            1,
            BookId(1),
            ReaderId(1),
            LoanPeriod(
                date(2026, 9, 1),
                date(2026, 9, 10)
            )
        )

        self.service = LibraryService()

    def test_issue_book(self): #Проверка выдачи книги.

        self.service.issue_book(
            self.book,
            self.loan
        )

        self.assertEqual(
            self.book._available,
            1
        )

    def test_fine_for_late_return(self): #Проверка штрафа за просрочку

        self.service.issue_book(
            self.book,
            self.loan
        )

        self.loan.return_book(
            date(2026, 9, 15)
        )

        self.assertGreater(
            self.loan.fine.amount,
            0
        )

    def test_cannot_issue_unavailable_book(self): #Проверка запрета выдачи книги, если экземпляров нет

        book = Book(
            BookId(2),
            "Пример книги",
            1
        )

        loan1 = Loan(
            2,
            BookId(2),
            ReaderId(2),
            LoanPeriod(
                date(2026, 9, 1),
                date(2026, 9, 10)
            )
        )

        loan2 = Loan(
            3,
            BookId(2),
            ReaderId(3),
            LoanPeriod(
                date(2026, 9, 1),
                date(2026, 9, 10)
            )
        )

        self.service.issue_book(book, loan1)

        with self.assertRaises(Exception):
            self.service.issue_book(book, loan2)


if __name__ == "__main__":
    unittest.main()