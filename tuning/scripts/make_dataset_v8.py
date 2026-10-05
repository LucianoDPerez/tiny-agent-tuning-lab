"""V8 trajectories: full decision tree in one diverse set.

Covers: write-before-verify (never verify a no-op as 'done' when a change
was requested), Next.js href (not `to`), search-first, read-once,
replace-don't-nest, verify-after-write, report+stop, empty-search recovery,
analysis-only, idempotency backend case.
"""
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
    # 1. Write BEFORE verify; a green build with no diff is NOT done when a change was requested
    traj(
        f"implementar: en {PAGE}, la card 'Esta semana' debe linkear a /app/agenda. Verificá con build.",
        [
            ("Leo el bloque exacto.", "read_file",
             {"path": PAGE, "start_line": 269, "end_line": 274},
             '        <div className="card-dashboard p-4">\n          <p className="text-sm font-medium text-gray-500">Esta semana</p>'),
            ("Primero el cambio, después la verificación: un build verde sin diff no cumple la tarea.", "edit_file",
             {"path": PAGE,
              "old_str": '        <div className="card-dashboard p-4">\n          <p className="text-sm font-medium text-gray-500">Esta semana</p>\n          <p className="text-2xl font-semibold text-gray-900">{weekCount}</p>\n          <p className="text-xs text-gray-400 mt-0.5">turnos</p>\n        </div>',
              "new_str": '        <Link href="/app/agenda" className="card-dashboard p-4 block cursor-pointer hover:border-gray-300 transition-colors">\n          <p className="text-sm font-medium text-gray-500">Esta semana</p>\n          <p className="text-2xl font-semibold text-gray-900">{weekCount}</p>\n          <p className="text-xs text-gray-400 mt-0.5">turnos</p>\n        </Link>'},
             "edit ok: 1 bloque reemplazado"),
            ("Ahora sí verifico el cambio.", "run_build", {"path": REPO}, "build exit=0"),
            ("Listo.\n\n1. `app/app/page.tsx`: card 'Esta semana' → Link href=\"/app/agenda\" (Next.js usa href, no to).\n2. Verificación: `run_build` exit=0 con el diff aplicado.\n\nVerificación: build verde. Fin.", None, None, None),
        ],
    ),
    # 2. Empty search -> broaden once -> dashboard -> write -> verify
    traj(
        f"implementar: en {REPO}, la card de 'Servicios activos' debe linkear a /app/configuracion/servicios. Verificá.",
        [
            ("Busco el texto.", "search_code",
             {"path": REPO, "pattern": "Servicios activos"},
             f"{PAGE}:277"),
            ("Leo el bloque.", "read_file",
             {"path": PAGE, "start_line": 274, "end_line": 280},
             '        <div className="card-dashboard p-4 col-span-2 sm:col-span-1">'),
            ("Reemplazo directo con href de Next.js.", "edit_file",
             {"path": PAGE,
              "old_str": '        <div className="card-dashboard p-4 col-span-2 sm:col-span-1">\n          <p className="text-sm font-medium text-gray-500">Servicios activos</p>',
              "new_str": '        <Link href="/app/configuracion/servicios" className="card-dashboard p-4 col-span-2 sm:col-span-1 block cursor-pointer hover:border-gray-300 transition-colors">\n          <p className="text-sm font-medium text-gray-500">Servicios activos</p>'},
             "edit ok: 1 bloque reemplazado"),
            ("Verifico con el cambio aplicado.", "run_build", {"path": REPO}, "build exit=0"),
            ("Listo.\n\n1. `app/app/page.tsx`: card → Link href=\"/app/configuracion/servicios\".\n2. Verificación: `run_build` exit=0.\n\nVerificación: build verde. Fin.", None, None, None),
        ],
    ),
    # 3. Backend idempotency: search, read, edit, verify, stop
    traj(
        f"implementar: en {REPO}, el POST de reservas duplica ante reintentos. Agregá clave de idempotencia y verificá.",
        [
            ("Busco el handler.", "search_code",
             {"path": REPO, "pattern": "export async function POST"},
             f"{REPO}/app/api/bookings/route.ts:12"),
            ("Leo el handler.", "read_file",
             {"path": REPO + "/app/api/bookings/route.ts", "start_line": 1, "end_line": 20},
             "export async function POST(req: Request) {\n  const body = await req.json();"),
            ("Agrego la clave antes de ejecutar la lógica.", "edit_file",
             {"path": REPO + "/app/api/bookings/route.ts",
              "old_str": "export async function POST(req: Request) {\n  const body = await req.json();",
              "new_str": "export async function POST(req: Request) {\n  const key = req.headers.get('X-Idempotency-Key');\n  const body = await req.json();"},
             "edit ok: 1 bloque reemplazado"),
            ("Verifico.", "run_build", {"path": REPO}, "build exit=0"),
            ("Listo.\n\n1. `app/api/bookings/route.ts`: lee `X-Idempotency-Key` (deduplicar con constraint único es el paso siguiente).\n2. Verificación: `run_build` exit=0.\n\nVerificación: build verde. Fin.", None, None, None),
        ],
    ),
    # 4. Analysis-only: explicitly zero writes, report
    traj(
        f"analizar: en {REPO}, ¿qué cards del dashboard ya son Links? No modifiques nada.",
        [
            ("Una sola búsqueda.", "search_code",
             {"path": REPO, "pattern": "card-dashboard p-4 block"},
             f"{PAGE}:428"),
            ("Resultado:\n\n1. Solo la card de próximos turnos (línea 428) es Link.\n2. Las 3 de métricas son divs: candidatas.\n3. Cero escrituras: la tarea es análisis.\n\nVerificación: no aplica escritura; análisis completo.", None, None, None),
        ],
    ),
    # 5. Small a11y fix: read once, edit, verify, stop
    traj(
        f"implementar: en {PAGE}, agregá title='Ver todos los turnos' al Link de 'Ver todos' (líneas ~404-407). Verificá.",
        [
            ("Leo el bloque.", "read_file",
             {"path": PAGE, "start_line": 403, "end_line": 408},
             '<Link href="/app/agenda" className="text-sm font-medium text-violet-600 hover:underline">'),
            ("Agrego el title con old_str copiado.", "edit_file",
             {"path": PAGE,
              "old_str": '<Link href="/app/agenda" className="text-sm font-medium text-violet-600 hover:underline">',
              "new_str": '<Link href="/app/agenda" title="Ver todos los turnos" className="text-sm font-medium text-violet-600 hover:underline">'},
             "edit ok: 1 bloque reemplazado"),
            ("Verifico.", "run_build", {"path": REPO}, "build exit=0"),
            ("Listo.\n\n1. `app/app/page.tsx`: title accesible agregado.\n2. Verificación: `run_build` exit=0.\n\nVerificación: build verde. Fin.", None, None, None),
        ],
    ),
]

with open("data/train_v8_traj.jsonl", "w", encoding="utf-8") as f:
    for t in TRAJS:
        f.write(json.dumps(t, ensure_ascii=False) + "\n")
print(f"Wrote {len(TRAJS)} -> data/train_v8_traj.jsonl")
