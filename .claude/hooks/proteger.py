#!/usr/bin/env python3
"""
Hook PreToolUse sobre Bash: bloquea comandos destructivos o peligrosos.

Exit 2 = bloquea. Exit 0 = deja pasar.
"""
import json
import re
import sys

# (patron, motivo)
REGLAS = [
    (r"\brm\s+(-[a-zA-Z]*\s+)*-[a-zA-Z]*[rf]", "borrado recursivo/forzado"),
    (r":\s*\(\s*\)\s*\{.*\|.*&.*\}\s*;", "fork bomb"),
    (r"\bmkfs\b",                      "formateo de disco"),
    (r"\bdd\s+.*of=/dev/",             "escritura directa a disco"),
    (r">\s*/dev/sd[a-z]",              "escritura directa a disco"),
    (r"\bchmod\s+(-R\s+)?777\b",       "permisos 777"),
    (r"DROP\s+(TABLE|DATABASE|SCHEMA)", "DROP de base de datos"),
    (r"TRUNCATE\s+TABLE",              "TRUNCATE de tabla"),
    (r"\bDELETE\s+FROM\s+\w+\s*(;|$)", "DELETE sin WHERE"),
    (r"\bgit\s+push\s+.*--force(?!-with-lease)", "push --force (usar --force-with-lease)"),
    (r"\bgit\s+reset\s+--hard\b",      "reset --hard descarta cambios sin recuperacion"),
    (r"\bgit\s+clean\s+-[a-zA-Z]*f",   "git clean borra archivos sin seguimiento"),
    (r"curl[^|]*\|\s*(sudo\s+)?(ba)?sh", "descargar y ejecutar directo"),
    (r"wget[^|]*\|\s*(sudo\s+)?(ba)?sh", "descargar y ejecutar directo"),
]


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cmd = (data.get("tool_input") or {}).get("command", "")
    if not cmd:
        sys.exit(0)

    for patron, motivo in REGLAS:
        if re.search(patron, cmd, re.IGNORECASE):
            print(
                f"Comando bloqueado: {motivo}\n\n"
                f"  {cmd}\n\n"
                "Si realmente hace falta, el usuario lo corre a mano "
                "o ajusta .claude/hooks/proteger.py",
                file=sys.stderr,
            )
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
