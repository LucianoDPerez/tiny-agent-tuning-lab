# Java fixture — idempotent booking creation (1 file: BookingService.java)
#
# Task prompt for the agent:
#   implementar: en BookingService.java el método createBooking duplica reservas
#   cuando el cliente reintenta. Agregá soporte de clave de idempotencia:
#   createBookingWithKey(customer, slot, idemKey) que devuelva el MISMO id
#   si la clave ya existe, sin duplicar. Actualizá Main.java para usar la
#   clave y que imprima PASS. Verificá compilando y corriendo.
#
# Verify: ./verify.sh  (javac + java Main -> PASS)
javac BookingService.java Main.java && java Main
