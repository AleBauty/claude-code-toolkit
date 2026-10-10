"""
Red de seguridad de .claude/hooks/verificar.py.

Correr desde la raiz del repo:

    python3 tests/test_verificar.py      (o: python tests/test_verificar.py)

Importa el hook y llama a sus funciones: lo que se prueba no depende de que
haya npm, ruff o mypy instalados.

Que cubre:
- RAIZ: usa CLAUDE_PROJECT_DIR; si no esta, el "cwd" del JSON; si tampoco, el
  directorio actual. Con el cwd como raiz, desde un subdirectorio no encuentra
  package.json ni pyproject.toml y no verifica nada, en silencio.
- TIMEOUT: si un comando no termina, el hook avisa por stderr y sale con 1
  (Claude Code lo muestra como aviso, sin bloquear). Antes salia con 0 y nadie
  se enteraba de que no se habia verificado.
- Un error real de lint sigue saliendo con 2.
"""
import contextlib
import io
import json
import os
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent / ".claude/hooks"
sys.path.insert(0, str(HOOKS))
import verificar  # noqa: E402

fallos = []
total = 0


def chequear(cond: bool, msg: str):
    global total
    total += 1
    if not cond:
        fallos.append(msg)


def correr_main(entrada: dict) -> tuple[int, str]:
    """Corre verificar.main() con `entrada` como stdin; devuelve (exit, stderr)."""
    err = io.StringIO()
    stdin_orig = sys.stdin
    sys.stdin = io.StringIO(json.dumps(entrada))
    try:
        with contextlib.redirect_stderr(err):
            verificar.main()
        codigo = 0
    except SystemExit as e:
        codigo = e.code if isinstance(e.code, int) else 1
    finally:
        sys.stdin = stdin_orig
    return codigo, err.getvalue()


def con_env(valor: str | None):
    if valor is None:
        os.environ.pop("CLAUDE_PROJECT_DIR", None)
    else:
        os.environ["CLAUDE_PROJECT_DIR"] = valor


def main():
    original_env = os.environ.get("CLAUDE_PROJECT_DIR")
    original_cmds, original_timeout = verificar.comandos_para, verificar.TIMEOUT
    try:
        # --- raiz del proyecto ---
        con_env("/proyecto/real")
        r = verificar.raiz_del_proyecto({"cwd": "/proyecto/real/src/sub"})
        chequear(r == Path("/proyecto/real"), f"con CLAUDE_PROJECT_DIR, raiz={r}")

        con_env(None)
        r = verificar.raiz_del_proyecto({"cwd": "/otro"})
        chequear(r == Path("/otro"), f"sin CLAUDE_PROJECT_DIR, raiz={r} (esperado el cwd)")

        r = verificar.raiz_del_proyecto({})
        chequear(r == Path.cwd(), f"sin nada, raiz={r} (esperado el directorio actual)")

        # --- timeout: avisa y sale con 1 ---
        verificar.TIMEOUT = 1
        lento = f'"{sys.executable}" -c "import time; time.sleep(10)"'
        verificar.comandos_para = lambda raiz, archivo: [("lento", lento)]
        codigo, err = correr_main({"tool_input": {"file_path": "x.py"}, "cwd": "."})
        chequear(codigo == 1, f"timeout: exit={codigo}, esperado 1")
        chequear("no termino" in err and "lento" in err,
                 f"timeout: el aviso no dice que paso: {err.strip()[:150]!r}")

        # --- un error real sigue bloqueando ---
        falla = f'"{sys.executable}" -c "import sys; print(\'E501 linea larga\'); sys.exit(1)"'
        verificar.comandos_para = lambda raiz, archivo: [("lint", falla)]
        codigo, err = correr_main({"tool_input": {"file_path": "x.py"}, "cwd": "."})
        chequear(codigo == 2 and "E501" in err, f"error de lint: exit={codigo}, esperado 2")

        # --- todo bien: 0 y en silencio ---
        bien = f'"{sys.executable}" -c "pass"'
        verificar.comandos_para = lambda raiz, archivo: [("lint", bien)]
        codigo, err = correr_main({"tool_input": {"file_path": "x.py"}, "cwd": "."})
        chequear(codigo == 0 and not err.strip(), f"todo bien: exit={codigo} stderr={err!r}")
    finally:
        verificar.comandos_para, verificar.TIMEOUT = original_cmds, original_timeout
        con_env(original_env)

    for f in fallos:
        print("FALLA", f)
    print(f"\n{total - len(fallos)}/{total} casos pasan"
          + (f" - {len(fallos)} FALLAN" if fallos else ""))
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
