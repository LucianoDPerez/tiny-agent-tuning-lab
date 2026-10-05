"""Booking store with duplicate-on-retry flaw (hexagonal port shape)."""


class BookingStore:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def create(self, customer: str, slot: str) -> str:
        if not customer or not slot:
            raise ValueError("customer and slot are required")
        booking_id = f"bk_{len(self._store) + 1}"
        self._store[booking_id] = f"{customer}|{slot}"
        return booking_id

    def count(self) -> int:
        return len(self._store)
