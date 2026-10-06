"""
Deteccion del interprete de Python para los hooks. No es un hook.

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


def error_sin_interprete() -> str:
    return (
        f"ERROR: ninguno de {', '.join(INTERPRETES)} ejecuta Python en esta maquina.\n"
        "Los hooks no correrian y no bloquearian nada.\n"
        "Instala Python (en Windows, desactiva los alias de la Store en\n"
        "'Alias de ejecucion de aplicaciones') y volve a correr esto."
    )
