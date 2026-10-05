# Python fixture — idempotent creation (1 file: store.py; check already written)
#
# Task prompt for the agent:
#   implementar: en store.py agregá el método create_with_key(customer, slot, key)
#   que devuelva el MISMO id cuando la clave ya existe, sin duplicar
#   (guardá clave -> id en un dict, con early return). Verificá con
#   python3 check.py  -> PASS
python3 check.py
