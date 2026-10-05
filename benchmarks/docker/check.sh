#!/bin/bash
# Static + build checks for the hardening task.
set -e
grep -q "^USER " Dockerfile || { echo "FAIL: no USER"; exit 1; }
grep -q "^HEALTHCHECK" Dockerfile || { echo "FAIL: no HEALTHCHECK"; exit 1; }
test -f .dockerignore || { echo "FAIL: no .dockerignore"; exit 1; }
grep -q "restart:" compose.yml || { echo "FAIL: no restart policy"; exit 1; }
docker compose config >/dev/null && docker build -t fixture-api . >/dev/null
echo PASS
