import unittest
from datetime import datetime

from scooter_value_objects import (
    ScooterId,
    UserId,
    BatteryLevel,
    Tariff
)
from scooter import Scooter
from ride import Ride
from scooter_service import ScooterRentalService


class TestScooterRental(unittest.TestCase):

    def setUp(self):
        self.scooter = Scooter(
            ScooterId(1),
            BatteryLevel(80)
        )

        self.tariff = Tariff(
            price_per_minute=10,
            minimum_price=50
        )

        self.ride = Ride(
            1,
            ScooterId(1),
            UserId(1),
            self.tariff,
            datetime(2026, 9, 30, 10, 0)
        )

        self.service = ScooterRentalService()

    def test_start_ride(self): #Проверка начала поездки

        self.service.start_ride(
            self.scooter,
            self.ride,
            20
        )

        self.assertEqual(
            self.scooter._status,
            "арендован"
        )
        
    def test_finish_ride(self): #Проверка завершения поездки

        self.service.start_ride(
            self.scooter,
            self.ride,
            20
        )

        self.ride.finish(
            datetime(2026, 9, 30, 10, 15)
        )

        self.assertGreater(
            self.ride._price,
            0
        )

    def test_cannot_rent_low_battery_scooter(self): #Проверка запрета аренды

        scooter = Scooter(
            ScooterId(2),
            BatteryLevel(10)
        )

        ride = Ride(
            2,
            ScooterId(2),
            UserId(2),
            self.tariff,
            datetime(2026, 9, 30, 11, 0)
        )

        with self.assertRaises(Exception):
            self.service.start_ride(
                scooter,
                ride,
                20
            )

    def test_cannot_finish_ride_before_start(self): #Проверка запрета завершения поездки раньше начала

        self.service.start_ride(
            self.scooter,
            self.ride,
            20
        )

        with self.assertRaises(Exception):
            self.ride.finish(
                datetime(2026, 9, 30, 9, 0)
            )


if __name__ == "__main__":
    unittest.main()