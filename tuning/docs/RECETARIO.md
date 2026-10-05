# Recetario: convertir un SLM en asistente de código con LoRA en una MacBook Air

Cómo fine-tuneamos **Spark-X2.5-1.7B** para coding agentico con una M1 de 16GB,
qué funcionó, qué no, y los números de cada iteración.

## Punto de partida (baseline)

- **Modelo**: `XHToken/Spark-X2.5-1.7B` (arquitectura custom `Spark2_5ForCausalLM`,
  sliding-window híbrido, 1M de contexto nativo).
- **Hardware**: MacBook Air M1, 16GB RAM. Stack: `transformers + peft + trl` en MPS
  (MLX no soporta la arquitectura; QLoRA 4-bit no corre en MPS → LoRA bf16).
- **Baseline conversacional** (8 prompts de ingeniería, rubric propio):
  - Base + thinking ON (default del chat template): **20/40** — el modelo
    responde con meta-razonamiento ("We need to...").
  - Base + thinking OFF (`enable_thinking=false`): **31/40**.
  - Primera lección: **Spark es un modelo thinking**; el template default contamina
    las respuestas. El 11/40 de diferencia no es conocimiento, es formato.

## Iteraciones Q&A (LoRA r16, LR 5e-5 salvo V1)

| Versión | Datos | Epochs | Rubric | Held-out | Conclusión |
|---|---|---|---|---|---|
| V1 | 30 mixtos | 6, LR 1e-4 | 24/40 | — | Sobreajuste: conciso pero sin estructura |
| V2-A | 18 conceptos | 3 | 25/40 | — | Conceptos declarativos degradan formato |
| V2-B | 12 disciplina dev-senior | 3 | **33/40** | 27/35 | Lo único que mueve la aguja en Q&A |
| V3 | 12 + 10 conceptos | 3 | 24/40 | 21/35 | Conceptos en párrafo rompen formato |
| V4 | 13 disciplina estructurada | 3 | 32/40 | 28/35 | Empate con V2-B |

Lección: **enseñar comportamiento observable > enseñar conceptos**.
SOLID/DRY/OWASP como Q&A no transfiere; disciplina operacional sí.

## Iteraciones de trayectorias agent (con tool calls)

| Versión | Datos | Resultado en run real |
|---|---|---|
| V5 | 13 Q&A + 6 trajs | No escribe; mejores paths, loop de reads |
| V6 | + 4 trajs recovery | **Primera escritura real** en tarea angosta (imperfecta, sin verify) |
| V7 | + 3 trajs close-the-loop | Verifica sin escribir (falso "completado") |
| V8 | 31 ej., 3 epochs, full-text loss | 0 tools, loop, emite `</think>` (regresión) |
| V9 | misma data + completion-only loss | 0 tools, loop (no alcanzó) |

Lecciones:
- Iteraciones chicas (3-6 trajs) = **whack-a-mole**: cada una sobreajusta al
  último fallo (V6 escribe-sin-verificar → V7 verifica-sin-escribir).
- Full-text loss enseña a copiar boilerplate del template. El masking
  (completion-only) es obligatorio si entrenás sobre texto renderizado.
- `truncate_dataset` de trl revienta con columnas `messages` que tienen
  `tool_calls` anidados (pyarrow) → pre-renderizar a `text` con el chat template.

## El experimento decisivo

Misma tarea angosta (archivo + bloque + verificación explícitos):

- **V6/V8/V9**: 1 escritura imperfecta / loops / 0 tools.
- **BASE sin LoRA**: read → edit_file correcto (`href` bien, reemplazo limpio) →
  run_build → reportó. **Turno completado con verificación ✅.**

Conclusión honesta: **el SFT no le enseñó tool-behavior al modelo; el base ya
sabía** (tool-eval 5/6 desde el día 1). Lo que hace funcionar al 1.7B en el
harness son **prompts grounded y angostos**, no más LoRA. Las tareas abiertas
fallan en exploración/convergencia — eso se arregla descomponiendo en el
harness (sub-tareas de 1 archivo), no en el modelo.

## Receta reutilizable

1. Medí el base primero (rubric + tool-eval + 1 run real angosto). Sin baseline,
   no sabés si tu fine-tune ayuda.
2. Desactivá el thinking para respuestas directas (o actívalo solo donde pague).
3. Dataset chico y curado > dataset grande mediocre (12 buenos > 30 mezclados).
4. Entrená solo sobre respuestas del asistente (completion-only loss).
5. Evaluá checkpoints, no asumas que `final` gana (nuestro loss subió 2.76→3.05
   en la última epoch de V1).
6. Validá en el harness real: el rubric conversacional no predice agencia.
7. Si el base ya hace la tarea con buen prompt, no lo "arregles" con SFT.

## Destilación (lo que sí funcionó para agencia)
- 2-3 traces exitosos de un modelo fuerte (Intern-S2-Preview, 35B, con prompts reales de contexto
  largo > 30 ejemplos sintéticos.
- Tracer a nivel de stream (texto + calls + results en orden) en el harness;
  filtrar calls alucinadas ("not a valid tool").
- Comprimir verbosidad (textos, results largos) pero NUNCA los tool calls.
- Completion-only loss obligatorio; max_length según el trace más largo que
  quepa en VRAM (4k en M1 16GB con eager attention).
- Q&A de disciplina como ancla (13 ej.) + traces reales (2-3) > solo uno.

## Artefactos

- `scripts/`: `make_dataset*.py`, `train_lora.py`, `train_continue.py`,
  `eval.py`, `eval_tool.py`, `rubric.py`
- `data/`: datasets por versión + `eval_prompts*.jsonl` (held-out incluidos)
- Modelos GGUF Q4_K_M: `spark-v4` (mejor Q&A) y `spark-base` (mejor agente).
  Servir con llama.cpp: `llama-server -m models/spark-vX-Q4_K_M.gguf -c 65536
  -ngl 99 --flash-attn on --jinja ...`
