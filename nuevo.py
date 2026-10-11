#!/usr/bin/env python3
"""
Crea un repositorio nuevo a partir de esta caja de herramientas.

Copia los agentes, los hooks y la metodologia al repo nuevo, para que Claude
Code los tenga cuando lo abras ahi adentro. Sin esta copia, el repo del cliente
no tiene ni agentes ni hooks: Claude lee .claude/ de la carpeta donde se abre.

Uso:
    python3 nuevo.py <ruta-destino>

Ejemplo:
    python3 nuevo.py ~/repos/sistema_acme
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent

# deteccion compartida con activar-hooks.py; vive con los hooks y viaja con ellos
sys.path.insert(0, str(AQUI / ".claude/hooks"))
try:
    from interprete import (  # noqa: E402
        detectar_interprete, error_sin_interprete, probar_hooks, settings_con_interprete,
    )
except ImportError as e:
    print(f"ERROR: falta .claude/hooks/interprete.py en la caja ({e}). No creo nada.")
    sys.exit(1)

# carpetas de trabajo del repo nuevo
ESTRUCTURA = ["datos", "datos/adr", "src", "tests", "docs"]

# lo que se copia desde la caja de herramientas
COPIAR_DIRS = [".claude/agents", ".claude/hooks"]
# activar-hooks.py va porque settings.json esta ignorado: quien clone el repo lo regenera
COPIAR_FILES = ["METODOLOGIA.md", ".gitignore", ".env.example", "activar-hooks.py"]
# plantillas que los agentes leen; sin stack.csv no hay TBD que los haga preguntar
COPIAR_FILES += ["datos/stack.csv", "datos/convenciones.md"]
# de aca sale settings.json: sin el, el repo nace sin hooks
EJEMPLO_SETTINGS = ".claude/settings.json.example"


def hooks_requeridos() -> list[str]:
    """interprete.py mas cada hook que settings.json.example manda a correr."""
    ejemplo = AQUI / EJEMPLO_SETTINGS
    usados = re.findall(r"\.claude/hooks/(\w+\.py)", ejemplo.read_text(encoding="utf-8")) \
        if ejemplo.is_file() else []
    return [f".claude/hooks/{h}" for h in ["interprete.py", *dict.fromkeys(usados)]]


def fuentes_faltantes() -> list[str]:
    """Todo lo que se va a copiar y no esta. Se revisa ANTES de crear nada: un
    repo a medio armar es peor que ningun repo.

    "La carpeta tiene algo" no alcanza: __pycache__ cuenta como algo. Se valida
    que tenga lo que se espera: al menos un agente .md, y cada hook que usa
    settings.json.example."""
    faltan = [f for f in COPIAR_FILES + [EJEMPLO_SETTINGS] if not (AQUI / f).is_file()]
    if not list((AQUI / ".claude/agents").glob("*.md")):
        faltan.append(".claude/agents (ningun agente .md)")
    faltan += [h for h in hooks_requeridos() if not (AQUI / h).is_file()]
    return faltan


def problemas_del_resultado(destino: Path) -> list[str]:
    """Verifica lo que nuevo.py afirma al terminar, en vez de darlo por hecho."""
    problemas = []
    if not (destino / ".claude/settings.json").is_file():
        problemas.append("no se escribio .claude/settings.json: el repo no tiene hooks")
    esperados = len(list((AQUI / ".claude/agents").glob("*.md")))
    copiados = len(list((destino / ".claude/agents").glob("*.md")))
    if copiados == 0 or copiados != esperados:   # 0 == 0 no es un exito
        problemas.append(f"se copiaron {copiados} agentes de {esperados}")
    problemas += [f"falta {h}" for h in hooks_requeridos() if not (destino / h).is_file()]
    return problemas


def version_herramientas() -> str:
    """Commit de la caja de herramientas, para saber de que version salio."""
    try:
        r = subprocess.run(
            ["git", "-C", str(AQUI), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return "sin-git"


def texto_version(ver: str) -> str:
    """Contenido completo de .herramientas-version en el repo de un sistema."""
    return (
        f"{AQUI.name} @ {ver}\n\n"
        "Version de la caja de herramientas con la que se creo o actualizo este repo.\n"
        "Si la caja mejoro despues, este repo NO se actualiza solo. Es a proposito:\n"
        "un cambio en la caja no deberia cambiar el comportamiento de algo que ya\n"
        "entregaste.\n\n"
        "Para traer la version nueva, con este repo sin cambios sin commitear,\n"
        "desde la caja:\n"
        "    python actualizar.py <ruta de este repo>\n"
        "Muestra que va a cambiar y espera confirmacion. Sobrescribe lo que es de\n"
        "la caja (hooks, agentes, settings.json.example, activar-hooks.py,\n"
        "METODOLOGIA.md), no toca lo que es de este repo (CLAUDE.md, datos/,\n"
        ".gitignore, src/, tests/, docs/) y regenera .claude/settings.json.\n"
        "Despues: reiniciar Claude Code desde la raiz de este repo.\n"
    )


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    destino = Path(sys.argv[1]).expanduser().resolve()
    nombre = destino.name

    if destino.exists() and any(destino.iterdir()):
        print(f"ERROR: {destino} ya existe y no esta vacia.")
        print("No voy a escribir encima. Elegi otra ruta o vaciala vos.")
        sys.exit(1)

    # antes de crear nada: lo que falta en la caja se saltearia en silencio
    faltan = fuentes_faltantes()
    if faltan:
        print("ERROR: a la caja le falta lo que hay que copiar:")
        for f in faltan:
            print(f"  {f}")
        print("No creo el repo: naceria incompleto y nada lo avisaria.")
        sys.exit(1)

    # antes de crear nada: sin interprete los hooks quedan muertos y no bloquean
    interprete = detectar_interprete()
    if interprete is None:
        print(error_sin_interprete())
        print("No creo el repo.")
        sys.exit(1)

    for sub in ESTRUCTURA:
        (destino / sub).mkdir(parents=True, exist_ok=True)

    # sin "if existe": ya se valido. Si algo falla aca, que se vea.
    for d in COPIAR_DIRS:
        shutil.copytree(AQUI / d, destino / d, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__"))
    for f in COPIAR_FILES:
        shutil.copy2(AQUI / f, destino / f)

    # los hooks activos, no el ejemplo: es el punto de copiarlos
    ejemplo = AQUI / EJEMPLO_SETTINGS
    (destino / ".claude/settings.json").write_text(
        settings_con_interprete(ejemplo, interprete), encoding="utf-8"
    )
    shutil.copy2(ejemplo, destino / EJEMPLO_SETTINGS)

    ver = version_herramientas()
    if ver == "sin-git":
        print("AVISO: no se pudo leer la version de la caja con git. .herramientas-version\n"
              "       va a decir 'sin-git' y no se va a saber de que version salio el repo.")
    (destino / ".herramientas-version").write_text(texto_version(ver), encoding="utf-8")

    (destino / "CLAUDE.md").write_text(
        PLANTILLA_CLAUDE.format(nombre=nombre, ver=ver, caja=AQUI.name,
                                parrafo_hooks=PARRAFO_HOOKS), encoding="utf-8"
    )

    # git: .gitignore primero y solo
    try:
        subprocess.run(["git", "init", "-q"], cwd=destino, check=True, timeout=30)
        subprocess.run(["git", "add", ".gitignore"], cwd=destino, check=True, timeout=30)
        subprocess.run(
            ["git", "commit", "-q", "-m", "inicial: .gitignore antes que cualquier otra cosa"],
            cwd=destino, check=True, timeout=30,
        )
        git_ok = True
    except Exception as e:
        git_ok = False
        print(f"AVISO: git no se pudo inicializar ({e}). Hacelo a mano.")

    # verificar lo que se va a afirmar, no darlo por hecho
    problemas = problemas_del_resultado(destino)
    ok_hooks, lineas = probar_hooks(destino, interprete)
    if problemas or not ok_hooks:
        print(f"\nERROR: el repo en {destino} quedo incompleto:")
        for p in problemas:
            print(f"  {p}")
        if not ok_hooks:
            for linea in lineas:
                print(f"  {linea}")
        print("No usarlo así. Revisar la caja, borrar la carpeta y volver a crearlo.")
        sys.exit(1)

    print(f"\nCreado: {destino}")
    print(f"Caja de herramientas: {AQUI.name} @ {ver}")
    print(f"Hooks configurados con: {interprete}")
    for linea in lineas:
        print(linea)
    if git_ok:
        print("git iniciado, primer commit = solo el .gitignore")
    print("\nFalta hacer, en este orden:")
    print("  1. Crear el repo REMOTO en PRIVADO y conectarlo")
    print("  2. Verificar que el .gitignore tapa lo que tiene que tapar:")
    print("       git check-ignore -v .env")
    print("     Si no devuelve nada, ese archivo se va a subir")
    print("  3. Arriba dice OK para cada hook: ya se probaron. Para repetir la")
    print("     prueba, correr activar-hooks.py dentro del repo nuevo.")
    print("  4. Abrir Claude Code EN ESTA CARPETA y preguntarle")
    print('     "Que subagentes tenes disponibles?": tienen que aparecer los 15')
    print(f"  5. Completar el CLAUDE.md y registrar la entrada en {AQUI.name}/INDICE-SISTEMAS.md")
    print("     (no versionado; si no existe, copiarlo de INDICE-SISTEMAS.example.md)")


# va en la plantilla y actualizar.py lo imprime para pegar a mano: una sola fuente
PARRAFO_HOOKS = """\
**Al empezar una sesión, verificar que exista `.claude/settings.json`.** Si no
existe, los hooks no están activos: nada bloquea comandos destructivos ni
credenciales. Avisarle al usuario y ofrecer correr `activar-hooks.py`. Pasa al
clonar el repo en otra máquina: `nuevo.py` ya lo genera al crear un repo, pero
un clon no lo trae porque no se versiona."""

PLANTILLA_CLAUDE = """# {nombre}

