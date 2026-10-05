# 3-file radius task (java): extract idempotency into its own class + wire + verify
#
# Task prompt for the agent:
#   implementar en este directorio (3 archivos):
#   1) Creá IdempotencyStore.java: clase con Map clave->id, métodos
#      lookup(key) (devuelve id o null) y remember(key, id).
#   2) En BookingService.java agregá createBookingWithKey(customer, slot, key)
#      que use IdempotencyStore (early return si la clave existe) y un campo
#      store para bookings.
#   3) Actualizá Main.java para llamar dos veces con clave k1 y verificar
#      igualdad de ids y count==1 (imprimir PASS/FAIL).
#   Verificá con: javac *.java && java Main  -> PASS
javac *.java && java Main
