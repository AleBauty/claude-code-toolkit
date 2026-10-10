#!/usr/bin/env python3
"""
Hook PostToolUse: corre lint y typecheck despues de cada Edit/Write.

Detecta el tipo de proyecto y usa la herramienta que corresponda.

NO BLOQUEA: corre despues de la herramienta, el archivo ya quedo escrito.
Exit 2 = le devuelve el error a Claude para que lo corrija.
Exit 1 = no se pudo verificar (timeout, la herramienta no corrio): Claude Code
         lo muestra como aviso, sin frenar nada.
Exit 0 = todo bien.

No es un hook de seguridad: ante un JSON invalido sale con 0.

Configurar en .claude/settings.json (ver settings.json.example).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

TIMEOUT = 120


def leer_entrada():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def archivo_editado(data):
    ti = data.get("tool_input") or {}
    return ti.get("file_path") or ti.get("path") or ""


def raiz_del_proyecto(data):
    """CLAUDE_PROJECT_DIR primero: el cwd de la sesion puede ser un subdirectorio,
    y desde ahi no se ve package.json ni pyproject.toml."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or Path.cwd())


def correr(cmd, cwd):
    """(codigo, salida). codigo None = no se pudo verificar; salida dice por que."""
    try:
        r = subprocess.run(
            cmd, cwd=cwd, shell=True,
            capture_output=True, text=True, timeout=TIMEOUT,
        )
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return None, f"no termino en {TIMEOUT} s"
    except Exception as e:
        return None, f"no se pudo correr: {type(e).__name__}: {e}"


def existe(raiz, *nombres):
    return any((raiz / n).exists() for n in nombres)


def comandos_para(raiz, archivo):
    """Devuelve [(descripcion, comando)] segun el proyecto y el archivo tocado."""
    ext = Path(archivo).suffix.lower()
    cmds = []

    # --- JavaScript / TypeScript ---
    if ext in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"} and existe(raiz, "package.json"):
        try:
            pkg = json.loads((raiz / "package.json").read_text(encoding="utf-8"))
            scripts = pkg.get("scripts", {})
        except Exception:
            scripts = {}
        if "lint" in scripts:
            cmds.append(("lint", "npm run lint --silent"))
        if existe(raiz, "tsconfig.json"):
            cmds.append(("typecheck", "npx --no-install tsc --noEmit"))

    # --- Python ---
    elif ext == ".py":
        if existe(raiz, "pyproject.toml", "ruff.toml", ".ruff.toml"):
            cmds.append(("ruff", f'ruff check "{archivo}"'))
        usa_mypy = existe(raiz, "mypy.ini", ".mypy.ini")
        if not usa_mypy and existe(raiz, "pyproject.toml"):
            try:
                usa_mypy = "mypy" in (raiz / "pyproject.toml").read_text(
                    encoding="utf-8", errors="ignore")
            except Exception:
                usa_mypy = False
        if usa_mypy:
            cmds.append(("mypy", f'mypy "{archivo}"'))

    # --- Go ---
    elif ext == ".go" and existe(raiz, "go.mod"):
        cmds.append(("vet", "go vet ./..."))

    # --- Rust ---
    elif ext == ".rs" and existe(raiz, "Cargo.toml"):
        cmds.append(("clippy", "cargo clippy --quiet"))

    return cmds


def main():
    data = leer_entrada()
    archivo = archivo_editado(data)
    if not archivo:
        sys.exit(0)

    raiz = raiz_del_proyecto(data)
    problemas = []
    avisos = []

    for desc, cmd in comandos_para(raiz, archivo):
        codigo, salida = correr(cmd, raiz)
        if codigo is None:
            avisos.append(f"[{desc}] {cmd}: {salida}")
        elif codigo != 0 and salida.strip():
            problemas.append(f"[{desc}] {cmd}\n{salida.strip()[:3000]}")

    if problemas:
        print(
            "Verificacion fallida tras editar " + archivo + "\n\n"
            + "\n\n".join(problemas)
            + "\n\nCorregir antes de continuar.",
            file=sys.stderr,
        )
        sys.exit(2)       # devuelve el error a Claude

    # verificar.py es un control de CALIDAD, no de seguridad: avisa pero no
    # bloquea. Sale con 1 porque Claude Code muestra el stderr de un exit 1 como
    # aviso; con 0 el mensaje no lo ve nadie. proteger.py y secretos.py son
    # controles de SEGURIDAD y hacen lo contrario: fallan cerrado con 2. No
    # unificar los dos criterios.
    if avisos:
        print(
            "AVISO: no se pudo verificar " + archivo + " (no bloquea)\n\n"
            + "\n".join(avisos),
            file=sys.stderr,
        )
        sys.exit(1)       # aviso visible, sin bloquear

    sys.exit(0)


if __name__ == "__main__":
    main()
