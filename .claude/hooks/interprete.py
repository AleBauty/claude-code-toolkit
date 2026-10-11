"""
Deteccion del interprete de Python para los hooks, y prueba de que bloquean.
No es un hook.

Fuente unica para nuevo.py y activar-hooks.py: si cada uno tuviera su copia,
se desincronizarian sin que nadie lo note.
"""
import json
import os
import subprocess
import tempfile
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

# Cada prueba: hook, entrada (funcion del proyecto de prueba), exit esperado,
# marca en stderr, que prueba, y si es de seguridad.
# La marca es lo que distingue al hook de verdad: sin el archivo, Python tambien
# sale con 2 ("can't open file"), y un exit 2 solo pasaria por un bloqueo.
# El JSON se arma aca y no en una linea de shell: un comando de shell que lo
# contenga escrito lo bloquea el propio hook antes de que llegue a correr.
PRUEBAS = [
    ("proteger.py",
     lambda p: json.dumps({"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/prueba"}}),
     2, "Comando bloqueado", "bloquea un comando destructivo", True),
    ("secretos.py",
     lambda p: json.dumps({"tool_name": "Write", "tool_input": {
         "file_path": str(p / "config.py"), "content": _LINEA_CON_CREDENCIAL}}),
     2, "Posible credencial", "bloquea una credencial", True),
    # el revisor escribiendo codigo: tiene que quedar afuera de su docs/revisor/
    ("alcance.py",
     lambda p: json.dumps({"tool_name": "Write", "agent_type": "revisor", "tool_input": {
         "file_path": str(p / "src" / "app.py"), "content": "x"}}),
     2, "Bloqueado por alcance.py", "frena al revisor fuera de docs/revisor/", True),
    # calidad: en un repo sin stack no hay nada que verificar; se prueba que
    # arranque y avise ante una entrada ilegible (bloque D)
    ("verificar.py", lambda p: "{entrada rota",
     1, "AVISO", "arranca y avisa ante una entrada ilegible", False),
]


def probar_hooks(raiz: Path, interprete: str) -> tuple[bool, list[str]]:
    """Corre cada hook con una entrada que tiene que hacerlo reaccionar.

    Devuelve (los de seguridad funcionan, lineas para mostrar). Si falla uno de
    seguridad, el primer valor es False: no hay que escribir settings.json. Si
    falla uno de calidad, la linea es un AVISO y el primer valor no cambia.
    Los hooks se llaman por ruta absoluta y corren contra un proyecto de prueba
    temporal (CLAUDE_PROJECT_DIR): no tocan el repo real.
    """
    seguridad_ok, lineas = True, []
    with tempfile.TemporaryDirectory(prefix="prueba-hooks-") as tmp:
        proyecto = Path(tmp)
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(proyecto)}
        for hook, entrada, esperado, marca, que, de_seguridad in PRUEBAS:
            ok, linea = _probar_uno(Path(raiz).resolve() / ".claude" / "hooks" / hook, interprete,
                                    entrada(proyecto), env, esperado, marca, f"{hook} {que}")
            if not ok and de_seguridad:
                seguridad_ok = False
                linea = f"FALLA: {linea}"
            elif not ok:
                linea = f"AVISO: {linea} (es de calidad: no impide activar los otros)"
            lineas.append(linea)
    return seguridad_ok, lineas


def _probar_uno(ruta: Path, interprete: str, entrada: str, env: dict,
                esperado: int, marca: str, que: str) -> tuple[bool, str]:
    try:
        r = subprocess.run([interprete, str(ruta)], input=entrada.encode("utf-8"),
                           capture_output=True, timeout=30, cwd=env["CLAUDE_PROJECT_DIR"], env=env)
        codigo, err = r.returncode, r.stderr.decode("utf-8", errors="replace").strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        codigo, err = None, f"no se pudo correr: {e}"
    if codigo == esperado and marca in err:
        return True, f"OK: {que} (exit {codigo})."
    return False, (f"{que}: exit {codigo}, se esperaba {esperado} con '{marca}'. {err[:200]}")


def error_sin_interprete() -> str:
    return (
        f"ERROR: ninguno de {', '.join(INTERPRETES)} ejecuta Python en esta maquina.\n"
        "Los hooks no correrian y no bloquearian nada.\n"
        "Instala Python (en Windows, desactiva los alias de la Store en\n"
        "'Alias de ejecucion de aplicaciones') y volve a correr esto."
    )
