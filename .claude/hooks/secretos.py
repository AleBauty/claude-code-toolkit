#!/usr/bin/env python3
"""
Hook PreToolUse sobre Edit/Write: evita escribir credenciales en archivos.

Heuristica, no garantia: detecta los patrones mas comunes.
Exit 2 = bloquea.
"""
import json
import re
import sys
from pathlib import Path

# archivos donde SI pueden ir valores de ejemplo
PERMITIDOS = {".env.example", ".env.sample", "settings.json.example"}

PATRONES = [
    # el nombre puede tener prefijo (DB_PASSWORD, CLIENTE_API_KEY) o ir solo (KEY, TOKEN),
    # pero el patron tiene que cerrar justo antes del = para no marcar "keyboard ="
    (r"(?i)\b[a-z0-9]*[_-]?(api[_-]?key|key|secret|token|passwd|password|credential)\s*[:=]\s*[\"'][^\"'\s]{8,}[\"']",
     "credencial en texto plano"),
    (r"\bsk-[A-Za-z0-9_-]{16,}", "clave de API tipo sk-"),
    (r"\bghp_[A-Za-z0-9]{20,}", "token de GitHub"),
    (r"\bAKIA[0-9A-Z]{16}\b", "access key de AWS"),
    (r"-----BEGIN\s+(RSA|OPENSSH|EC|DSA|PGP)?\s*PRIVATE KEY-----", "clave privada"),
    (r"(?i)postgres(ql)?://[^:\s]+:[^@\s]+@", "connection string con contraseña"),
    (r"(?i)mongodb(\+srv)?://[^:\s]+:[^@\s]+@", "connection string con contraseña"),
]

# valores obviamente de ejemplo
EJEMPLOS = re.compile(
    r"(?i)(tu[-_]?clave|your[-_]?key|xxx+|<[^>]+>|cambiar|placeholder|example|ejemplo|dummy|fake|test123)"
)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    ti = data.get("tool_input") or {}
    ruta = ti.get("file_path") or ti.get("path") or ""
    if Path(ruta).name in PERMITIDOS:
        sys.exit(0)

    contenido = ti.get("content") or ti.get("new_string") or ""
    if not contenido:
        sys.exit(0)

    hallazgos = []
    for patron, motivo in PATRONES:
        for m in re.finditer(patron, contenido):
            if EJEMPLOS.search(m.group(0)):
                continue
            hallazgos.append(f"  {motivo}: {m.group(0)[:60]}")

    if hallazgos:
        print(
            "Posible credencial en " + (ruta or "el contenido") + ":\n\n"
            + "\n".join(hallazgos)
            + "\n\nLas credenciales van en .env (que esta en .gitignore).\n"
              "Si es un valor de ejemplo, usar un placeholder evidente "
              "(tu-clave, <API_KEY>).",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
