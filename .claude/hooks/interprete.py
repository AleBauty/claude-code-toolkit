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


def probar_proteger(raiz: Path, interprete: str) -> tuple[bool, str]:
    """Le manda a proteger.py un comando destructivo y confirma que bloquea (exit 2).

    El JSON se arma aca y no en una linea de shell: un comando de shell que lo
    contenga escrito lo bloquea el propio hook antes de que llegue a correr.
    La ruta es absoluta: no depende del directorio desde donde se llame.
    """
    hook = Path(raiz).resolve() / ".claude" / "hooks" / "proteger.py"
    entrada = json.dumps({"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/prueba"}})
    try:
        r = subprocess.run([interprete, str(hook)], input=entrada.encode("utf-8"),
                           capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, f"no se pudo correr {hook}: {e}"
    if r.returncode == 2:
        return True, "OK: proteger.py bloquea un comando destructivo (exit 2)."
    err = r.stderr.decode("utf-8", errors="replace").strip()
    return False, (f"FALLA: proteger.py no bloqueo un comando destructivo "
                   f"(exit {r.returncode}, se esperaba 2). {err[:300]}")


def error_sin_interprete() -> str:
    return (
        f"ERROR: ninguno de {', '.join(INTERPRETES)} ejecuta Python en esta maquina.\n"
        "Los hooks no correrian y no bloquearian nada.\n"
        "Instala Python (en Windows, desactiva los alias de la Store en\n"
        "'Alias de ejecucion de aplicaciones') y volve a correr esto."
    )
