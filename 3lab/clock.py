from datetime import date, datetime, timedelta
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        ...

    def today(self) -> date:
        ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now()

    def today(self) -> date:
        return self.now().date()


class ShiftedClock:
    def __init__(self):
        self._offset = timedelta(0)
        self._last_time = self.now()

    def now(self) -> datetime:
        return datetime.now() + self._offset

    def today(self) -> date:
        return self.now().date()

    def set_time(self, new_time: datetime):
        current_time = self.now()

        if new_time < current_time:
            raise ValueError("Нельзя переводить часы назад")

        self._offset = new_time - datetime.now()
        self._last_time = new_time