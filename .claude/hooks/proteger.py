#!/usr/bin/env python3
"""
Hook PreToolUse sobre Bash y PowerShell: bloquea comandos destructivos o peligrosos.

Las reglas de PowerShell/cmd son los equivalentes de las de Unix, no una
lista aparte: misma intencion, otra sintaxis. Las de git y SQL ya sirven
para cualquier shell.

El contrato es "bloqueo lo que destruye". Lo que cambia la postura de
seguridad (Set-ExecutionPolicy, etc.) no entra aca: va como control aparte.

DELIBERADO: los patrones se buscan en el texto del comando, sin interpretarlo.
Un `echo "rm -rf ..."` o un string con "reg delete" adentro tambien se bloquea.
No es un bug: un hook de este tipo tiene que errar hacia bloquear de mas.
Parsear el comando para distinguir un string de una ejecucion real abre la
puerta a evadirlo. Lo fijan los tests del repo claude-code-toolkit (tests/test_proteger.py).

Exit 2 = bloquea. Exit 0 = deja pasar.

FALLA CERRADO: si el hook mismo se rompe (JSON invalido, estructura inesperada,
cualquier excepcion) sale con 2 y el mensaje dice que fallo el hook, no el
comando. Un exit 1 Claude Code lo toma como "no bloquear": un hook de seguridad
roto dejaria pasar todo. La contracara: un bug que rompe el hook siempre
bloquea todo, y Claude no puede arreglarlo porque el hook corre antes que el
arreglo. Por eso la salida va en el propio mensaje (disableAllHooks en
.claude/settings.local.json). Detalle completo: SETUP.md del repo claude-code-toolkit.
"""
import json
import re
import sys

# (patron, motivo)
REGLAS = [
    (r"\brm\s+(-[a-zA-Z]*\s+)*-[a-zA-Z]*[rf]", "borrado recursivo/forzado"),
    (r":\s*\(\s*\)\s*\{.*\|.*&.*\}\s*;", "fork bomb"),
    (r"\bmkfs\b",                      "formateo de disco"),
    (r"\bdd\s+.*of=/dev/",             "escritura directa a disco"),
    (r">\s*/dev/sd[a-z]",              "escritura directa a disco"),
    (r"\bchmod\s+(-R\s+)?777\b",       "permisos 777"),
    (r"DROP\s+(TABLE|DATABASE|SCHEMA)", "DROP de base de datos"),
    (r"TRUNCATE\s+TABLE",              "TRUNCATE de tabla"),
    (r"\bDELETE\s+FROM\s+\w+\s*(;|$)", "DELETE sin WHERE"),
    (r"\bgit\s+push\s+.*--force(?!-with-lease)", "push --force (usar --force-with-lease)"),
    (r"\bgit\s+reset\s+--hard\b",      "reset --hard descarta cambios sin recuperacion"),
    (r"\bgit\s+clean\s+-[a-zA-Z]*f",   "git clean borra archivos sin seguimiento"),
    (r"curl[^|]*\|\s*(sudo\s+)?(ba)?sh", "descargar y ejecutar directo"),
    (r"wget[^|]*\|\s*(sudo\s+)?(ba)?sh", "descargar y ejecutar directo"),

    # --- PowerShell / cmd: equivalentes de las reglas de arriba ---
    # rm -rf: Remove-Item y sus alias con -Recurse o -Force (PowerShell acepta prefijos: -r, -fo)
    (r"\b(Remove-Item|ri|rm|rmdir|rd|del|erase)\b[^;|\n]*\s-(r\w*|fo\w*)\b",
     "borrado recursivo/forzado (PowerShell)"),
    (r"\b(rd|rmdir)\b[^;&|\n]*\s/s\b", "borrado recursivo (cmd)"),
    (r"\b(del|erase)\b[^;&|\n]*\s/[sqf]\b", "borrado recursivo/forzado/sin confirmar (cmd)"),
    # mkfs / dd a disco
    (r"\b(Format-Volume|Clear-Disk|Initialize-Disk|Remove-Partition)\b", "formateo de disco (PowerShell)"),
    (r"\bformat(\.com)?\s+[a-z]:", "formateo de disco (cmd)"),
    (r"\bdiskpart\b", "particionado de disco (cmd)"),
    # rm -rf sobre el registro: borrar ramas puede dejar Windows inservible
    # (Remove-Item HKLM:\... -Recurse ya lo cubre la regla de Remove-Item)
    (r"\breg(\.exe)?\s+delete\b", "borrado del registro de Windows"),
    # chmod 777: escritura o control total para todos
    (r"\bicacls\b.*\s/grant(:r)?\s+[\"']?(\*S-1-1-0|Everyone|Todos)[\"']?:\S*[FM]\b",
     "permisos de escritura para todos (icacls)"),
    # curl | sh
    (r"\b(iwr|irm|Invoke-WebRequest|Invoke-RestMethod|curl|wget)\b[^|]*\|\s*(iex|Invoke-Expression)\b",
     "descargar y ejecutar directo (PowerShell)"),
    (r"\b(iex|Invoke-Expression)\b.*\b(DownloadString|iwr|irm|Invoke-WebRequest|Invoke-RestMethod)\b",
     "descargar y ejecutar directo (PowerShell)"),
]


def main():
    # UTF-8 explicito en las dos puntas: Claude Code manda y lee UTF-8. Con el default
    # del entorno (cp1252 en Windows) el mensaje salia deformado con acentos, y no
    # romper dependia de surrogateescape. Detalle: SETUP.md del repo claude-code-toolkit.
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    data = json.loads(sys.stdin.buffer.read().decode("utf-8"))  # invalido: fallar_cerrado()

    cmd = (data.get("tool_input") or {}).get("command", "")
    if not cmd:
        sys.exit(0)

    for patron, motivo in REGLAS:
        if re.search(patron, cmd, re.IGNORECASE):
            print(
                f"Comando bloqueado: {motivo}\n\n"
                f"  {cmd}\n\n"
                "Si realmente hace falta, el usuario lo corre a mano "
                "o ajusta .claude/hooks/proteger.py",
                file=sys.stderr,
            )
            sys.exit(2)

    sys.exit(0)


def fallar_cerrado(error: BaseException):
    print(
        f"FALLO EL HOOK proteger.py, no tu comando: {type(error).__name__}: {error}\n"
        "Tu comando no fue evaluado, y por seguridad se bloquea.\n"
        "Si pasa con cualquier comando, el hook tiene un bug. Para salir: fuera de "
        "Claude Code, poner {\"disableAllHooks\": true} en .claude/settings.local.json "
        "(se aplica sin reiniciar), arreglar el hook y despues sacar esa linea. "
        "Mientras tanto no hay ninguna proteccion.",
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
