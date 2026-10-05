package bookings

import "testing"

// After the fix, CreateWithKey with the same key must return the same id
// and keep Count at 1.
func TestIdempotentCreate(t *testing.T) {
	s := NewStore()
	first, err := s.CreateWithKey("ana", "10:00", "key-1")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	second, err := s.CreateWithKey("ana", "10:00", "key-1")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if first != second {
		t.Fatalf("expected same id, got %q and %q", first, second)
	}
	if got := s.Count(); got != 1 {
		t.Fatalf("expected count 1, got %d", got)
	}
}
