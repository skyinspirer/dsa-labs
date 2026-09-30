from datetime import datetime

from library.library_exceptions import DomainInvariantViolation


class Ride:
    def __init__(
        self,
        ride_id,
        scooter_id,
        user_id,
        tariff,
        start_time
    ):
        self.id = ride_id
        self.scooter_id = scooter_id
        self.user_id = user_id
        self.tariff = tariff
        self.start_time = start_time
        self._end_time = None
        self._price = None

    def finish(self, end_time):
        if end_time < self.start_time:
            raise DomainInvariantViolation(
            )

        self._end_time = end_time

        minutes = int(
            (end_time - self.start_time).total_seconds() / 60
        )

        price = minutes * self.tariff.price_per_minute

        self._price = max(
            price,
            self.tariff.minimum_price
        )