"""V6 trajectories: recovery + no-repeat-reads discipline.

New failure modes to fix (from V5 real run):
- search returns empty -> broaden pattern ONCE, then read the known dashboard file directly
- never read the same path twice; never read a directory path
- max 3 reads, then edit; verify; report and stop
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
    # 1. Search empty -> broaden once -> read dashboard directly -> edit
    traj(
        f"implementar: en el dashboard del profesional ({REPO}) hay una card que muestra la cantidad de pacientes (texto 'Pacientes'). Hacela clickeable a /app/clientes con cursor pointer y hover. Verificá con build.",
        [
            ("Busco la card por su texto.", "search_code",
             {"path": REPO, "pattern": "Pacientes"},
             "(sin resultados)"),
            ("No hay 'Pacientes' literal; el dominio usa 'clientes'. Busco eso una vez.", "search_code",
             {"path": REPO, "pattern": "clientes"},
             f"{PAGE}: dashboard; {REPO}/app/app/clientes/page.tsx: página de clientes"),
            ("Leo el dashboard una sola vez para ubicar las cards de métricas.", "read_file",
             {"path": PAGE, "start_line": 255, "end_line": 280},
             '<div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">... cards de métricas ...'),
            ("Agrego la card 'Clientes' clickeable siguiendo el patrón Link del repo, sin releer nada.", "edit_file",
             {"path": PAGE,
              "old_str": '        <div className="card-dashboard p-4">\n          <p className="text-sm font-medium text-gray-500">Hoy</p>',
              "new_str": '        <Link href="/app/clientes" className="card-dashboard p-4 block cursor-pointer hover:border-gray-300 transition-colors">\n          <p className="text-sm font-medium text-gray-500">Clientes</p>'},
             "edit ok: 1 bloque reemplazado"),
            ("Verifico.", "run_build", {"path": REPO}, "build exit=0"),
            ("Listo.\n\n1. `app/app/page.tsx`: card 'Clientes' clickeable → /app/clientes (cursor-pointer + hover).\n2. Nota: no existía card 'Pacientes'; el dominio usa 'clientes'.\n3. Verificación: `run_build` exit=0.\n\nVerificación: build verde.", None, None, None),
        ],
    ),
    # 2. Never re-read: read once, act
    traj(
        f"implementar: en {REPO}, hacé que el link 'Ver todos' de próximos turnos use estilo underline solo en hover (ya existe) y agregá título accesible. Verificá.",
        [
            ("Ubico el link.", "search_code",
             {"path": REPO, "pattern": "Ver todos"},
             f"{PAGE}:405: Ver todos"),
            ("Leo el bloque una vez.", "read_file",
             {"path": PAGE, "start_line": 402, "end_line": 408},
             '<Link href="/app/agenda" className="text-sm font-medium text-violet-600 hover:underline">\n            Ver todos\n          </Link>'),
            ("Agrego el título accesible con el old_str copiado de la lectura. No releo.", "edit_file",
             {"path": PAGE,
              "old_str": '<Link href="/app/agenda" className="text-sm font-medium text-violet-600 hover:underline">',
              "new_str": '<Link href="/app/agenda" title="Ver todos los turnos" className="text-sm font-medium text-violet-600 hover:underline">'},
             "edit ok: 1 bloque reemplazado"),
            ("Verifico.", "run_build", {"path": REPO}, "build exit=0"),
            ("Listo.\n\n1. `app/app/page.tsx`: título accesible en 'Ver todos'.\n2. Una sola lectura, un solo edit.\n3. Verificación: `run_build` exit=0.\n\nVerificación: build verde.", None, None, None),
        ],
    ),
    # 3. Directory is not a file: list, don't read
    traj(
        f"analizar: en {REPO}, ¿qué hay bajo app/app/clientes/?",
        [
            ("Listo el directorio (nunca se lee un directorio con read_file).", "search_code",
             {"path": REPO + "/app/app/clientes", "pattern": "page"},
             f"{REPO}/app/app/clientes/page.tsx; {REPO}/app/app/clientes/[clientId]/page.tsx"),
            ("Leo la página de clientes una vez.", "read_file",
             {"path": REPO + "/app/app/clientes/page.tsx", "start_line": 1, "end_line": 40},
             '"use client"; ... lista de clientes ...'),
            ("Estructura:\n\n1. `app/app/clientes/page.tsx`: lista de clientes.\n2. `app/app/clientes/[clientId]/page.tsx`: detalle.\n3. No modifiqué nada, era análisis.\n\nVerificación: lectura directa, sin reintentos.", None, None, None),
        ],
    ),
    # 4. Stop rule: 3 reads max, then write or report
    traj(
        f"implementar: en {REPO}, cambiá el heading 'Inicio' del dashboard por 'Panel' y verificá.",
        [
            ("Ubico el heading.", "search_code",
             {"path": REPO, "pattern": ">Inicio<"},
             f"{PAGE}:257: <h1>Inicio</h1>"),
            ("Leo el bloque.", "read_file",
             {"path": PAGE, "start_line": 256, "end_line": 260},
             '<h1 className="text-xl font-semibold text-gray-900">Inicio</h1>'),
            ("Cambio mínimo con old_str copiado.", "edit_file",
             {"path": PAGE,
              "old_str": '<h1 className="text-xl font-semibold text-gray-900">Inicio</h1>',
              "new_str": '<h1 className="text-xl font-semibold text-gray-900">Panel</h1>'},
             "edit ok: 1 bloque reemplazado"),
            ("Verifico.", "run_build", {"path": REPO}, "build exit=0"),
            ("Listo.\n\n1. `app/app/page.tsx`: 'Inicio' → 'Panel'.\n2. Dos lecturas totales (search + read), un edit.\n3. Verificación: `run_build` exit=0.\n\nVerificación: build verde.", None, None, None),
        ],
    ),
]

with open("data/train_v6_traj.jsonl", "w", encoding="utf-8") as f:
    for t in TRAJS:
        f.write(json.dumps(t, ensure_ascii=False) + "\n")
print(f"Wrote {len(TRAJS)} -> data/train_v6_traj.jsonl")
