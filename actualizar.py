#!/usr/bin/env python3
"""
Trae a un repo creado con nuevo.py la version actual de esta caja de herramientas.

Uso:
    python3 actualizar.py <ruta-del-repo>      (o: python actualizar.py ...)

El criterio es por DUENO, no por archivo:

- Lo que es DE LA CAJA se sobrescribe siempre: .claude/hooks/*.py,
  .claude/settings.json.example, .claude/agents/*.md, activar-hooks.py y
  METODOLOGIA.md. La lista sale de recorrer esas carpetas al correr: un hook o
  un agente nuevo viaja sin tocar este script.
- Lo que es DEL REPO no se toca nunca: CLAUDE.md, datos/, .gitignore, src/,
  tests/, docs/ (y todo lo que no sea de la caja).
- .env.example se crea si falta y no se pisa nunca: el repo le agrega sus
  propias variables.
- Un agente del repo que la caja no tiene (propio, o borrado de la caja) no se
  toca, pero el plan lo informa.

Pasos:
1. Se niega a correr si el repo tiene cambios sin commitear: no pisa trabajo a
   medio hacer, y el diff de la actualizacion queda limpio para revisar.
2. Muestra que va a cambiar y espera confirmacion. Si un agente personalizado
   aparece en "Se sobrescribe", ese es el momento de frenar.
3. Copia, corre activar-hooks.py en el repo (regenera .claude/settings.json,
   que no se versiona, y prueba que proteger.py bloquee) y reescribe
   .herramientas-version entero.
4. Imprime lo que queda a mano: reiniciar Claude Code, el parrafo del
   CLAUDE.md y las pruebas.

No commitea: el diff lo revisa el usuario.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent

sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI / ".claude/hooks"))
from interprete import detectar_interprete, error_sin_interprete  # noqa: E402
from nuevo import PARRAFO_HOOKS, texto_version, version_herramientas  # noqa: E402

CREAR_SI_FALTA = [".env.example"]
DEL_REPO = ["CLAUDE.md", "datos/", ".gitignore", "src/", "tests/", "docs/"]


def de_la_caja() -> list[str]:
    """Lo que la caja produce. Rutas relativas, con /."""
    archivos = sorted(p for p in (AQUI / ".claude/hooks").glob("*.py"))
    archivos += sorted((AQUI / ".claude/agents").glob("*.md"))
    archivos += [AQUI / ".claude/settings.json.example", AQUI / "activar-hooks.py",
                 AQUI / "METODOLOGIA.md"]
    return [p.relative_to(AQUI).as_posix() for p in archivos]


def normalizado(p: Path) -> bytes:
    # en Windows git convierte LF a CRLF al copiar: comparar crudo los ve
    # distintos aunque sean iguales
    return p.read_bytes().replace(b"\r\n", b"\n")


def git(repo: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def salir(msg: str, codigo: int = 1):
    print(f"ERROR: {msg}")
    sys.exit(codigo)


def validar(destino: Path):
    if not destino.is_dir():
        salir(f"{destino} no existe.")
    if destino == AQUI:
        salir("esa es la caja de herramientas, no un repo de sistema.")
    raiz = git(destino, "rev-parse", "--show-toplevel")
    if raiz.returncode != 0 or Path(raiz.stdout.strip()).resolve() != destino:
        salir(f"{destino} no es la raiz de un repo git.")
    if not (destino / ".herramientas-version").is_file():
        salir(f"{destino} no tiene .herramientas-version: no parece creado con nuevo.py.")

    sucio = git(destino, "status", "--porcelain").stdout.strip()
    if sucio:
        salir("el repo tiene cambios sin commitear. Commitealos o descartalos antes:\n"
              "no voy a pisar trabajo a medio hacer.\n\n" + sucio)


def armar_plan(destino: Path) -> dict:
    plan = {"sobrescribe": [], "crea": [], "iguales": [], "respeta": [], "huerfanos": [],
            "avisos": []}
    caja = de_la_caja()
    for f in caja:
        if not (destino / f).is_file():
            plan["crea"].append(f)
        elif normalizado(destino / f) != normalizado(AQUI / f):
            plan["sobrescribe"].append(f)
        else:
            plan["iguales"].append(f)
    for f in CREAR_SI_FALTA:
        if not (AQUI / f).is_file():
            plan["avisos"].append(f"la caja no tiene {f}: no se puede ofrecer al repo")
            continue
        (plan["respeta"] if (destino / f).is_file() else plan["crea"]).append(f)
    # agentes que la caja no tiene: propios del repo o borrados de la caja. No se
    # tocan (podrian ser propios), pero se informan: no actuar no es callarse.
    for p in sorted((destino / ".claude/agents").glob("*.md")):
        f = p.relative_to(destino).as_posix()
        if f not in caja:
            plan["huerfanos"].append(f)
    return plan


def mostrar_plan(destino: Path, plan: dict, ver: str):
    print(f"Repo:  {destino}")
    print(f"Caja:  {AQUI.name} @ {ver}")
    actual = (destino / ".herramientas-version").read_text(encoding="utf-8").splitlines()
    print(f"Ahora: {actual[0] if actual else '(vacio)'}\n")

    avisos = list(plan["avisos"])
    if ver.startswith("sin-git"):
        avisos.append("no se pudo leer la version de la caja con git: "
                      ".herramientas-version va a decir 'sin-git'")
    for a in avisos:
        print(f"AVISO: {a}")
    if avisos:
        print()

    print("Se sobrescribe (de la caja, distinto en el repo):")
    for f in plan["sobrescribe"] or ["(nada)"]:
        print(f"  {f}")
    print("\nSe crea (no existe en el repo):")
    for f in plan["crea"] or ["(nada)"]:
        print(f"  {f}")
    print("\nNo se tocan (del repo):")
    for f in DEL_REPO + plan["respeta"]:
        print(f"  {f}")
    if plan["huerfanos"]:
        print("\nAgentes en el repo que ya no están en la caja (no se tocan; decidí vos):")
        for f in plan["huerfanos"]:
            print(f"  {f}")
        print("  Si es propio del repo, queda como está. Si la caja lo eliminó, borralo a mano.")
    print(f"\nIguales a la caja, no cambian: {len(plan['iguales'])} archivos.")
    print("Ademas: se regenera .claude/settings.json y se reescribe .herramientas-version.")
    print("Si un agente que personalizaste aparece en 'Se sobrescribe', responde que no.\n")


def aplicar(destino: Path, plan: dict, ver: str) -> str:
    for f in plan["sobrescribe"] + plan["crea"]:
        (destino / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(AQUI / f, destino / f)
    print(f"Copiados: {len(plan['sobrescribe']) + len(plan['crea'])} archivos.")

    interprete = detectar_interprete()
    if interprete is None:
        salir(error_sin_interprete() + "\nLos archivos ya se copiaron; settings.json NO se regenero.")
    print(f"\nCorriendo activar-hooks.py en el repo ({interprete}):")
    r = subprocess.run([interprete, str(destino / "activar-hooks.py")], cwd=destino,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("  " + (r.stdout + r.stderr).strip().replace("\n", "\n  "))
    if r.returncode != 0:
        salir("activar-hooks.py fallo. Los archivos ya se copiaron: revisar con git diff\n"
              "y no usar el repo hasta que la prueba de proteger.py de OK.")

    (destino / ".herramientas-version").write_text(texto_version(ver), encoding="utf-8")
    return interprete


def archivos_de_prueba() -> Path:
    """El JSON de prueba se escribe desde Python: una linea de shell que lo
    contenga la bloquea el propio hook antes de que corra."""
    d = Path(tempfile.mkdtemp(prefix="prueba-hooks-"))
    (d / "destructivo.json").write_text(
        json.dumps({"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/prueba"}}),
        encoding="utf-8")
    (d / "roto.json").write_text("{esto no es json", encoding="utf-8")
    return d


def instrucciones(destino: Path, interprete: str):
    hooks = (destino / ".claude/hooks").as_posix()
    pruebas = archivos_de_prueba().as_posix()
    tiene_parrafo = "verificar que exista `.claude/settings.json`" in \
        (destino / "CLAUDE.md").read_text(encoding="utf-8", errors="replace")

    print("\n" + "=" * 72)
    print("\n1. Reiniciá Claude Code desde la raíz del repo antes de probar nada: el\n"
          "   settings.json se lee al abrir la sesión.")

    print("\n2. El CLAUDE.md del repo es del repo: este script NO lo toca.")
    if tiene_parrafo:
        print("   Ya tiene el párrafo de verificar settings.json. No hace falta nada.")
    else:
        print("   Pegá este párrafo a mano, en una sección \"## Hooks\":\n")
        print("   " + PARRAFO_HOOKS.replace("\n", "\n   "))

    print("\n3. Pruebas, desde la sesión nueva. El JSON viene de un archivo: escrito\n"
          "   en la línea de comandos, el propio hook bloquearía el comando.\n")
    print(f'   {interprete} "{hooks}/proteger.py" < "{pruebas}/destructivo.json"; echo "exit=$?"')
    print("      -> exit=2, \"Comando bloqueado\"")
    print(f'   {interprete} "{hooks}/proteger.py" < "{pruebas}/roto.json"; echo "exit=$?"')
    print("      -> exit=2, \"FALLO EL HOOK\" y la salida con disableAllHooks")
    print("\n   Desde un subdirectorio (el caso que trababa la sesión), en pasos\n"
          "   separados: en Windows no se puede borrar la carpeta donde está parado\n"
          "   el shell.")
    print("      mkdir tmp-prueba && cd tmp-prueba && pwd    -> tiene que pasar")
    print("      cd ..")
    print("      rmdir tmp-prueba")

    print("\n4. Revisá el diff (git diff) y commiteá. Este script no commitea.")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    destino = Path(sys.argv[1]).expanduser().resolve()
    validar(destino)

    ver = version_herramientas()
    if git(AQUI, "status", "--porcelain").stdout.strip():
        ver += " (con cambios sin commitear en la caja)"

    plan = armar_plan(destino)
    mostrar_plan(destino, plan, ver)

    try:
        respuesta = input("¿Aplicar? [s/N] ").strip().lower()
    except EOFError:
        respuesta = ""
    if respuesta not in ("s", "si", "sí"):
        print("\nNo se aplicó nada.")
        sys.exit(0)

    print()
    interprete = aplicar(destino, plan, ver)
    instrucciones(destino, interprete)


if __name__ == "__main__":
    main()
