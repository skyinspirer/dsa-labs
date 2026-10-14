import unittest
from datetime import date

from library_value_objects import BookId, ReaderId, LoanPeriod
from book import Book
from loan import Loan
from library_service import LibraryService
from library_exceptions import TransitionNotAllowed
from library_repository import InMemoryBookRepository
from clock import FixedClock
from lending_process import LendingProcess


class TestLibrary(unittest.TestCase):
    def setUp(self):
        self.book = Book(BookId(1), "Война и мир", 2)

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

    def test_issue_book(self):
        self.loan.wait_for_issue()

        self.service.issue_book(self.book, self.loan)

        self.assertEqual(self.book.available, 1)
        self.assertEqual(self.loan.state_name, "Выдана")

    def test_fine_for_late_return(self):
        self.loan.wait_for_issue()
        self.service.issue_book(self.book, self.loan)

        self.loan.return_book(date(2026, 9, 15))

        self.assertGreater(self.loan.fine.amount, 0)

    def test_cannot_issue_unavailable_book(self):
        book = Book(BookId(2), "Пример книги", 1)

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

        loan1.wait_for_issue()
        loan2.wait_for_issue()

        self.service.issue_book(book, loan1)

        with self.assertRaises(Exception):
            self.service.issue_book(book, loan2)

    def test_forbidden_transition(self):
        with self.assertRaises(TransitionNotAllowed):
            self.loan.return_book(date(2026, 9, 5))

    def test_reservation_expiry(self):
        repo = InMemoryBookRepository()
        repo.save(self.book)

        clock = FixedClock(date(2026, 9, 1))
        process = LendingProcess(repo, clock)

        process.reserve_book(self.loan)

        clock.set_date(date(2026, 9, 6))

        self.assertFalse(process.check_reservation(self.loan))
        self.assertEqual(self.loan.state_name, "Отменена")


if __name__ == "__main__":
    unittest.main()