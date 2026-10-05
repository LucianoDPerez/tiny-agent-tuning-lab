# DB fixture — idempotency schema (file: migration.sql; Postgres dialect)
#
# Task prompt for the agent:
#   implementar: en migration.sql falta la pieza de idempotencia. Agregá la
#   tabla idempotency_keys (key TEXT PRIMARY KEY, booking_id TEXT NOT NULL
#   REFERENCES bookings(id), created_at TIMESTAMPTZ DEFAULT now()) de forma
#   que aplicar la migración dos veces no falle (IF NOT EXISTS). Verificá
#   con ./verify.sh (levanta postgres efímero y prueba el UNIQUE).
#
# Verify: ./verify.sh  -> PASS (unique constraint rejects duplicate key)
# NOTE: idempotency_keys table intentionally REMOVED from migration.sql for the task.
./verify.sh
