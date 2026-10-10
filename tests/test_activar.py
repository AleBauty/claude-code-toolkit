"""
Red de seguridad de activar-hooks.py, en una copia de la caja en un directorio temporal.

Correr desde la raiz del repo:

    python3 tests/test_activar.py      (o: python tests/test_activar.py)

Que cubre:
- activar-hooks.py prueba solo que proteger.py bloquee, y lo informa. Antes
  imprimia un comando para copiar que no funcionaba: tenia "rm -rf" escrito,
  asi que el propio hook lo bloqueaba, y usaba una ruta relativa.
- Ninguna instruccion impresa por activar-hooks.py o nuevo.py lleva un comando
  con el patron destructivo en linea.
- Si proteger.py no bloquea, activar-hooks.py lo dice y sale con 1.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PATRON_RM = re.compile(r"\brm\s+-[a-zA-Z]*[rf]")

fallos = []
total = 0


def chequear(cond: bool, msg: str):
    global total
    total += 1
    if not cond:
        fallos.append(msg)


def copia_de_la_caja(tmp: Path) -> Path:
    caja = tmp / "caja con espacios"
    shutil.copytree(RAIZ / ".claude/hooks", caja / ".claude/hooks",
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(RAIZ / ".claude/settings.json.example", caja / ".claude/settings.json.example")
    shutil.copy2(RAIZ / "activar-hooks.py", caja / "activar-hooks.py")
    return caja


def activar(caja: Path, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(caja / "activar-hooks.py")], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def main():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as t:
        tmp = Path(t)
        caja = copia_de_la_caja(tmp)

        # 1. corre la prueba y la informa, aunque se lo llame desde otro directorio
        r = activar(caja, cwd=tmp)
        salida = r.stdout + r.stderr
        chequear(r.returncode == 0, f"activar-hooks.py salio con {r.returncode}: {salida[-300:]!a}")
        chequear("OK: proteger.py bloquea" in salida, f"no informa la prueba: {salida[-300:]!a}")
        chequear((caja / ".claude/settings.json").is_file(), "no escribio settings.json")

        # 2. nada para copiar con el patron destructivo en linea
        chequear(not PATRON_RM.search(salida),
                 f"activar-hooks.py imprime un comando con el patron en linea: {salida!a}")

        # 3. si proteger.py no bloquea, lo dice y sale con 1
        (caja / ".claude/hooks/proteger.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
        r = activar(caja, cwd=tmp)
        salida = r.stdout + r.stderr
        chequear(r.returncode == 1 and "FALLA" in salida,
                 f"con un proteger.py roto: exit={r.returncode}, salida={salida[-300:]!a}")

        # 4. nuevo.py tampoco imprime el comando roto
        destino = tmp / "sistema"
        r = subprocess.run([sys.executable, str(RAIZ / "nuevo.py"), str(destino)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        salida = r.stdout + r.stderr
        chequear(r.returncode == 0, f"nuevo.py fallo: {salida[-300:]!a}")
        chequear(not PATRON_RM.search(salida),
                 f"nuevo.py imprime un comando con el patron en linea: {salida[-400:]!a}")
        chequear("OK: proteger.py bloquea" in salida, f"nuevo.py no informa la prueba: {salida[-300:]!a}")

    for f in fallos:
        print("FALLA", f)
    print(f"\n{total - len(fallos)}/{total} casos pasan"
          + (f" - {len(fallos)} FALLAN" if fallos else ""))
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
