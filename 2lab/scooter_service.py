class ScooterRentalService:
    def start_ride(self, scooter, ride, minimum_battery):
        scooter.rent(minimum_battery)
        return ride