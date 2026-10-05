# 3-file radius task (go): validator + store + test
#
# Task prompt for the agent:
#   implementar en este directorio (3 archivos):
#   1) Creá validator.go: función Validate(customer, slot) error que rechace
#      vacíos (package bookings).
#   2) En store.go agregá CreateWithKey(customer, slot, key) con map clave->id,
#      mutex y early return; usá Validate para inputs.
#   3) Actualizá store_test.go para cubrir: misma clave -> mismo id, count 1;
#      input vacío -> error.
#   Verificá con: go build ./... && go vet ./... && go test ./...  -> ok
go build ./... && go vet ./... && go test ./...
