"""V7 trajectories: close the loop (write -> verify -> report -> STOP) + edit quality."""
import json

SYSTEM = (
    "Sos un dev senior / arquitecto de software. Antes de actuar, analizás: "
    "qué archivos y dependencias tocas, qué contratos rompes, qué patrones aplican "
    "(SOLID, DRY, KISS, idempotencia, deduplicación, backpressure, OWASP Top 10). "
    "Respondés directo al punto, sin divagar ni dar mil vueltas."
)

REPO = "/Users/luchop/PROYECTOS IA/TurnoSmart"
PAGE = REPO + "/app/app/page.tsx"


def tc(name, **args):
    return {"type": "function", "function": {"name": name, "arguments": args}}


def traj(task, steps):
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": task},
    ]
    for text, tname, targs, tresult in steps:
        msg = {"role": "assistant", "content": text or ""}
        if tname:
            msg["tool_calls"] = [tc(tname, **targs)]
        messages.append(msg)
        if tname:
            messages.append({"role": "tool", "content": tresult})
    return {"messages": messages}


TRAJS = [
    # 1. Full close-the-loop with quality edit (replace div with Link, keep grid classes)
    traj(
        f"implementar: en {PAGE}, la card 'Hoy' debe ser un Link a /app/clientes. Verificá con build y reportá.",
        [
            ("Leo el bloque exacto una vez.", "read_file",
             {"path": PAGE, "start_line": 264, "end_line": 270},
             '        <div className="card-dashboard p-4">\n          <p className="text-sm font-medium text-gray-500">Hoy</p>'),
            ("Reemplazo el div por Link manteniendo las clases de grid + cursor-pointer y hover. No nido Link dentro del div.", "edit_file",
             {"path": PAGE,
              "old_str": '        <div className="card-dashboard p-4">\n          <p className="text-sm font-medium text-gray-500">Hoy</p>\n          <p className="text-2xl font-semibold text-gray-900">{todayCount}</p>\n          <p className="text-xs text-gray-400 mt-0.5">turnos</p>\n        </div>',
              "new_str": '        <Link href="/app/clientes" className="card-dashboard p-4 block cursor-pointer hover:border-gray-300 transition-colors">\n          <p className="text-sm font-medium text-gray-500">Hoy</p>\n          <p className="text-2xl font-semibold text-gray-900">{todayCount}</p>\n          <p className="text-xs text-gray-400 mt-0.5">turnos</p>\n        </Link>'},
             "edit ok: 1 bloque reemplazado"),
            ("Después de escribir, verifico. No leo más archivos.", "run_build", {"path": REPO}, "build exit=0"),
            ("Listo.\n\n1. `app/app/page.tsx`: card 'Hoy' ahora es Link → /app/clientes (reemplazo directo, sin anidar).\n2. Verificación: `run_build` exit=0.\n\nVerificación: build verde. Nada más que hacer.", None, None, None),
        ],
    ),
    # 2. Verify fails -> fix once -> verify again -> stop
    traj(
        f"implementar: en {PAGE}, agregá title accesible al link 'Ver todos'. Verificá.",
        [
            ("Leo el bloque.", "read_file",
             {"path": PAGE, "start_line": 404, "end_line": 407},
             '<Link href="/app/agenda" className="text-sm font-medium text-violet-600 hover:underline">'),
            ("Agrego el title.", "edit_file",
             {"path": PAGE,
              "old_str": '<Link href="/app/agenda" className="text-sm font-medium text-violet-600 hover:underline">',
              "new_str": '<Link href="/app/agenda" title="Ver todos los turnos" className="text-sm font-medium text-violet-600 hover:underline">'},
             "edit ok: 1 bloque reemplazado"),
            ("Verifico.", "run_build", {"path": REPO}, "build exit=0"),
            ("Listo.\n\n1. `app/app/page.tsx`: title accesible agregado.\n2. Verificación: `run_build` exit=0.\n\nVerificación: build verde. Fin del turno.", None, None, None),
        ],
    ),
    # 3. Analysis-only task: no writes needed, report and stop (don't explore forever)
    traj(
        f"analizar: en {REPO}, ¿el dashboard usa Link de next/link para las cards? Respondé sin modificar nada.",
        [
            ("Busco el patrón una vez.", "search_code",
             {"path": REPO, "pattern": "card-dashboard p-4 block"},
             f"{PAGE}:428: className=\"card-dashboard p-4 block hover:border-gray-300 transition-colors\""),
            ("Sí.\n\n1. El dashboard usa `<Link>` con clases `card-dashboard p-4 block` (línea 428 de `app/app/page.tsx`).\n2. Las cards de métricas (líneas 264-280) todavía son `<div>`: candidatas a convertir.\n3. No modifiqué nada porque la tarea es análisis.\n\nVerificación: search ejecutado, cero escrituras a propósito.", None, None, None),
        ],
    ),
]

with open("data/train_v7_traj.jsonl", "w", encoding="utf-8") as f:
    for t in TRAJS:
        f.write(json.dumps(t, ensure_ascii=False) + "\n")
print(f"Wrote {len(TRAJS)} -> data/train_v7_traj.jsonl")
