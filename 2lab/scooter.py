from library.library_exceptions import DomainInvariantViolation


class Scooter:
    FREE = "свободен"
    RENTED = "арендован"
    SERVICE = "на обслуживании"

    def __init__(self, scooter_id, battery):
        self.id = scooter_id
        self._battery = battery
        self._status = self.FREE

    def rent(self, minimum_battery):
        if self._status != self.FREE:
            raise DomainInvariantViolation(
            )

        if self._battery.value < minimum_battery:
            raise DomainInvariantViolation(
            )

        self._status = self.RENTED

    def finish_rent(self):
        if self._status != self.RENTED:
            raise DomainInvariantViolation(
            )

        self._status = self.FREE