from dataclasses import dataclass
from datetime import date

from library_exceptions import InvalidValueObject


@dataclass(frozen=True)
class BookId:
    value: int

    def __post_init__(self):
        if self.value <= 0:
            raise InvalidValueObject("Некорректный ID книги")


@dataclass(frozen=True)
class ReaderId:
    value: int

    def __post_init__(self):
        if self.value <= 0:
            raise InvalidValueObject("Некорректный ID читателя")


@dataclass(frozen=True)
class LoanPeriod:
    start: date
    end: date

    def __post_init__(self):
        if self.start > self.end:
            raise InvalidValueObject("Дата начала позже даты окончания")


@dataclass(frozen=True)
class Fine:
    amount: float

    def __post_init__(self):
        if self.amount < 0:
            raise InvalidValueObject("Штраф не может быть отрицательным")