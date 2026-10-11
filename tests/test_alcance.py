"""
Red de seguridad de .claude/hooks/alcance.py.

Correr desde la raiz del repo:

    python3 tests/test_alcance.py      (o: python tests/test_alcance.py)

Ejecuta el hook real por subprocess con el JSON que manda Claude Code. Dentro
de un subagente, la entrada trae "agent_type" con el nombre de la cabecera del
agente (verificado en vivo el 2026-10-11: llego "revisor").

Que cubre:
- revisor y seguridad solo escriben dentro de docs/<su-nombre>/.
- Salir con "..", usar la carpeta de otro agente, o una ruta relativa que
  escapa: bloquea. Sin esto el hook es decorativo.
- En Windows: barras invertidas y mayusculas distintas no lo esquivan ni lo
  traban.
- La sesion principal (sin agent_type) y los demas agentes: no se tocan.
- Hook roto: bloquea (es de seguridad, falla cerrado).
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / ".claude/hooks/alcance.py"

fallos = []
total = 0


def chequear(cond: bool, msg: str):
    global total
    total += 1
    if not cond:
        fallos.append(msg)


def correr(proyecto: Path, entrada) -> subprocess.CompletedProcess:
    datos = entrada if isinstance(entrada, str) else json.dumps(entrada)
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}
    env["CLAUDE_PROJECT_DIR"] = str(proyecto)
    return subprocess.run([sys.executable, str(HOOK)], input=datos.encode("utf-8"),
                          capture_output=True, env=env)


def write(agente: str | None, ruta: str, herramienta: str = "Write") -> dict:
    e = {"hook_event_name": "PreToolUse", "tool_name": herramienta,
         "tool_input": {"file_path": ruta, "content": "x"}}
    if agente:
        e["agent_type"] = agente
    return e


def main():
    if not HOOK.is_file():
        print(f"FALLA no existe {HOOK}")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "mi proyecto"
        (p / "docs" / "revisor").mkdir(parents=True)
        P = str(p)
        sep = os.sep

        casos = [
            # (nombre, entrada, exit esperado)
            ("revisor en su carpeta", write("revisor", f"{P}{sep}docs{sep}revisor{sep}2026-10-11-login.md"), 0),
            ("revisor en subcarpeta propia", write("revisor", f"{P}/docs/revisor/anexos/a.md"), 0),
            ("seguridad en su carpeta", write("seguridad", f"{P}/docs/seguridad/hallazgos.md"), 0),
            ("revisor con Edit en su carpeta", write("revisor", f"{P}/docs/revisor/x.md", "Edit"), 0),
            ("revisor en src/", write("revisor", f"{P}{sep}src{sep}app.py"), 2),
            ("revisor sale con ..", write("revisor", f"{P}/docs/revisor/../../src/x.py"), 2),
            ("revisor en la carpeta de otro", write("revisor", f"{P}/docs/seguridad/x.md"), 2),
            ("revisor en docs/ suelto", write("revisor", f"{P}/docs/x.md"), 2),
            ("revisor con prefijo parecido", write("revisor", f"{P}/docs/revisor-otro/x.md"), 2),
            ("revisor fuera del proyecto", write("revisor", str(Path(t) / "afuera.md")), 2),
            ("revisor con ruta relativa que escapa", write("revisor", "../../x.py"), 2),
            ("seguridad en CLAUDE.md", write("seguridad", f"{P}/CLAUDE.md"), 2),
            ("revisor sin file_path", {"tool_name": "Write", "agent_type": "revisor",
                                       "tool_input": {"content": "x"}}, 2),
            ("sesion principal en src/", write(None, f"{P}/src/app.py"), 0),
            ("backend en src/", write("backend", f"{P}/src/app.py"), 0),
            ("qa en tests/", write("qa", f"{P}/tests/test_x.py"), 0),
        ]
        if os.name == "nt":
            otra = "D:" if P[:2].upper() != "D:" else "E:"
            # commonpath() revienta con rutas en unidades distintas: tiene que ser un
            # bloqueo normal, no "FALLO EL HOOK" (que invita a desactivarlo)
            for nombre in ("revisor en otra unidad", "seguridad en otra unidad"):
                agente = nombre.split()[0]
                entrada = write(agente, f"{otra}\\algo\\x.md")
                r = correr(p, entrada)
                err = r.stderr.decode("utf-8", errors="replace")
                chequear(r.returncode == 2 and "Bloqueado por alcance.py" in err
                         and "FALLO EL HOOK" not in err,
                         f"[{nombre}] exit={r.returncode}, tenia que ser un bloqueo normal: {err.strip()[:150]!a}")
            casos += [
                ("Windows: mayusculas distintas en su carpeta",
                 write("revisor", f"{P.upper()}\\DOCS\\Revisor\\x.md"), 0),
                ("Windows: mayusculas no esquivan", write("revisor", f"{P.upper()}\\SRC\\x.py"), 2),
            ]

        for nombre, entrada, esperado in casos:
            r = correr(p, entrada)
            err = r.stderr.decode("utf-8", errors="replace")
            chequear(r.returncode == esperado,
                     f"[{nombre}] esperado={esperado} obtenido={r.returncode} {err.strip()[:150]!a}")
            if esperado == 2 and r.returncode == 2:
                chequear("alcance.py" in err, f"[{nombre}] el mensaje no dice que fue alcance.py")

        # falla cerrado: entrada rota bloquea y dice que fallo el hook
        for nombre, entrada in (("JSON roto", "{roto"), ("raiz no es objeto", "[1]")):
            r = correr(p, entrada)
            err = r.stderr.decode("utf-8", errors="replace")
            chequear(r.returncode == 2 and "FALLO EL HOOK alcance.py" in err
                     and '"disableAllHooks": true' in err,
                     f"[falla cerrado: {nombre}] exit={r.returncode} {err.strip()[:150]!a}")

    for f in fallos:
        print("FALLA", f)
    print(f"\n{total - len(fallos)}/{total} casos pasan" + (f" - {len(fallos)} FALLAN" if fallos else ""))
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
