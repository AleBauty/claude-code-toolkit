"""
Red de seguridad de la regla de traspaso (METODOLOGIA.md §11).

Correr desde la raiz del repo:

    python3 tests/test_traspaso.py      (o: python tests/test_traspaso.py)

La regla vive en METODOLOGIA.md y, copiada tal cual, en cada agente que
produce analisis que otro consume. Copiada en 10 lugares, se desincroniza sola
si nadie la vigila: este test es el que la vigila.

Que cubre:
- El bloque entre los marcadores es IDENTICO en METODOLOGIA.md y en los 9
  agentes que lo llevan.
- Los 6 que no lo llevan (producen archivos del repo, no analisis) no lo tienen.
- revisor y seguridad tienen Write (para dejar su salida) y la nota de que
  alcance.py los limita a docs/<nombre>/.
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
AGENTES = RAIZ / ".claude/agents"
INICIO, FIN = "<!-- traspaso:inicio -->", "<!-- traspaso:fin -->"

LLEVAN = ["revisor", "seguridad", "qa", "requisitos", "ux-ui", "arquitecto",
          "gestion-entrega", "descubrimiento", "datos-analitica"]
NO_LLEVAN = ["backend", "frontend", "mobile", "base-datos", "infraestructura", "documentacion"]

fallos = []
total = 0


def chequear(cond: bool, msg: str):
    global total
    total += 1
    if not cond:
        fallos.append(msg)


def bloque(texto: str) -> str | None:
    m = re.search(re.escape(INICIO) + r"(.*?)" + re.escape(FIN), texto, re.S)
    return m.group(1).replace("\r\n", "\n").strip() if m else None


def main():
    chequear(sorted(LLEVAN + NO_LLEVAN) == sorted(p.stem for p in AGENTES.glob("*.md")),
             "la lista de agentes del test no coincide con .claude/agents/: actualizar LLEVAN/NO_LLEVAN")

    canon = bloque((RAIZ / "METODOLOGIA.md").read_text(encoding="utf-8"))
    chequear(canon is not None, "METODOLOGIA.md no tiene el bloque de traspaso entre marcadores")
    canon = canon or ""
    for palabra in ("docs/<tu-nombre>/", "Detalle:", "Conteo:", "no sirvió", "leé el archivo"):
        chequear(palabra in canon, f"el bloque de METODOLOGIA.md no menciona {palabra!r}")

    for a in LLEVAN:
        b = bloque((AGENTES / f"{a}.md").read_text(encoding="utf-8"))
        chequear(b is not None, f"{a}.md no tiene el bloque de traspaso")
        chequear(b == canon, f"{a}.md tiene el bloque distinto al de METODOLOGIA.md")
    for a in NO_LLEVAN:
        chequear(INICIO not in (AGENTES / f"{a}.md").read_text(encoding="utf-8"),
                 f"{a}.md tiene el bloque de traspaso y no deberia")

    for a in ("revisor", "seguridad"):
        texto = (AGENTES / f"{a}.md").read_text(encoding="utf-8")
        tools = re.search(r"^tools:(.*)$", texto, re.M)
        chequear(tools is not None and "Write" in tools.group(1), f"{a}.md no tiene Write")
        chequear("alcance.py" in texto and f"docs/{a}/" in texto,
                 f"{a}.md no dice que alcance.py lo limita a docs/{a}/")

    for f in fallos:
        print("FALLA", f)
    print(f"\n{total - len(fallos)}/{total} casos pasan" + (f" - {len(fallos)} FALLAN" if fallos else ""))
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
