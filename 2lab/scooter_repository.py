from typing import Protocol


class ScooterRepository(Protocol):
    def get(self, scooter_id):
        ...

    def save(self, scooter):
        ...


class InMemoryScooterRepository:
    def __init__(self):
        self._items = {}

    def get(self, scooter_id):
        return self._items[scooter_id]

    def save(self, scooter):
        self._items[scooter.id] = scooter