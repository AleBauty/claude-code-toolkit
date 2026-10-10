#!/usr/bin/env python3
"""
Hook PreToolUse sobre Edit/Write: evita escribir credenciales en archivos.

Heurística, no garantía: detecta los patrones más comunes.
Exit 2 = bloquea.

LÍMITE CONOCIDO: solo revisa Edit y Write. Un archivo escrito desde Bash o
PowerShell (heredoc, `echo >`, `python -c`, `Set-Content`) NO pasa por acá.
No tiene solución completa con hooks: habría que interpretar cada comando de
shell para saber si escribe un archivo y qué escribe. Es un límite del
enfoque, no un bug. La red de fondo es .gitignore (.env) y revisar el diff
antes de cada commit.

FALLA CERRADO: si el hook mismo se rompe (JSON inválido, estructura inesperada,
cualquier excepción) sale con 2 y el mensaje dice que falló el hook, no el
archivo. Un exit 1 Claude Code lo toma como "no bloquear". La contracara: un
bug que rompe el hook siempre bloquea todo Edit/Write. Cómo salir de eso está
en SETUP.md ("Si un hook bloquea todo").
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
    # UTF-8 explicito en las dos puntas, no el default del entorno (en Windows,
    # cp1252): por que, en SETUP.md, "Codificación de los hooks"
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    data = json.loads(sys.stdin.buffer.read().decode("utf-8"))  # invalido: fallar_cerrado()

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


def fallar_cerrado(error: BaseException):
    print(
        f"FALLO EL HOOK secretos.py, no tu archivo: {type(error).__name__}: {error}\n"
        "El archivo no fue evaluado, y por seguridad se bloquea.\n"
        "Si esto pasa con cualquier Edit/Write, el hook tiene un bug: ver "
        "'Si un hook bloquea todo' en SETUP.md.",
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
