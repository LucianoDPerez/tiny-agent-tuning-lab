#!/bin/bash
# Verifies the migration against an ephemeral Postgres: applies it twice
# (idempotent), inserts a booking + key, then proves the UNIQUE constraint
# rejects a duplicate key. Self-contained: psql runs inside the container.
set -e
C=pg-fixture-$$
docker run -d --rm --name $C -e POSTGRES_PASSWORD=pw -p 55433:5432 postgres:16-alpine >/dev/null
trap "docker stop $C >/dev/null" EXIT
for i in $(seq 1 30); do docker exec $C pg_isready -U postgres >/dev/null 2>&1 && break; sleep 1; done
P() { docker exec -i $C psql -U postgres -d postgres -v ON_ERROR_STOP=1 "$@"; }
P -f - < migration.sql
P -f - < migration.sql
P -c "INSERT INTO bookings(id,customer,slot) VALUES ('bk_1','ana','10:00');"
P -c "INSERT INTO idempotency_keys(key,booking_id) VALUES ('k1','bk_1');"
if P -c "INSERT INTO idempotency_keys(key,booking_id) VALUES ('k1','bk_1');" 2>&1 | grep -qi "duplicate\|unique"; then
  echo PASS
else
  echo FAIL; exit 1
fi
