# Go fixture — idempotent creation (1 file: store.go; test already written)
#
# Task prompt for the agent:
#   implementar: en store.go agregá el método CreateWithKey(customer, slot, key)
#   que devuelva el MISMO id cuando la clave ya existe, sin duplicar
#   (guardá clave -> id). Después corré go build y go test.
#
# Verify: go build ./... && go vet ./... && go test ./...  -> ok
go build ./... && go vet ./... && go test ./...
