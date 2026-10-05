# PHP fixture — input validation with clear 400s (1 file: BookingController.php)
#
# Task prompt for the agent:
#   implementar: en BookingController.php el método store acepta cualquier
#   input y siempre devuelve 201. Agregá validación: si faltan customer o
#   slot (vacíos), devolvé ['status' => 400, 'error' => mensaje claro].
#   El input válido debe seguir devolviendo 201. Verificá con php -l y runner.php.
#
# Verify: php -l BookingController.php && php runner.php  -> PASS
php -l BookingController.php && php runner.php
