"""
Red de seguridad de .claude/hooks/estado.py (SessionStart).

Correr desde la raiz del repo:

    python3 tests/test_estado.py      (o: python tests/test_estado.py)

estado.py inyecta en el contexto, al abrir la sesion (y en resume, clear y
compact), solo la seccion "Estado actual" de BITACORA.md. Lo que imprime con
exit 0 es lo que Claude ve.

Que cubre:
- Sin BITACORA.md, o con la seccion vacia (solo comentarios): no imprime
  nada, exit 0. No ensucia el contexto.
- Seccion normal: imprime solo el Estado actual, sin los comentarios HTML y
  sin nada de "Decisiones cerradas" ni del "Historico".
- Seccion de mas de 1500 caracteres: la corta y avisa (dentro de lo que
  Claude ve) que la bitacora no cumple la regla de 3 a 6 lineas.
- Formato de la bitacora de stocky (la que se escribio a mano antes de la
  plantilla): se lee igual. Datos inventados: este repo es publico.
- Hook roto (BITACORA.md ilegible o que es una carpeta): exit 1 con aviso.
  Es de calidad: nunca 2.
- Entrada por stdin rota: no le importa, no la necesita.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / ".claude/hooks/estado.py"
ENTRADA = json.dumps({"hook_event_name": "SessionStart", "source": "startup"})

fallos = []
total = 0


def chequear(cond: bool, msg: str):
    global total
    total += 1
    if not cond:
        fallos.append(msg)


def correr(proyecto: Path, entrada: str = ENTRADA) -> tuple[int, str, str]:
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}
    env["CLAUDE_PROJECT_DIR"] = str(proyecto)
    r = subprocess.run([sys.executable, str(HOOK)], input=entrada.encode("utf-8"),
                       capture_output=True, env=env)
    return (r.returncode, r.stdout.decode("utf-8", errors="replace"),
            r.stderr.decode("utf-8", errors="replace"))


def bitacora(estado: str) -> str:
    return ("# Bitacora — prueba\n\n## Estado actual\n\n" + estado +
            "\n\n## Decisiones cerradas\n\n- 2026-01-01 — DECISION-QUE-NO-VA\n\n"
            "## Historico\n\n### 2026-01-01 — algo\n\n- HISTORICO-QUE-NO-VA\n")


def main():
    if not HOOK.is_file():
        print(f"FALLA no existe {HOOK}")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as t:
        p = Path(t)

        # sin BITACORA.md
        codigo, out, err = correr(p)
        chequear(codigo == 0 and out.strip() == "", f"sin BITACORA.md: exit={codigo} out={out!a}")

        # seccion vacia (solo el comentario de la plantilla)
        (p / "BITACORA.md").write_text(bitacora("<!-- 3 a 6 lineas. Se REESCRIBE. -->"), encoding="utf-8")
        codigo, out, err = correr(p)
        chequear(codigo == 0 and out.strip() == "", f"seccion vacia: exit={codigo} out={out!a}")

        # seccion normal
        estado = ("<!-- comentario de la plantilla\n     en dos lineas -->\n"
                  "- Etapa: requisitos v6 revisados.\n- Esperando: decisión del dueño (ÍNDICE).")
        (p / "BITACORA.md").write_text(bitacora(estado), encoding="utf-8")
        codigo, out, err = correr(p)
        chequear(codigo == 0, f"seccion normal: exit={codigo} err={err!a}")
        chequear("- Etapa: requisitos v6 revisados." in out and "(ÍNDICE)" in out,
                 f"seccion normal: no imprime el estado tal cual: {out!a}")
        chequear("comentario" not in out and "<!--" not in out, f"seccion normal: imprime el comentario: {out!a}")
        chequear("DECISION-QUE-NO-VA" not in out and "HISTORICO-QUE-NO-VA" not in out,
                 f"seccion normal: imprime otras secciones: {out!a}")

        # stdin roto: no lo necesita
        codigo, out, err = correr(p, "{roto")
        chequear(codigo == 0 and "- Etapa:" in out, f"stdin roto: exit={codigo} out={out!a}")

        # mas de 1500 caracteres: corta y avisa
        largo = "\n".join(f"- linea {i}: " + "x" * 60 for i in range(40))   # ~2900 caracteres
        (p / "BITACORA.md").write_text(bitacora(largo), encoding="utf-8")
        codigo, out, err = correr(p)
        chequear(codigo == 0, f"seccion larga: exit={codigo}")
        chequear("- linea 0:" in out and "- linea 39:" not in out, "seccion larga: no la corto")
        chequear("3 a 6 lineas" in out, f"seccion larga: no avisa la regla dentro de lo que ve Claude: {out[-300:]!a}")
        chequear(len(out) < 2000, f"seccion larga: imprime {len(out)} caracteres")

        # formato de stocky: titulo, decisiones "- fecha — ...", historico "### fecha — ..."
        stocky = ("# Bitacora — sistema\n\n## Estado actual\n\n"
                  "- Etapa: spec escrita; **falta** aplicar la revision.\n"
                  "- **Esperando decisión del usuario:** 9 huecos.\n\n"
                  "## Decisiones cerradas\n\n- 2026-10-06 — PV-30: algo decidido.\n\n"
                  "## Historico\n\n### 2026-10-11 — Algo\n\n- Se hizo X.\n  - No sirvió: Y.\n")
        (p / "BITACORA.md").write_text(stocky, encoding="utf-8")
        codigo, out, err = correr(p)
        chequear(codigo == 0 and "**Esperando decisión del usuario:** 9 huecos." in out
                 and "PV-30" not in out and "No sirvió" not in out,
                 f"formato stocky: exit={codigo} out={out!a}")

        # hook roto: archivo ilegible (no UTF-8) -> aviso, exit 1, nunca 2
        (p / "BITACORA.md").write_bytes(b"## Estado actual\n\xff\xfe roto\n")
        codigo, out, err = correr(p)
        chequear(codigo == 1 and "AVISO" in err and "estado.py" in err,
                 f"BITACORA ilegible: exit={codigo} err={err!a}")

        # hook roto: BITACORA.md es una carpeta
        (p / "BITACORA.md").unlink()
        (p / "BITACORA.md").mkdir()
        codigo, out, err = correr(p)
        chequear(codigo == 1 and "AVISO" in err, f"BITACORA carpeta: exit={codigo} err={err!a}")

    for f in fallos:
        print("FALLA", f)
    print(f"\n{total - len(fallos)}/{total} casos pasan" + (f" - {len(fallos)} FALLAN" if fallos else ""))
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
