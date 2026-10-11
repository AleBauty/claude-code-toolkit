#!/usr/bin/env python3
"""
Hook SessionStart: inyecta en el contexto la seccion "Estado actual" de
BITACORA.md, para que ninguna sesion arranque en blanco.

Corre en startup, resume, clear y compact. En SessionStart, lo que el hook
imprime con exit 0 es contexto que Claude ve. Se inyecta SOLO el Estado
actual (sin los comentarios HTML de la plantilla): las decisiones y el
historico se leen cuando alguien pregunta por algo viejo. Si no, la bitacora
seria un impuesto fijo de contexto en cada sesion.

- Sin BITACORA.md, o con la seccion vacia: no imprime nada, exit 0.
- Mas de TOPE caracteres: la corta y lo avisa dentro de lo que Claude ve, para
  que reescriba la seccion (la regla es 3 a 6 lineas).
- No usa stdin: lee la bitacora de la raiz del proyecto (CLAUDE_PROJECT_DIR).

Es de CALIDAD, no de seguridad: si se rompe, avisa con exit 1 y la sesion
arranca igual. Nunca 2.

El rastro mecanico de cada sesion (commits, archivos tocados) NO se escribe
con un hook: ya esta en git. Por que se descarto un hook Stop: ADR-001 en
datos/adr/ del repo claude-code-toolkit.
"""
import os
import re
import sys
from pathlib import Path

TOPE = 1500
TITULO = re.compile(r"^##\s+Estado actual\s*$", re.M)
SIGUIENTE = re.compile(r"^##\s", re.M)
COMENTARIO = re.compile(r"<!--.*?-->", re.S)


def estado_actual(texto: str) -> str:
    m = TITULO.search(texto)
    if not m:
        return ""
    resto = texto[m.end():]
    fin = SIGUIENTE.search(resto)
    seccion = resto[:fin.start()] if fin else resto
    seccion = COMENTARIO.sub("", seccion)
    return "\n".join(l.rstrip() for l in seccion.strip().splitlines() if l.strip())


def recortar(seccion: str) -> str:
    if len(seccion) <= TOPE:
        return seccion
    corte = seccion.rfind("\n", 0, TOPE)
    return (seccion[:corte if corte > 0 else TOPE] + "\n"
            f"[estado.py: recortado. La seccion tiene {len(seccion)} caracteres y la "
            f"regla es 3 a 6 lineas (tope {TOPE}). Reescribila: el Estado actual se "
            "reescribe, no se acumula; lo viejo va al Historico.]")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    proyecto = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    bitacora = proyecto / "BITACORA.md"
    if not bitacora.exists():
        sys.exit(0)

    try:
        seccion = estado_actual(bitacora.read_text(encoding="utf-8"))
    except Exception as e:
        # de calidad: avisa con 1, no bloquea con 2. La sesion arranca igual.
        print(f"AVISO: estado.py no pudo leer {bitacora}: {type(e).__name__}: {e}. "
              "La sesion arranca sin el Estado actual.", file=sys.stderr)
        sys.exit(1)

    if not seccion:
        sys.exit(0)
    print("Estado actual del trabajo (de BITACORA.md; las decisiones y el historico "
          "se leen solo si hacen falta):\n")
    print(recortar(seccion))
    sys.exit(0)


if __name__ == "__main__":
    main()
