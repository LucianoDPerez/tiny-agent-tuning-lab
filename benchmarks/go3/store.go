// Package bookings: idempotent creation via caller-supplied keys.
package bookings

import (
	"errors"
	"fmt"
	"sync"
)

type Store struct {
	mu   sync.Mutex
	byID map[string]string
}

func NewStore() *Store { return &Store{byID: map[string]string{}} }

// Create stores customer|slot and returns a new id. Retries with the same
// payload currently create duplicates.
func (s *Store) Create(customer, slot string) (string, error) {
	if customer == "" || slot == "" {
		return "", errors.New("customer and slot are required")
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	id := fmt.Sprintf("bk_%d", len(s.byID)+1)
	s.byID[id] = customer + "|" + slot
	return id, nil
}

func (s *Store) Count() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return len(s.byID)
}
