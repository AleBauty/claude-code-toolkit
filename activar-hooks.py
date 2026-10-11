#!/usr/bin/env python3
"""
Activa los hooks en esta maquina: escribe .claude/settings.json a partir del
.example, con el interprete de Python que funciona aca.

settings.json no se versiona porque el interprete cambia de maquina a maquina
(python3 en Linux, python en muchos Windows). Uno equivocado no da error:
los hooks simplemente dejan de bloquear.

Uso:
    python3 activar-hooks.py      (o: python activar-hooks.py)
"""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent

sys.path.insert(0, str(AQUI / ".claude/hooks"))
from interprete import (  # noqa: E402
    detectar_interprete, error_sin_interprete, probar_hooks, settings_con_interprete,
)


def main():
    ejemplo = AQUI / ".claude/settings.json.example"
    if not ejemplo.is_file():
        print(f"ERROR: no existe {ejemplo}. Sin el ejemplo no hay de donde armar los hooks.")
        sys.exit(1)

    interprete = detectar_interprete()
    if interprete is None:
        print(error_sin_interprete())
        print("No escribo settings.json.")
        sys.exit(1)

    # probar ANTES de escribir: si no, queda un settings.json que afirma hooks
    # activos sin haberlo comprobado. Los hooks se llaman por ruta directa, no
    # necesitan settings.json para correr.
    ok, lineas = probar_hooks(AQUI, interprete)
    if not ok:
        print("\n".join(lineas))
        print("No escribo settings.json: los hooks de seguridad no protegen. "
              "Si ya habia uno, quedo como estaba.")
        sys.exit(1)

    destino = AQUI / ".claude/settings.json"
    destino.write_text(settings_con_interprete(ejemplo, interprete), encoding="utf-8")

    print(f"Hooks activados con: {interprete}")
    print(f"Escrito: {destino}")
    print("\n" + "\n".join(lineas))
    print("Para repetir la prueba, volver a correr este script.")


if __name__ == "__main__":
    main()
