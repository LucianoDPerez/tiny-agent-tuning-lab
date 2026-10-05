-- Idempotency store: one row per key. Replays return the saved result
-- instead of re-executing. The UNIQUE constraint is the correctness core.
CREATE TABLE IF NOT EXISTS bookings (
    id          TEXT PRIMARY KEY,
    customer    TEXT NOT NULL,
    slot        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
