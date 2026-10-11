"""
Red de seguridad de actualizar.py, contra un repo de prueba en un directorio temporal.

Correr desde la raiz del repo:

    python3 tests/test_actualizar.py      (o: python tests/test_actualizar.py)

Arma lo mismo que habia en stocky: un repo creado con nuevo.py y despues dejado
con los hooks de 8639c4d (ruta relativa, fallan abierto), personalizado y
commiteado. Despues corre actualizar.py y revisa que:

- Se niega a correr con cambios sin commitear, y no toca nada.
- Muestra el plan y, si la respuesta no es "s", no toca nada.
- Compara normalizando fines de linea: un archivo igual pero con CRLF no
  aparece como "se sobrescribe".
- Lo que es DE LA CAJA (hooks, settings.json.example, agentes,
  activar-hooks.py, METODOLOGIA.md) queda igual a la caja.
- Lo que es DEL REPO (CLAUDE.md, datos/, .gitignore) queda intacto, y
  .env.example no se pisa.
- Un agente del repo que la caja no tiene se informa en el plan y no se toca.
- settings.json queda regenerado y los hooks funcionan desde un subdirectorio.
- .herramientas-version se reescribe entero.
- Las instrucciones finales salen en orden y las pruebas leen el JSON de un
  archivo, sin el patron destructivo escrito en la linea de shell.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
VIEJA = "8639c4d"   # version de la caja con la que se creo stocky
PATRON_RM = re.compile(r"\brm\s+-[a-zA-Z]*[rf]")

sys.path.insert(0, str(RAIZ))
import nuevo  # noqa: E402

fallos = []
total = 0


def chequear(cond: bool, msg: str):
    global total
    total += 1
    if not cond:
        fallos.append(msg)


def git(repo: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


def leer(p: Path) -> bytes:
    return p.read_bytes().replace(b"\r\n", b"\n")


def actualizar(repo: Path, respuesta: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(RAIZ / "actualizar.py"), str(repo)],
                          input=respuesta, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def foto(repo: Path) -> dict:
    """Contenido de todo lo versionado + settings.json, para ver si algo cambio."""
    archivos = git(repo, "ls-files").stdout.split() + [".claude/settings.json"]
    return {f: (repo / f).read_bytes() for f in archivos if (repo / f).is_file()}


def repo_viejo(tmp: Path) -> Path:
    repo = tmp / "sistema viejo"
    r = subprocess.run([sys.executable, str(RAIZ / "nuevo.py"), str(repo)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stdout + r.stderr

    # hooks y configuracion de la version vieja
    for f in (".claude/hooks/proteger.py", ".claude/hooks/secretos.py",
              ".claude/hooks/verificar.py", ".claude/hooks/interprete.py",
              ".claude/settings.json.example", "activar-hooks.py"):
        viejo = subprocess.run(["git", "show", f"{VIEJA}:{f}"], cwd=RAIZ, capture_output=True)
        (repo / f).write_bytes(viejo.stdout)
    ejemplo = json.loads((repo / ".claude/settings.json.example").read_text(encoding="utf-8"))
    (repo / ".claude/settings.json").write_text(json.dumps(ejemplo), encoding="utf-8")

    # lo que es del repo, personalizado
    (repo / "CLAUDE.md").write_text("# sistema viejo\n\nreglas propias\n", encoding="utf-8")
    (repo / "datos/stack.csv").write_text("area,decision\nbase_datos,postgres\n", encoding="utf-8")
    (repo / ".env.example").write_text("DATABASE_URL=<propia del repo>\n", encoding="utf-8")
    (repo / ".gitignore").write_text(
        (repo / ".gitignore").read_text(encoding="utf-8") + "\n# propia\nsalida/\n", encoding="utf-8")

    # un agente que la caja no tiene (propio del repo, o borrado de la caja)
    (repo / ".claude/agents/propio-del-repo.md").write_text("# agente propio\n", encoding="utf-8")

    # un archivo de la caja igual pero con CRLF: no tiene que aparecer como cambio
    meto = (RAIZ / "METODOLOGIA.md").read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    (repo / "METODOLOGIA.md").write_bytes(meto)

    git(repo, "add", "-A")
    r = git(repo, "-c", "core.autocrlf=false", "commit", "-q", "-m", "estado viejo")
    assert r.returncode == 0, r.stderr
    return repo


def bash() -> str | None:
    if os.name == "nt":
        g = shutil.which("git")
        if g:
            cand = Path(g).resolve().parent.parent / "bin" / "bash.exe"
            if cand.is_file():
                return str(cand)
    return shutil.which("bash")


def main():
    if not (RAIZ / "actualizar.py").is_file():
        print("FALLA no existe actualizar.py")
        sys.exit(1)

    # 0. si la caja no tiene algo de CREAR_SI_FALTA, el plan lo dice (antes: continue mudo)
    sys.path.insert(0, str(RAIZ))
    import actualizar as script
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as t:
        caja = Path(t) / "caja"
        shutil.copytree(RAIZ / ".claude", caja / ".claude",
                        ignore=shutil.ignore_patterns("__pycache__", "settings.json"))
        for f in ("activar-hooks.py", "METODOLOGIA.md"):
            shutil.copy2(RAIZ / f, caja / f)          # sin .env.example
        destino = Path(t) / "repo"
        (destino / ".claude/agents").mkdir(parents=True)
        original = script.AQUI
        script.AQUI = caja
        try:
            plan = script.armar_plan(destino)
        finally:
            script.AQUI = original
        chequear(any(".env.example" in a for a in plan.get("avisos", [])),
                 f"la caja sin .env.example no genera aviso en el plan: {plan.get('avisos')!a}")

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as t:
        tmp = Path(t)
        repo = repo_viejo(tmp)
        antes = foto(repo)
        del_repo = {f: antes[f] for f in ("CLAUDE.md", "datos/stack.csv", ".env.example", ".gitignore",
                                          ".claude/agents/propio-del-repo.md")}

        # 1. con cambios sin commitear: se niega y no toca nada
        (repo / "a medio hacer.txt").write_text("x", encoding="utf-8")
        r = actualizar(repo, "s\n")
        chequear(r.returncode != 0 and "sin commitear" in r.stdout + r.stderr,
                 f"con cambios sin commitear: exit={r.returncode} {(r.stdout + r.stderr)[-200:]!a}")
        os.remove(repo / "a medio hacer.txt")
        chequear(foto(repo) == antes, "con cambios sin commitear igual toco archivos")

        # 2. muestra el plan y, sin un "s", no toca nada
        r = actualizar(repo, "n\n")
        plan = r.stdout
        chequear("proteger.py" in plan and "Se sobrescribe" in plan,
                 f"el plan no muestra lo que se sobrescribe: {plan[-400:]!a}")
        chequear(foto(repo) == antes, "respondiendo 'n' igual toco archivos")

        # 2b. un agente que la caja no tiene: el plan lo informa, no se calla
        info = plan.split("Agentes en el repo que ya no están en la caja", 1)
        chequear(len(info) == 2 and "propio-del-repo.md" in info[1].split("\n\n", 1)[0],
                 f"el plan no informa el agente que no esta en la caja: {plan[-500:]!a}")

        # 3. CRLF: METODOLOGIA.md es igual, no se lista como cambio
        seccion = plan.split("Se sobrescribe", 1)[-1].split("No se tocan", 1)[0]
        chequear("METODOLOGIA.md" not in seccion,
                 "METODOLOGIA.md con CRLF aparece como cambio: no normaliza fines de linea")

        # 4. aplicar
        r = actualizar(repo, "s\n")
        salida = r.stdout + r.stderr
        chequear(r.returncode == 0, f"actualizar.py fallo: exit={r.returncode} {salida[-400:]!a}")

        # de la caja: igual a la caja
        de_la_caja = ([p.relative_to(RAIZ).as_posix() for p in (RAIZ / ".claude/hooks").glob("*.py")]
                      + [p.relative_to(RAIZ).as_posix() for p in (RAIZ / ".claude/agents").glob("*.md")]
                      + [".claude/settings.json.example", "activar-hooks.py", "METODOLOGIA.md"])
        for f in de_la_caja:
            chequear((repo / f).is_file() and leer(repo / f) == leer(RAIZ / f),
                     f"{f} no quedo igual a la caja")

        # del repo: intacto
        for f, contenido in del_repo.items():
            chequear((repo / f).read_bytes() == contenido, f"{f} es del repo y fue modificado")

        # settings.json regenerado
        cfg = (repo / ".claude/settings.json").read_text(encoding="utf-8")
        chequear("${CLAUDE_PROJECT_DIR}" in cfg, "settings.json no quedo regenerado")
        chequear("OK: proteger.py bloquea" in salida, "no informa la prueba de activar-hooks.py")

        # .herramientas-version entero
        version = (repo / ".herramientas-version").read_text(encoding="utf-8")
        chequear(version.startswith(f"{RAIZ.name} @ ") and "actualizar.py" in version,
                 f".herramientas-version no se reescribio entero: {version[:200]!a}")

        # instrucciones finales: en orden, y las pruebas leen el JSON de un archivo
        i_reinicio = salida.find("Reiniciá Claude Code desde la raíz del repo")
        i_parrafo = salida.find("Al empezar una sesión, verificar que exista")
        i_pruebas = salida.find("proteger.py\" <")
        chequear(-1 < i_reinicio < i_parrafo < i_pruebas,
                 f"instrucciones fuera de orden: reinicio={i_reinicio} parrafo={i_parrafo} "
                 f"pruebas={i_pruebas}")
        final = salida[i_reinicio:]
        chequear(not PATRON_RM.search(final),
                 "las instrucciones finales tienen el patron destructivo en linea")
        for m in re.finditer(r'< "([^"]+\.json)"', final):
            chequear(Path(m.group(1)).is_file(), f"el JSON de prueba {m.group(1)} no existe")

        # 5. los hooks del repo funcionan desde un subdirectorio, como en una sesion real
        sh = bash()
        if sh is None:
            print("AVISO: sin bash; salteo la prueba desde subdirectorio.")
        else:
            sub = repo / "src" / "algo"
            sub.mkdir(parents=True, exist_ok=True)
            env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
            cmds = [h["command"] for g in json.loads(cfg)["hooks"].values()
                    for grupo in g for h in grupo["hooks"]]
            prot = next(c for c in cmds if "proteger.py" in c)
            for entrada, esperado in (({"tool_input": {"command": "ls"}}, 0),
                                      ({"tool_input": {"command": "rm -rf /tmp/x"}}, 2)):
                r = subprocess.run([sh, "-c", prot], cwd=sub, env=env, input=json.dumps(entrada),
                                   capture_output=True, text=True)
                chequear(r.returncode == esperado,
                         f"proteger.py desde subdirectorio: exit={r.returncode}, esperado {esperado}")

        # 6. idempotente: una segunda corrida no tiene nada que sobrescribir
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "actualizado")
        r = actualizar(repo, "n\n")
        seccion = r.stdout.split("Se sobrescribe", 1)[-1].split("No se tocan", 1)[0]
        chequear("proteger.py" not in seccion, "una segunda corrida vuelve a listar proteger.py")

    for f in fallos:
        print("FALLA", f)
    print(f"\n{total - len(fallos)}/{total} casos pasan"
          + (f" - {len(fallos)} FALLAN" if fallos else ""))
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
