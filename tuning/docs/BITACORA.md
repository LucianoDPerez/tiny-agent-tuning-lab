# Bitácora Spark-X2.5-1.7B fine-tune

## Objetivo
Convertir Spark-X2.5-1.7B en un SLM útil para coding agentico en agent-devs (harness `~/agent-lucho`), con criterios de dev senior (SOLID, KISS, DRY, idempotencia, dedup, backpressure, OWASP) y, sobre todo, capaz de completar tareas reales.

## Baselines
- **Spark base + chat template con thinking OFF**: rubric heurístico 31/40 (no monólogo, conciso, estructurado)
- **Spark base (chat template thinking ON por defecto)**: 20/40 — el meta-razonamiento ("We need to…") viene del propio template, no del modelo
- **V1 (30 ejemplos mixtos, 6 epochs, LR 1e-4, grad-accum 8)**: 24/40 — sobreajuste al estilo, perdió estructura

## Iteraciones (LoRA r16, MPS)
| Iteración | Datos | LR | Epochs | Rubric 8 | Held-out | Observación |
|---|---|---|---|---|---|---|
| V1 | train.jsonl+train_agent_discipline.jsonl (30) | 1e-4 | 6 | 24/40 | — | Más conciso, pierde listas |
| V2-A | conceptos (train.jsonl, 18) | 5e-5 | 3 | 25/40 | — | Pierde estructura; conceptos solos degradan |
| V2-B | disciplina (train_agent_discipline.jsonl, 12) | 5e-5 | 3 | 33/40 | 27/35 | Mejora formato, +2 sobre base |
| V3 | disciplina 12 + conceptos estructurales 10 | 5e-5 | 3 | 24/40 | 21/35 | Conceptos en párrafo rompen formato |
| V4 | disciplina 13 (estructura explícita + circuit breaker) | 5e-5 | 3 | 32/40 | 28/35 | Empate con V2-B; mejor estructura explícita |

## Evidencia clave
- Los conceptos declarativos degradan el formato: SFT de Q&A enseña lo declarativo, no el comportamiento del agente.
- Spark es un modelo thinking: el chat template default (`enable_thinking=true`) producía respuestas "metapensadas". Lo dejamos en `false` para evals y training.
- **Run real (agente completo) V4 (Q4_K_M local): NO completa la tarea "card de Pacientes clickeable"**. Fallos: inventó paths (`/Users/luchop/PROYECTOS-IA-TurnoSmart`), leyó archivos como `Users-luchop-PROYECTOS-IA-TurnoSmart/app/page.tsx` (joining path raro), no tocó el repo. Trace guardado en `/tmp/spark_trace_pacientes*.jsonl`.
- TurnoSmart `npm run build` falla por `docs/*.canvas.tsx` con `import ... from 'cursor/canvas'` → arreglado en branch `spark-card-click` excluyendo `docs` en tsconfig.

## Decisiones
- Arquitectura custom `Spark2_5ForCausalLM`: no hay soporte en mlx-lm → LoRA con `transformers+peft+trl` en MPS. GGUF funciona con llama.cpp (convirtió con `~/llama.cpp/convert_hf_to_gguf.py` f16 → `llama-quantize Q4_K_M`).
- Dataset en formato chat con system prompt de dev senior. Respuestas deben ser directas, con listas y línea de verificación; el meta-razonamiento viña del template thinking, no hay que enseñar "pensar", sino "decidir+justificar breve+actuar".
- Próximo: entrenar sobre transcripts reales del harness (tool calls + verify) para pasar de "buen resumidor" a "agente que termina tareas".

## V5 (disciplina + 6 trayectorias agent con tool calls)
- Datos: 13 Q&A V4 + 6 trajs (search→read→edit→verify) renderizados a texto con chat template. Entrenado desde base, 2 epochs, LR 5e-5.
- Rubric Q&A: 30/40 (levemente bajo V4). Tool-eval (primera tool correcta con path exacto): 5/6, igual que base.
- **Run real Pacientes con V5 GGUF**: NO escribe. Mejoras vs V4: usa paths relativos al inicio, llama search_code con path exacto del repo e inspect_routes (diversidad de tools). Fallo persistente: loop de read_file sobre archivos irrelevantes (OAuthRedirect.tsx repetido, directorios leídos como archivos), nunca converge a edit. 1024s, 36k tokens.
- Lección: el modelo no sabe recuperarse cuando el search devuelve vacío ("Pacientes" no existe; la card real es de métricas/clientes). V6 debe enseñar recuperación + regla de no-releer.

