"""
Red de seguridad de la configuracion de hooks (.claude/settings.json.example).

Correr desde la raiz del repo:

    python3 tests/test_settings.py      (o: python tests/test_settings.py)

Que cubre:
- Cada comando de hook apunta al script con "${CLAUDE_PROJECT_DIR}", entre
  comillas. Con una ruta relativa, si el directorio de trabajo de la sesion
  cambia, Python no encuentra el script, sale con 2 y Claude Code lo toma como
  bloqueo: quedan bloqueados todos los Bash, PowerShell, Edit y Write, sin un
  mensaje que explique la causa.
- Ejecuta cada comando como lo hace Claude Code (por un shell, con
  CLAUDE_PROJECT_DIR en el entorno) desde un subdirectorio, y desde una ruta
  con espacios. Un hook que no encuentra su script falla aca, no en la sesion.

Necesita bash (en Windows, el de Git: es el que usa Claude Code para los hooks).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EJEMPLO = RAIZ / ".claude/settings.json.example"

sys.path.insert(0, str(RAIZ / ".claude/hooks"))
from interprete import detectar_interprete, settings_con_interprete  # noqa: E402

# lo que recibe cada hook: una entrada que deja pasar y, si corresponde, una que bloquea
INOFENSIVO = {"tool_name": "Bash", "tool_input": {"command": "ls", "file_path": "x.txt",
                                                   "content": "hola"}}
DESTRUCTIVO = {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/x"}}

fallos = []


def bash() -> str | None:
    """bash de Git en Windows (no el de WSL de System32); el del PATH en el resto."""
    if os.name == "nt":
        git = shutil.which("git")
        if git:
            # ...\Git\cmd\git.exe -> ...\Git\bin\bash.exe
            cand = Path(git).resolve().parent.parent / "bin" / "bash.exe"
            if cand.is_file():
                return str(cand)
    return shutil.which("bash")


def comandos(cfg: dict) -> list[str]:
    return [h["command"] for grupos in cfg.get("hooks", {}).values()
            for g in grupos for h in g.get("hooks", [])]


def chequear(cond: bool, msg: str):
    if not cond:
        fallos.append(msg)


def correr(sh: str, cmd: str, proyecto: Path, cwd: Path, entrada: dict) -> subprocess.CompletedProcess:
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(proyecto))
    return subprocess.run([sh, "-c", cmd], cwd=cwd, env=env, input=json.dumps(entrada),
                          capture_output=True, text=True, encoding="utf-8", timeout=60)


def main():
    cfg = json.loads(EJEMPLO.read_text(encoding="utf-8"))
    cmds = comandos(cfg)
    chequear(len(cmds) == 3, f"se esperaban 3 hooks, hay {len(cmds)}")

    # 1. forma: ruta absoluta via la variable, entre comillas (espacios en la ruta)
    for c in cmds:
        chequear(re.search(r'"\$\{CLAUDE_PROJECT_DIR\}/\.claude/hooks/\w+\.py"', c) is not None,
                 f'no usa "${{CLAUDE_PROJECT_DIR}}/..." entre comillas: {c}')

    # 2. activar-hooks.py / nuevo.py cambian el interprete sin romper la ruta
    generado = json.loads(settings_con_interprete(EJEMPLO, "python"))
    for c in comandos(generado):
        chequear(c.startswith('python "${CLAUDE_PROJECT_DIR}/'),
                 f"settings generado con la ruta rota: {c}")

    # 3. ejecucion real desde un subdirectorio y desde una ruta con espacios
    sh = bash()
    interprete = detectar_interprete()
    if sh is None or interprete is None:
        print("AVISO: sin bash o sin Python funcional; salteo la ejecucion real.")
    else:
        reales = comandos(json.loads(settings_con_interprete(EJEMPLO, interprete)))
        with tempfile.TemporaryDirectory() as tmp:
            con_espacios = Path(tmp) / "mi proyecto"
            shutil.copytree(RAIZ / ".claude/hooks", con_espacios / ".claude/hooks",
                            ignore=shutil.ignore_patterns("__pycache__"))
            sub = con_espacios / "src" / "profundo"
            sub.mkdir(parents=True)

            for proyecto, cwd, nombre in ((RAIZ, sub, "subdirectorio"),
                                          (con_espacios, sub, "ruta con espacios")):
                for c in reales:
                    r = correr(sh, c, proyecto, cwd, INOFENSIVO)
                    chequear(r.returncode == 0,
                             f"[{nombre}] exit {r.returncode} con entrada inofensiva: {c}\n"
                             f"    {r.stderr.strip()[:200]}")
                prot = next(c for c in reales if "proteger.py" in c)
                r = correr(sh, prot, proyecto, cwd, DESTRUCTIVO)
                chequear(r.returncode == 2 and "borrado" in r.stderr,
                         f"[{nombre}] proteger.py no bloqueo rm -rf (exit {r.returncode})")

    for f in fallos:
        print("FALLA", f)
    print(f"\n{'OK' if not fallos else str(len(fallos)) + ' FALLAN'}: test_settings")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
