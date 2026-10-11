"""
Red de seguridad de nuevo.py: crea un repo de verdad y revisa lo que recibe.

Correr desde la raiz del repo:

    python3 tests/test_nuevo.py      (o: python tests/test_nuevo.py)

Que cubre:
- Que cada archivo que nuevo.py dice copiar exista en la caja. Si falta,
  nuevo.py lo saltea en silencio y el repo nace sin el.
- Que el repo generado tenga .env.example y que .env este ignorado.
- Que .herramientas-version describa el procedimiento de actualizacion vigente.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import nuevo  # noqa: E402

fallos = []
total = 0


def chequear(cond: bool, msg: str):
    global total
    total += 1
    if not cond:
        fallos.append(msg)


def main():
    # 1. lo que nuevo.py promete copiar existe en la caja
    for f in nuevo.COPIAR_FILES:
        chequear((RAIZ / f).is_file(), f"nuevo.py copia {f}, pero no existe en la caja")

    # 2. un repo generado de verdad
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        destino = Path(tmp) / "sistema_prueba"
        r = subprocess.run([sys.executable, str(RAIZ / "nuevo.py"), str(destino)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        chequear(r.returncode == 0, f"nuevo.py fallo: {r.stdout[-300:]} {r.stderr[-300:]}")

        chequear((destino / ".env.example").is_file(), "el repo generado no tiene .env.example")
        ignorado = subprocess.run(["git", "check-ignore", "-q", ".env"], cwd=destino)
        chequear(ignorado.returncode == 0, ".env no esta ignorado en el repo generado")

        # .herramientas-version: el procedimiento de actualizacion vigente, no el viejo
        version = (destino / ".herramientas-version").read_text(encoding="utf-8")
        chequear("copiar .claude/agents a mano" not in version,
                 ".herramientas-version tiene el procedimiento viejo (solo agentes)")
        for debe in ("actualizar.py", "activar-hooks.py", "settings.json.example"):
            chequear(debe in version, f".herramientas-version no menciona {debe}")

    for f in fallos:
        print("FALLA", f)
    print(f"\n{total - len(fallos)}/{total} casos pasan"
          + (f" - {len(fallos)} FALLAN" if fallos else ""))
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
