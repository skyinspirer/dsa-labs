from library_exceptions import DomainInvariantViolation
from library_value_objects import Fine


class Loan:
    def __init__(self, loan_id, book_id, reader_id, period):
        self.id = loan_id
        self.book_id = book_id
        self.reader_id = reader_id
        self.period = period
        self._returned = False
        self._fine = Fine(0)

    def return_book(self, return_date):
        if self._returned:
            raise DomainInvariantViolation(
                "Книга уже возвращена"
            )

        if return_date < self.period.start:
            raise DomainInvariantViolation(
                "Книга возвращена раньше выдачи"
            )

        if return_date > self.period.end:
            days = (return_date - self.period.end).days
            self._fine = Fine(days * 100)

        self._returned = True

    @property
    def fine(self):
        return self._fine