Sistema. Repo propio.

Creado desde la caja de herramientas `{caja}/` @ {ver}

## Que tiene que hacer

(Una linea. Si no se puede escribir en una linea, el alcance no esta claro.)

## Estado

| Frente | Estado |
|---|---|
| requisitos | TBD |
| arquitectura | TBD |
| construccion | TBD |

## Antes de responder

1. `METODOLOGIA.md` — reglas de proceso, aplican a todos los agentes
2. `datos/stack.csv` — decisiones tecnicas. **Si dice TBD, preguntar**
3. `datos/convenciones.md` — estilo del proyecto
4. `datos/adr/` — por que se decidio lo que se decidio

## Orden que evita retrabajo

```
descubrimiento -> requisitos -> ux-ui -> arquitecto -> base-datos -> backend/frontend/mobile
                                                                         |
                                                           qa -> revisor -> seguridad
                                                                         |
                                                     infraestructura -> documentacion
```

## Hooks

Se activan corriendo `activar-hooks.py`, que escribe `.claude/settings.json`
con el intérprete de Python que funciona en esa máquina. Ese archivo no se
versiona.

{parrafo_hooks}

## Git

- Antes de cada commit: mostrarme el diff y esperar aprobacion.
- Credenciales nunca en archivos versionados. Van en `.env`, que esta ignorado.
- Si una credencial se filtro: **rotarla**. Borrar el commit no arregla nada.

## Sesgo explicito

Lo simple primero. Antes de proponer algo complejo, verificar que el problema
lo justifique.

Tono: espanol neutro, tecnico, directo.
"""


if __name__ == "__main__":
    main()
