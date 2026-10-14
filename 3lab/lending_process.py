from datetime import timedelta

from library_exceptions import DomainInvariantViolation, GatewayUnresolved


class LendingProcess:
    def __init__(self, book_repository, clock, fine_paid=None):
        self.book_repository = book_repository
        self.clock = clock
        self.fine_paid = fine_paid or (lambda reader_id: True)

    def reserve_book(self, loan):
        expires = self._add_working_days(self.clock.today(), 3)
        loan.reserve(expires)
        return loan

    def check_reservation(self, loan):
        if loan.reservation_expires is None:
            raise DomainInvariantViolation(
                "У бронирования не задан срок действия"
            )

        if self.clock.today() > loan.reservation_expires:
            loan.cancel("Истёк срок бронирования")
            return False

        loan.wait_for_issue()
        return True

    def check_reader_debt(self, loan):
        if not self.fine_paid(loan.reader_id):
            loan.reject("Есть неоплаченный штраф")
            return False

        return True

    def issue_book(self, loan):
        if loan.state_name == "Забронирована":
            if not self.check_reservation(loan):
                return False

        if not self.check_reader_debt(loan):
            return False

        book = self.book_repository.get(loan.book_id)
        book.issue()
        loan.issue()
        return True

    def extend_loan(self, loan, has_waiting_readers):
        if loan.extensions >= 1 or has_waiting_readers:
            raise GatewayUnresolved(
                "Продление невозможно: оно уже использовано "
                "или есть очередь"
            )

        new_end = loan.period.end + timedelta(days=7)
        loan.extend(new_end)
        return new_end

    def send_due_reminder(self, loan):
        reminder_date = loan.period.end - timedelta(days=2)

        if self.clock.today() >= reminder_date and not loan.returned:
            loan._record("due_reminder", reminder_date.isoformat())
            return True

        return False

    def check_overdue(self, loan):
        if (
            self.clock.today() > loan.period.end
            and loan.state_name in ("Выдана", "Продлена")
        ):
            loan.mark_overdue()
            return True

        return False

    def process_long_overdue(self, loan):
        deadline = loan.period.end + timedelta(days=30)

        if (
            self.clock.today() >= deadline
            and loan.state_name == "Просрочена"
        ):
            loan.send_to_administration()
            return True

        return False

    def return_book(self, loan, damage_found=False):
        if damage_found:
            loan._record(
                "damage_report_created",
                "Обнаружено повреждение книги"
            )
            loan._record(
                "damage_fine_assessed",
                "Штраф за повреждение требует расчёта"
            )

        book = self.book_repository.get(loan.book_id)
        loan.return_book(self.clock.today())
        book.return_copy()

        return loan.fine

    @staticmethod
    def _add_working_days(start_date, days):
        result = start_date
        added = 0

        while added < days:
            result += timedelta(days=1)

            if result.weekday() < 5:
                added += 1

        return result