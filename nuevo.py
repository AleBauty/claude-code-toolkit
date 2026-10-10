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
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent

# deteccion compartida con activar-hooks.py; vive con los hooks y viaja con ellos
sys.path.insert(0, str(AQUI / ".claude/hooks"))
from interprete import detectar_interprete, error_sin_interprete, settings_con_interprete  # noqa: E402

# carpetas de trabajo del repo nuevo
ESTRUCTURA = ["datos", "datos/adr", "src", "tests", "docs"]

# lo que se copia desde la caja de herramientas
COPIAR_DIRS = [".claude/agents", ".claude/hooks"]
# activar-hooks.py va porque settings.json esta ignorado: quien clone el repo lo regenera
COPIAR_FILES = ["METODOLOGIA.md", ".gitignore", ".env.example", "activar-hooks.py"]
# plantillas que los agentes leen; sin stack.csv no hay TBD que los haga preguntar
COPIAR_FILES += ["datos/stack.csv", "datos/convenciones.md"]


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

    # antes de crear nada: sin interprete los hooks quedan muertos y no bloquean
    interprete = detectar_interprete()
    if interprete is None:
        print(error_sin_interprete())
        print("No creo el repo.")
        sys.exit(1)

    for sub in ESTRUCTURA:
        (destino / sub).mkdir(parents=True, exist_ok=True)

    for d in COPIAR_DIRS:
        origen = AQUI / d
        if origen.is_dir():
            shutil.copytree(origen, destino / d, dirs_exist_ok=True)

    for f in COPIAR_FILES:
        origen = AQUI / f
        if origen.is_file():
            shutil.copy2(origen, destino / f)

    # los hooks activos, no el ejemplo: es el punto de copiarlos
    ejemplo = AQUI / ".claude/settings.json.example"
    if ejemplo.is_file():
        (destino / ".claude/settings.json").write_text(
            settings_con_interprete(ejemplo, interprete), encoding="utf-8"
        )
        shutil.copy2(ejemplo, destino / ".claude/settings.json.example")

    ver = version_herramientas()
    (destino / ".herramientas-version").write_text(
        f"{AQUI.name} @ {ver}\n\n"
        "Version de la caja de herramientas con la que se creo este repo.\n"
        "Si los agentes de la caja mejoraron despues, este repo NO se actualiza\n"
        "solo. Eso es a proposito: un cambio en la caja no deberia cambiar el\n"
        "comportamiento de algo que ya entregaste.\n"
        "Para traer la version nueva, volver a copiar .claude/agents a mano.\n",
        encoding="utf-8",
    )

    (destino / "CLAUDE.md").write_text(
        PLANTILLA_CLAUDE.format(nombre=nombre, ver=ver, caja=AQUI.name), encoding="utf-8"
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

    print(f"\nCreado: {destino}")
    print(f"Caja de herramientas: {AQUI.name} @ {ver}")
    print(f"Hooks configurados con: {interprete}")
    if git_ok:
        print("git iniciado, primer commit = solo el .gitignore")
    print("\nFalta hacer, en este orden:")
    print("  1. Crear el repo REMOTO en PRIVADO y conectarlo")
    print("  2. Verificar que el .gitignore tapa lo que tiene que tapar:")
    print("       git check-ignore -v .env")
    print("     Si no devuelve nada, ese archivo se va a subir")
    print("  3. Probar que los hooks bloquean de verdad (no asumirlo):")
    print('       echo \'{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}\' | '
          f'{interprete} .claude/hooks/proteger.py')
    print("     Tiene que dar exit code 2")
    print("  4. Abrir Claude Code EN ESTA CARPETA y preguntarle")
    print('     "Que subagentes tenes disponibles?": tienen que aparecer los 15')
    print(f"  5. Completar el CLAUDE.md y registrar la entrada en {AQUI.name}/INDICE-SISTEMAS.md")
    print("     (no versionado; si no existe, copiarlo de INDICE-SISTEMAS.example.md)")


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
