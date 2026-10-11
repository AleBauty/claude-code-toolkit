"""
Deteccion del interprete de Python para los hooks, y prueba de que bloquean.
No es un hook.

Fuente unica para nuevo.py y activar-hooks.py: si cada uno tuviera su copia,
se desincronizarian sin que nadie lo note.
"""
import json
import subprocess
from pathlib import Path

# en orden de preferencia; el primero que funcione de verdad es el que usan los hooks
INTERPRETES = ["python3", "python"]


def detectar_interprete() -> str | None:
    """Primer interprete que ejecuta Python de verdad.

    Mira la salida, no solo el exit code: el alias de la Microsoft Store en
    Windows existe en el PATH pero no ejecuta el codigo.
    """
    for cand in INTERPRETES:
        try:
            r = subprocess.run(
                [cand, "-c", "print(1)"],
                capture_output=True, text=True, timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if r.returncode == 0 and r.stdout.strip() == "1":
            return cand
    return None


def settings_con_interprete(ejemplo: Path, interprete: str) -> str:
    """settings.json.example con los comandos de hooks apuntando a `interprete`."""
    cfg = json.loads(ejemplo.read_text(encoding="utf-8"))
    for grupos in cfg.get("hooks", {}).values():
        for grupo in grupos:
            for hook in grupo.get("hooks", []):
                prog, _, resto = hook["command"].partition(" ")
                if prog in INTERPRETES:
                    hook["command"] = f"{interprete} {resto}"
    return json.dumps(cfg, indent=2, ensure_ascii=False) + "\n"


# Credencial de prueba armada por partes A PROPOSITO, y la linea que la contiene
# tambien: escrita entera, secretos.py bloquea el Edit/Write de este mismo
# archivo. No juntar las partes.
_CREDENCIAL_DE_PRUEBA = "sk-" + "pRu3bA" + "dEl0sH00ks" + "N0eSr3aL"
_LINEA_CON_CREDENCIAL = "API_KEY = " + '"' + _CREDENCIAL_DE_PRUEBA + '"'

# (hook, entrada, exit esperado, marca en stderr, que prueba, es de seguridad)
# La marca es lo que distingue al hook de verdad: sin el archivo, Python tambien
# sale con 2 ("can't open file"), y un exit 2 solo pasaria por un bloqueo.
# El JSON se arma aca y no en una linea de shell: un comando de shell que lo
# contenga escrito lo bloquea el propio hook antes de que llegue a correr.
PRUEBAS = [
    ("proteger.py", json.dumps({"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/prueba"}}),
     2, "Comando bloqueado", "bloquea un comando destructivo", True),
    ("secretos.py", json.dumps({"tool_name": "Write", "tool_input": {
        "file_path": "config.py", "content": _LINEA_CON_CREDENCIAL}}),
     2, "Posible credencial", "bloquea una credencial", True),
    # calidad: en un repo sin stack no hay nada que verificar; se prueba que
    # arranque y avise ante una entrada ilegible (bloque D)
    ("verificar.py", "{entrada rota", 1, "AVISO", "arranca y avisa ante una entrada ilegible", False),
]


def probar_hooks(raiz: Path, interprete: str) -> tuple[bool, list[str]]:
    """Corre cada hook con una entrada que tiene que hacerlo reaccionar.

    Devuelve (los de seguridad funcionan, lineas para mostrar). Si falla uno de
    seguridad, el primer valor es False: no hay que escribir settings.json. Si
    falla verificar.py, la linea es un AVISO y el primer valor no cambia.
    La ruta es absoluta: no depende del directorio desde donde se llame.
    """
    seguridad_ok, lineas = True, []
    for hook, entrada, esperado, marca, que, de_seguridad in PRUEBAS:
        ruta = Path(raiz).resolve() / ".claude" / "hooks" / hook
        try:
            r = subprocess.run([interprete, str(ruta)], input=entrada.encode("utf-8"),
                               capture_output=True, timeout=30)
            codigo, err = r.returncode, r.stderr.decode("utf-8", errors="replace").strip()
        except (OSError, subprocess.TimeoutExpired) as e:
            codigo, err = None, f"no se pudo correr: {e}"
        if codigo == esperado and marca in err:
            lineas.append(f"OK: {hook} {que} (exit {codigo}).")
            continue
        detalle = (f"{hook} no {que}: exit {codigo}, se esperaba {esperado} con "
                   f"'{marca}'. {err[:200]}")
        if de_seguridad:
            seguridad_ok = False
            lineas.append(f"FALLA: {detalle}")
        else:
            lineas.append(f"AVISO: {detalle} (es de calidad: no impide activar los otros)")
    return seguridad_ok, lineas


def error_sin_interprete() -> str:
    return (
        f"ERROR: ninguno de {', '.join(INTERPRETES)} ejecuta Python en esta maquina.\n"
        "Los hooks no correrian y no bloquearian nada.\n"
        "Instala Python (en Windows, desactiva los alias de la Store en\n"
        "'Alias de ejecucion de aplicaciones') y volve a correr esto."
    )
