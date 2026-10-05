# Matriz políglota: fixture × modelo (tareas grounded)

| fixture | base-1.7B | base-4B | 4b-v1 | 4b-v2 | 4b-v3 | notas |
|---|---|---|---|---|---|---|
| ts (card Link) | ✅ (346s) | ✅ | ❌ (planifica, no emite edit) | ❌ (corrompe: mezcla 2 cards) | ✅ (reemplazo exacto, ✅) | V2 regresó en TS; V3 lo cura con trace 35B |
| java (idempotencia) | ❌ (0 writes) | ❌ (no consulta la clave) | — | ✅ (early-return, PASS) | — (hereda V2) | fallo destilado de Intern-S2-Preview |
| php (validación 400) | ✅ | ✅ | — | ✅ (PASS) | — (hereda V2) | |
| go (idempotencia+test) | — | ❌ (0 writes) | — | ✅ (mutex, go test ok) | — (hereda V2) | |
| docker (hardening) | — | ❌ (roto) | — | ✅ (6/6 checks) | — (hereda V2) | solo cuelga el pull (infra) |
| db (UNIQUE) | — | ✅ (postgres real) | — | ✅ (PASS) | — (hereda V2) | |
| python (idempotencia) | — | — | — | ❌ (hackea test + ✅ falso) | ✅ (dict separado, PASS, no toca test) | V3 enseña honestidad operacional |

## Radio multi-archivo (4B-V2/V3)
| tarea | resultado | notas |
|---|---|---|
| java 3 archivos (store+Main+clase nueva) | ✅ (PASS manual) | crea + cablea bien; harness no auto-verificó |
| go 3 archivos (validator+store+test) | ✅ (lint/tests/build ✅) | cierre completo del harness |
| docker 3 archivos (Dockerfile+compose+new) | ✅ (6/6 checks) | implícito en fixture docker |

## Guía de uso 4B-V3 en agent-devs (evidencia, no teoría)
- 🟢 **Excelente**: tareas grounded de 1-3 archivos con objetivo + verificación explícitos, en TS/Java/PHP/Go/Python/SQL-DDL/Docker. Lee → edita con old_str exacto → verifica → reporta.
- 🟡 **Bueno con restricciones**: 2-3 archivos (medido hasta 3), repos conocidos, tareas donde debe buscar primero (recovery simple).
- 🟠 **Riesgoso**: 4+ archivos, exploración abierta en repos grandes, requisitos ambiguos, decisiones de diseño múltiples.
- 🔴 **No delegar solo**: "implementá esta feature" sin spec, migraciones complejas, planificación autónoma larga.
- **Planner**: puede proponer planes con archivos correctos, pero verificar siempre el plan antes de ejecutar (tiende a planificar de más y actuar de menos en V1; V2/V3 actúan).
- **Reviewer**: pendiente de medir (siguiente batería: bug plantado + severidad).
- **Regla de oro**: si la tarea cabe en "modificá ESTE archivo para X y verificá con Y", V3 la cierra. Si empieza con "explorá...", descomponé en el harness primero.
