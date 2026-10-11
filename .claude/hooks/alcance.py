#!/usr/bin/env python3
"""
Hook PreToolUse sobre Edit/Write: revisor y seguridad solo escriben en
docs/<su-nombre>/.

Esos dos agentes tienen Write para dejar su salida completa en un archivo
(regla de traspaso, METODOLOGIA.md §11), no para editar codigo: el revisor no
escribe lo que revisa. Sin este hook esa separacion era una promesa de texto.

Como sabe quien escribe: dentro de un subagente, la entrada trae "agent_type"
con el nombre de la cabecera del agente (no el del archivo). Verificado en vivo
el 2026-10-11: llego "revisor". En la sesion principal no viene, y el hook no
hace nada. Los demas agentes tampoco se tocan.

La ruta se compara ya resuelta (sin "..", barras y mayusculas normalizadas en
Windows): "docs/revisor/../../src/x.py" no pasa.

LIMITE CONOCIDO: solo cubre Edit y Write. Esos dos agentes tambien tienen Bash
y podrian escribir por ahi. No se cierra a proposito: el riesgo real es un
revisor que edita codigo por error, y para eso usa Write; cerrar Bash rompe
los greps y los tests que necesitan.

COSTO: un hook mas en cada Edit y Write (~0,5 s, casi todo arrancar Python),
para proteger a 2 de 15 agentes. Si en el uso diario molesta, el arreglo es
FUSIONAR este chequeo con secretos.py (que ya corre en Edit|Write), NO sacarlo.

FALLA CERRADO, como proteger.py y secretos.py: si el hook mismo se rompe sale
con 2. La salida de un bloqueo por bug va en el propio mensaje.
"""
import json
import os
import sys
from pathlib import Path

# agente -> carpeta donde puede escribir, relativa a la raiz del proyecto
RESTRINGIDOS = {"revisor": "docs/revisor", "seguridad": "docs/seguridad"}


def normal(p: Path) -> str:
    # resolve() saca los ".." y sigue enlaces; normcase iguala barras y
    # mayusculas en Windows (en Linux/Mac no cambia nada)
    return os.path.normcase(str(p.resolve()))


def adentro(ruta: Path, carpeta: Path) -> bool:
    r, c = normal(ruta), normal(carpeta)
    try:
        return os.path.commonpath([r, c]) == c
    except ValueError:
        # sin raiz comun (en Windows, otra unidad: D:\ contra C:\): esta afuera.
        # Es un bloqueo normal, no un fallo del hook: un "FALLO EL HOOK" aca
        # haria creer que el hook esta roto e invitaria a desactivarlo.
        return False


def main():
    # UTF-8 explicito en las dos puntas: Claude Code manda y lee UTF-8.
    # Detalle: SETUP.md del repo claude-code-toolkit.
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    data = json.loads(sys.stdin.buffer.read().decode("utf-8"))  # invalido: fallar_cerrado()

    agente = data.get("agent_type")
    if agente not in RESTRINGIDOS:
        sys.exit(0)

    proyecto = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
    permitido = proyecto / RESTRINGIDOS[agente]
    ruta = (data.get("tool_input") or {}).get("file_path") or ""

    destino = Path(ruta)
    if not destino.is_absolute():
        destino = Path(data.get("cwd") or os.getcwd()) / destino

    if ruta and adentro(destino, permitido):
        sys.exit(0)

    print(
        f"Bloqueado por alcance.py: el agente {agente} solo escribe en "
        f"{RESTRINGIDOS[agente]}/ (su salida de traspaso), no en el resto del repo.\n\n"
        f"  Intento: {ruta or '(sin file_path)'}\n\n"
        "Si encontraste algo para corregir, anotalo en tu archivo de traspaso: "
        "lo corrige el agente que corresponde.",
        file=sys.stderr,
    )
    sys.exit(2)


def fallar_cerrado(error: BaseException):
    print(
        f"FALLO EL HOOK alcance.py, no tu escritura: {type(error).__name__}: {error}\n"
        "El archivo no fue evaluado, y por seguridad se bloquea.\n"
        "Si pasa con cualquier Edit/Write, el hook tiene un bug. Para salir: fuera de "
        "Claude Code, poner {\"disableAllHooks\": true} en .claude/settings.local.json "
        "(se aplica sin reiniciar), arreglar el hook y despues sacar esa linea. "
        "Mientras tanto no hay ninguna proteccion.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        fallar_cerrado(e)
