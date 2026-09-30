from dataclasses import dataclass

from library.library_exceptions import InvalidValueObject


@dataclass(frozen=True)
class ScooterId:
    value: int

    def __post_init__(self):
        if self.value <= 0:
            raise InvalidValueObject("Некорректный ID самоката")


@dataclass(frozen=True)
class UserId:
    value: int

    def __post_init__(self):
        if self.value <= 0:
            raise InvalidValueObject("Некорректный ID пользователя")


@dataclass(frozen=True)
class BatteryLevel:
    value: int

    def __post_init__(self):
        if self.value < 0 or self.value > 100:
            raise InvalidValueObject(
            )


@dataclass(frozen=True)
class Tariff:
    price_per_minute: float
    minimum_price: float

    def __post_init__(self):
        if self.price_per_minute < 0:
            raise InvalidValueObject(
            )

        if self.minimum_price < 0:
            raise InvalidValueObject(
            )