## V6 (V4 + 6 trajs V5 + 4 trajs V6 recovery/no-releer)
- Datos: 23 ejemplos en texto. 2 epochs, LR 5e-5.
- Rubric Q&A: 31/40. Tool-eval: 5/6 (igual que base/V5).
- **Run real Pacientes con V6 GGUF**: NO escribe (19 read_file, 0 writes, 1337s). Mejora: exploración sistemática por rangos y búsquedas de dominio (Professional|Client|Service). Fallo: leyó `app/page.tsx` (landing pública) en vez de `app/app/page.tsx` (dashboard) y nunca convergió a edit.
- Patrón en V4/V5/V6 real runs: el 1.7B explora pero no se compromete con un edit. Próximo: test diagnóstico con tarea angosta (archivo+cambio exactos) para aislar exploración vs escritura.

## V6 narrow-task breakthrough (primera escritura real)
- Tarea angosta (archivo + bloque exactos) con V6 GGUF: **el modelo SÍ escribe** — `edit_file` con old_str exacto copiado del read, archivo correcto, `M app/app/page.tsx`.
- El edit compila limpio (tsc sin errores en page.tsx; fallos pre-existentes solo en __tests__).
- Calidad imperfecta: anidó Link dentro del div en vez de reemplazarlo. El turno igual falló: tras escribir siguió leyendo en vez de verificar+cerrar; el harness reportó "no logró escribir" aunque el archivo quedó modificado.
- Conclusión: el 1.7B PUEDE operar tools; el problema es convergencia/cierre, no mecánica. V7 enseña close-the-loop.

## V7 (close-the-loop trajs)
- Datos: 26 ejemplos en texto. 2 epochs, LR 5e-5.
- **Run narrow con V7 GGUF**: el modelo llamó run_build DOS veces SIN escribir antes. El harness marcó "Turno completado (verificación exitosa, sin cambios en disco)" — falso positivo, la tarea pedía un cambio y no hay diff.
- Patrón: V6 escribía sin verificar; V7 verifica sin escribir. El SFT con 3-6 trajs por iteración sobreajusta al último fallo (whack-a-mole). V8 debe ser una sola corrida diversa que cubra el árbol completo.
- Detalle: V7 escribió `<Link to=...>` (sintaxis React Router) en su plan; Next.js usa `href=`. Corregir en datos.

## V8 (31 ejemplos, 3 epochs, full-text loss)
- Rubric Q&A: 29/40. Tool-eval: 5/6.
- **Run narrow con V8 GGUF: REGRESIÓN** — 0 tool calls, loop repitiendo texto, emite basura del template (`</think>`). Causa: el loss sobre el texto completo enseña a copiar boilerplate del chat template.
- Fix (V9): misma data V8 + `DataCollatorForCompletionOnlyLM("<|Bot|>")` para entrenar solo sobre respuestas del asistente.

## V9 (misma data V8 + completion-only loss sobre <|Bot|>)
- Tool-eval: 5/6 (igual). **Run narrow con V9: 0 tool calls, loop de texto** — igual que V8. El masking no transfirió al harness.
- Hipótesis principal: mismatch de distribución de contexto — entrenamos en 200-1000 tokens, el harness inyecta 12-40k (system + preloads + historial). El modelo nunca vio contextos largos en SFT.
- Siguiente: test decisivo con BASE sin LoRA en tarea angosta (¿el éxito de V6 fue training o varianza?).

## Test decisivo: BASE sin LoRA en tarea angosta → ÉXITO
- El base hizo read → edit_file (reemplazo correcto, href bien) → run_build → reportó. Turno: "Tarea realizada, verificación ✅". 346s.
- Conclusión: el SFT V4-V9 no aporta a tool-behavior; la varianza del prompt domina. El base ya sabía operar tools (tool-eval 5/6 desde el día 1).
- El SFT Q&A (V2-B/V4, 33/40) sirve para estilo conversacional, no para agencia. Se frena el loop SFT de trayectorias.
- Lo que funciona: prompts grounded y angostos (archivo + bloque + verificación explícitos). Lo abierto falla en exploración/convergencia: eso se arregla descomponiendo en el harness, no en el modelo.

## Matriz final (base vs fine-tunes × angosta vs abierta)
|  | Tarea angosta (archivo+bloque+verify) | Tarea abierta (dashboard Pacientes) |
|---|---|---|
| BASE | ✅ edit correcto + build + report (346s) | ❌ 4 reads, 0 writes |
| V6 | ⚠️ edit imperfecto, sin verify | ❌ loops de exploración |
| V7/V8/V9 | ❌ 0 tools / loops | — (no se probó, narrow ya fallaba) |

Veredicto: el 1.7B ejecuta sub-tareas grounded; las abiertas requieren
descomposición en el harness. Fin del loop SFT.

## Destilación con Intern-S2-Preview (Intern-S2-Preview-35B vía API remota)
- 12B local descartado: emite tool calls como texto (no estructurado) + 2.9 tok/s + prefill 9-11 min (timeouts del harness).
- Harness apuntado temporalmente a la API Intern (tmp commits: api key por env, bypass de health-checks locales, timeouts elevados).
- Tracer mejorado: recorder a nivel de stream (texto + calls + results en orden) + limpieza de calls alucinadas ("not a valid tool").
- 3 runs angostos con Intern-S2-Preview: 2 ✅ completos + 1 con edit perfecto pero turno "fallido" por mecánicas (verifys no bindeadas en algunos attempts). Todos escribieron bien.
- V10 = 13 Q&A V4 + 2 traces reales (5611 + 1689 tokens renderizados). max_length 8192, completion-only loss, 2 epochs.

