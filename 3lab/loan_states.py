from library_exceptions import TransitionNotAllowed


class LoanState:
    name = "Неизвестное состояние"
    allowed_events = ()

    def _deny(self, loan, event):
        raise TransitionNotAllowed(
            f"Переход из состояния «{loan.state_name}» "
            f"по событию «{event}» запрещён"
        )

    def wait_for_issue(self, loan):
        self._deny(loan, "wait_for_issue")

    def issue(self, loan):
        self._deny(loan, "issue")

    def extend(self, loan, new_end):
        self._deny(loan, "extend")

    def mark_overdue(self, loan):
        self._deny(loan, "mark_overdue")

    def return_book(self, loan, return_date):
        self._deny(loan, "return_book")

    def reject(self, loan, reason):
        self._deny(loan, "reject")

    def cancel(self, loan, reason):
        self._deny(loan, "cancel")

    def send_to_administration(self, loan):
        self._deny(loan, "send_to_administration")


class ReservedState(LoanState):
    name = "Забронирована"
    allowed_events = ("wait_for_issue", "cancel", "reject")

    def wait_for_issue(self, loan):
        loan._change_state(WaitingForIssueState(), "wait_for_issue")

    def cancel(self, loan, reason):
        loan._change_state(CancelledState(), "cancel", reason)

    def reject(self, loan, reason):
        loan._change_state(RejectedState(), "reject", reason)


class WaitingForIssueState(LoanState):
    name = "Ожидает выдачи"
    allowed_events = ("issue", "cancel", "reject")

    def issue(self, loan):
        loan._change_state(IssuedState(), "issue")

    def cancel(self, loan, reason):
        loan._change_state(CancelledState(), "cancel", reason)

    def reject(self, loan, reason):
        loan._change_state(RejectedState(), "reject", reason)


class IssuedState(LoanState):
    name = "Выдана"
    allowed_events = ("extend", "mark_overdue", "return_book")

    def extend(self, loan, new_end):
        loan.period = type(loan.period)(loan.period.start, new_end)
        loan._extensions += 1
        loan._change_state(ExtendedState(), "extend", new_end.isoformat())

    def mark_overdue(self, loan):
        loan._change_state(OverdueState(), "mark_overdue")

    def return_book(self, loan, return_date):
        loan._finish_return(return_date)
        loan._change_state(
            ReturnedState(), "return_book", return_date.isoformat()
        )


class ExtendedState(LoanState):
    name = "Продлена"
    allowed_events = ("mark_overdue", "return_book")

    def mark_overdue(self, loan):
        loan._change_state(OverdueState(), "mark_overdue")

    def return_book(self, loan, return_date):
        loan._finish_return(return_date)
        loan._change_state(
            ReturnedState(), "return_book", return_date.isoformat()
        )


class OverdueState(LoanState):
    name = "Просрочена"
    allowed_events = ("return_book", "send_to_administration")

    def return_book(self, loan, return_date):
        loan._finish_return(return_date)
        loan._change_state(
            ReturnedState(), "return_book", return_date.isoformat()
        )

    def send_to_administration(self, loan):
        loan._change_state(
            SentToAdministrationState(), "send_to_administration"
        )


class ReturnedState(LoanState):
    name = "Возвращена"


class RejectedState(LoanState):
    name = "Отклонена"


class CancelledState(LoanState):
    name = "Отменена"


class SentToAdministrationState(LoanState):
    name = "Передана администрации"