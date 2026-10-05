"""Executable check: same key twice -> same id, count stays 1."""
from store import BookingStore


def main() -> None:
    s = BookingStore()
    first = s.create_with_key("ana", "10:00", "k1")
    second = s.create_with_key("ana", "10:00", "k1")
    ok = first == second and s.count() == 1
    print("PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