## V10 (13 Q&A + 2 traces reales Intern-S2-Preview, completion-only, ctx 8k, 2 epochs)
- Tool-eval: 5/6. **Run narrow con V10 GGUF: ✅ TAREA COMPLETA** (read exacto → edit → run_build → verificación ✅). Primer fine-tune que cierra el loop.
- La destilación de traces reales con prompts de contexto largo SÍ transfiere, donde 30 ejemplos sintéticos no lo hicieron.

## V10 abierta: falla en exploración (20 calls, loop en marketing/, 0 writes)
- V10 angosta ✅, V10 abierta ❌. Los 2 traces reales eran de tareas angostas: enseñan mecánica, no exploración/recovery. Los trajs sintéticos V6 (recovery) habían quedado fuera de V10.
- V11 = 13 Q&A + 18 trajs sintéticos (V5-V8: mecánica, recovery, close-the-loop, href) + 2 traces reales.

## V11 (33 ej.: Q&A + 18 sintéticos + 2 reales, completion-only, ctx 4k)
- OOM en MPS con max_length 8192 (eager attention + KV del server compitiendo). Fix: comprimir textos/results verbosos (tool calls intactos) → max 3443 tokens, max_length 4096.
- **Run narrow V11**: pendiente de evaluar (server levantado).
- **Run abierta V11**: encontró el dashboard correcto (git_status → inspect_routes → app/app/page.tsx) pero loop de re-lecturas en marketing/, 0 writes.
- Limpieza agent-lucho: rama feature/trace-dump-v2 con solo el tracer (dumper + recorder); tmps revertidos.

## V11 narrow: ✅ TAREA COMPLETA (3 tool calls, verificación ✅)
- V11 = mejor modelo final: cierra tareas grounded, mejor orientación en abiertas (encuentra el dashboard) aunque las abiertas siguen sin cerrar.
- Veredicto final: destilación de traces reales >> SFT sintético. Tareas abiertas requieren descomposición en el harness.

## 4B baseline (XHToken/Spark-X2.5-4B, thinking OFF)
- Q&A rubric: 32/40 (vs 1.7B 31/40). Tool-eval: 6/6 perfecto (vs 1.7B 5/6).
- 4B-V1 plan: 32 ejemplos (V11 menos el trace de 3443 tokens que excede ctx 2048), completion-only, 2 epochs, LR 5e-5.

## 4B-V1 (32 ej., completion-only, ctx 2048, 2 epochs, LR 5e-5)
- Baseline 4B: 32/40 + tool 6/6. 4B-V1: 33/40 (+verificación 5/8) + tool 6/6.
- Entrenó en M1 16GB sin OOM (~1.5h, 22M params entrenables).

## 4B narrow control: BASE ✅ vs 4B-V1 ❌ (regresión)
- base-4B: read → read → edit_file → run_build → ✅ (M page.tsx, verificación verde).
- 4b-v1 (mismos datos V11): leyó líneas exactas, planificó en texto, NUNCA emitió el edit. Mismo patrón que 1.7B-V1.
- Hipótesis: el LoRA sobre Q&A+trajs cortos interfiere con el cierre agentico del 4B base (que ya era bueno: 6/6 tool-eval).

## 4B-V2 (13 Q&A + 5 turns destilados java/go/docker Intern-S2-Preview, completion-only, ctx 2560, 2 epochs)
- Entrenó en ~22 min una vez liberada la RAM (un llama-server zombie de 3.7GB causaba thrash). Loss 2.37, acc 61%.

## 4B-V2 barrió los 3 fallos (java/go/docker ✅; base era ❌❌❌)
- Q&A 33/40 + tool 6/6 (igual que V1). Real: java PASS (early-return), go test ok (byKey+mutex), docker 6/6 checks.
- 4B-V1 narrow ❌ vs base-4B narrow ✅: el LoRA sin destilación políglota regresó el cierre; V2 lo recupera.
- Pendiente: regresión php/db con V2 + radio 3-archivos (hipótesis sin medir).

## 4B-V3 (Q&A + java/go/docker/ts/python traces Intern-S2-Preview, completion-only con fix </think>, ctx 2560)
- Q&A: 30/40 (baja vs V2, irrelevante). Tool: 6/6.
- Real: TS ✅ (cura regresión V2, reemplazo exacto), python ✅ honesto (dict separado, no toca test).
- V3 = mejor modelo. Uso: tareas grounded 1-3 archivos; ver MATRIX.md (guía de uso con semáforos).
