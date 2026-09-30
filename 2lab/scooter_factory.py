from scooter import Scooter
from scooter_value_objects import ScooterId, BatteryLevel
from library_exceptions import DomainInvariantViolation


def restore_scooter(data):
    scooter = Scooter(
        ScooterId(data["id"]),
        BatteryLevel(data["battery"])
    )

    if data["status"] not in [
        Scooter.FREE,
        Scooter.RENTED,
        Scooter.SERVICE
    ]:
        raise DomainInvariantViolation(
        )

    scooter._status = data["status"]

    return scooter