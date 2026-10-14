from dataclasses import dataclass
from datetime import date

from library_exceptions import DomainInvariantViolation
from library_value_objects import Fine
from loan_states import ReservedState


@dataclass(frozen=True)
class DomainEvent:
    name: str
    occurred_on: date
    details: str = ""


class Loan:
    def __init__(self, loan_id, book_id, reader_id, period):
        self.id = loan_id
        self.book_id = book_id
        self.reader_id = reader_id
        self.period = period
        self._fine = Fine(0)
        self._state = ReservedState()
        self._extensions = 0
        self._events = []
        self._return_date = None
        self._reservation_date = period.start
        self._reservation_expires = None

    @property
    def state_name(self):
        return self._state.name

    @property
    def allowed_events(self):
        return self._state.allowed_events

    @property
    def events(self):
        return tuple(self._events)

    @property
    def fine(self):
        return self._fine

    @property
    def extensions(self):
        return self._extensions

    @property
    def returned(self):
        return self.state_name == "Возвращена"

    @property
    def reservation_expires(self):
        return self._reservation_expires

    @property
    def return_date(self):
        return self._return_date

    def _record(self, name, details=""):
        self._events.append(
            DomainEvent(name, date.today(), details)
        )

    def _change_state(self, state, event, details=""):
        self._state = state
        self._record(event, details)

    def reserve(self, expires_on):
        self._reservation_expires = expires_on
        self._record("reserve", expires_on.isoformat())

    def wait_for_issue(self):
        self._state.wait_for_issue(self)

    def issue(self):
        self._state.issue(self)

    def extend(self, new_end):
        self._state.extend(self, new_end)

    def mark_overdue(self):
        self._state.mark_overdue(self)

    def return_book(self, return_date):
        self._state.return_book(self, return_date)

    def reject(self, reason):
        self._state.reject(self, reason)

    def cancel(self, reason):
        self._state.cancel(self, reason)

    def send_to_administration(self):
        self._state.send_to_administration(self)

    def _finish_return(self, return_date):
        if return_date < self.period.start:
            raise DomainInvariantViolation(
                "Книга возвращена раньше выдачи"
            )

        if return_date > self.period.end:
            days = (return_date - self.period.end).days
            self._fine = Fine(days * 100)

        self._return_date = return_date