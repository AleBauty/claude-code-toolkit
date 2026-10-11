"""
Red de seguridad de nuevo.py: crea un repo de verdad y revisa lo que recibe.

Correr desde la raiz del repo:

    python3 tests/test_nuevo.py      (o: python tests/test_nuevo.py)

Que cubre:
- Que cada archivo que nuevo.py dice copiar exista en la caja. Si falta,
  nuevo.py lo saltea en silencio y el repo nace sin el.
- Que el repo generado tenga .env.example y que .env este ignorado.
- Que .herramientas-version describa el procedimiento de actualizacion vigente.
- Que nuevo.py VALIDE ANTES DE CREAR: con una fuente faltante (por ejemplo
  settings.json.example) sale con error, la nombra y no crea la carpeta
  destino. Antes creaba el repo sin hooks y salia con 0.
- Que un repo recien creado tenga settings.json y los 15 agentes.
- Que si git falla al leer la version de la caja, avise en vez de anotar
  "sin-git" en silencio.
"""
import shutil
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


def copia_de_la_caja(tmp: Path) -> Path:
    """La caja sin .git ni tests: nuevo.py usa su propia carpeta como origen."""
    caja = tmp / "caja"
    shutil.copytree(RAIZ, caja, ignore=shutil.ignore_patterns(
        ".git", "tests", "__pycache__", "INDICE-SISTEMAS.md", "settings.json"))
    return caja


def correr_nuevo(caja: Path, destino: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(caja / "nuevo.py"), str(destino)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def main():
    # 0. validar antes de crear: fuentes faltantes, cada una por separado
    faltantes = [".claude/settings.json.example", ".claude/agents", ".claude/hooks",
                 "METODOLOGIA.md", "datos/stack.csv"]
    for falta in faltantes:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as t:
            caja = copia_de_la_caja(Path(t))
            p = caja / falta
            shutil.rmtree(p) if p.is_dir() else p.unlink()
            destino = Path(t) / "sistema"
            codigo, salida = correr_nuevo(caja, destino)
            chequear(codigo != 0, f"sin {falta}: nuevo.py salio con 0")
            chequear(falta in salida.replace("\\", "/"), f"sin {falta}: el error no lo nombra: {salida[-200:]!a}")
            chequear(not destino.exists(), f"sin {falta}: creo la carpeta destino igual")

    # 0a. "tiene algo" no alcanza: tiene que tener lo que se espera. Una carpeta
    #     con solo __pycache__ (o sin los hooks que usa settings.json) no sirve.
    def dejar_solo(carpeta: Path, conservar: tuple[str, ...]):
        for p in carpeta.iterdir():
            if p.name not in conservar:
                shutil.rmtree(p) if p.is_dir() else p.unlink()
        (carpeta / "__pycache__").mkdir(exist_ok=True)
        (carpeta / "__pycache__" / "basura.pyc").write_bytes(b"\x00")

    huecos = {
        "agentes: solo __pycache__": (".claude/agents", (), ".claude/agents"),
        "hooks: solo interprete.py": (".claude/hooks", ("interprete.py",), "proteger.py"),
    }
    for nombre, (carpeta, conservar, nombrado) in huecos.items():
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as t:
            caja = copia_de_la_caja(Path(t))
            dejar_solo(caja / carpeta, conservar)
            destino = Path(t) / "sistema"
            codigo, salida = correr_nuevo(caja, destino)
            chequear(codigo != 0, f"{nombre}: nuevo.py salio con 0")
            chequear(nombrado in salida.replace("\\", "/"),
                     f"{nombre}: el error no nombra {nombrado}: {salida[-200:]!a}")
            chequear(not destino.exists(), f"{nombre}: creo la carpeta destino igual")

    # 0c. verificar.py roto: es de CALIDAD, no impide crear el repo. Avisa y sigue,
    #     igual que activar-hooks.py (test_activar). Si esto empieza a fallar,
    #     alguien lo trato como de seguridad.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as t:
        caja = copia_de_la_caja(Path(t))
        (caja / ".claude/hooks/verificar.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
        destino = Path(t) / "sistema"
        codigo, salida = correr_nuevo(caja, destino)
        chequear(codigo == 0 and (destino / ".claude/settings.json").is_file(),
                 f"verificar.py roto impidio crear el repo: exit={codigo} {salida[-250:]!a}")
        chequear("AVISO" in salida and "verificar.py" in salida,
                 f"verificar.py roto: no avisa: {salida[-250:]!a}")

    # 0b. caja sin git: la version no se puede leer, tiene que avisar
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as t:
        caja = copia_de_la_caja(Path(t))
        codigo, salida = correr_nuevo(caja, Path(t) / "sistema")
        chequear(codigo == 0 and "AVISO" in salida and "version" in salida.lower(),
                 f"caja sin git: no avisa que no pudo leer la version: {salida[-300:]!a}")

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
        chequear((destino / ".claude/settings.json").is_file(), "el repo generado no tiene settings.json")
        # BITACORA.md: la plantilla, calcada de la de stocky
        bit = destino / "BITACORA.md"
        chequear(bit.is_file(), "el repo generado no tiene BITACORA.md")
        if bit.is_file():
            texto = bit.read_text(encoding="utf-8")
            titulos = [l for l in texto.splitlines() if l.startswith("#")]
            chequear(titulos == ["# Bitacora — sistema_prueba", "## Estado actual",
                                 "## Decisiones cerradas", "## Historico"],
                     f"BITACORA.md con otros titulos: {titulos!a}")
            r = subprocess.run([sys.executable, str(destino / ".claude/hooks/estado.py")],
                               input=b"{}", capture_output=True,
                               env={**__import__("os").environ, "CLAUDE_PROJECT_DIR": str(destino)})
            chequear(r.returncode == 0 and b"Etapa" in r.stdout,
                     f"estado.py no lee la bitacora recien creada: {r.stdout[-200:]!a}")
        agentes = len(list((destino / ".claude/agents").glob("*.md")))
        chequear(agentes == 15, f"el repo generado tiene {agentes} agentes, no 15")
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
