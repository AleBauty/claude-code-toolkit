"""
Red de seguridad de .claude/hooks/secretos.py.

Correr desde la raiz del repo:

    python3 tests/test_secretos.py      (o: python tests/test_secretos.py)

Ejecuta el hook real por subprocess, con el mismo JSON que le manda Claude
Code, y compara el exit code: 2 = bloquea, 0 = deja pasar.

Que cubre:
- BLOQUEAR: credenciales con los patrones del hook.
- PERMITIR: placeholders evidentes, archivos de ejemplo y texto normal.
- FALLAR CERRADO: si el hook se rompe (entrada invalida, estructura
  inesperada) bloquea, y el mensaje dice que fallo el hook, no el archivo.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / ".claude/hooks/secretos.py"

# Valores armados por partes A PROPOSITO. Si se escriben como un literal entero,
# secretos.py los detecta y bloquea el Edit/Write de este mismo archivo de test:
# no se puede ni guardarlo. No "limpiarlos" juntando las partes.
CLAVE = "sk-" + "a1B2c3D4e5F6g7H8i9J0k1L2"
TOKEN_GH = "ghp" + "_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4"

BLOQUEAR = {
    "clave tipo sk-": ("config.py", f'cliente = Cliente("{CLAVE}")'),
    "token de GitHub": ("deploy.sh", f"export GH={TOKEN_GH}"),
    "password en texto plano": ("app.py", 'DB_PASSWORD = "' + "s3cr3t0Real99" + '"'),
}

PERMITIR = {
    "texto normal": ("notas.md", "Hoy configuramos el teclado: keyboard = es"),
    "placeholder evidente": ("app.py", 'API_KEY = "<API_KEY>"'),
    "archivo de ejemplo": (".env.example", f"OPENAI_API_KEY={CLAVE}"),
    "contenido vacio": ("vacio.txt", ""),
}

ENTRADAS_ROTAS = {
    "JSON mal formado": "{esto no es json",
    "entrada vacia": "",
    "raiz que no es objeto": "[1, 2]",
    "tool_input que no es objeto": '{"tool_input": "texto"}',
}


# Claude Code manda UTF-8 y lee el mensaje como UTF-8. El hook no puede depender
# de como viene configurado stdin/stderr (en Windows, cp1252): ver SETUP.md,
# "Codificación de los hooks". Sin PYTHONUTF8/PYTHONIOENCODING, como un hook real.
ENV = {k: v for k, v in os.environ.items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}
CON_ACENTOS = "ContraseñaÍNDICE2024"


def correr(entrada: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HOOK)], input=entrada.encode("utf-8"),
                          capture_output=True, env=ENV)


def entrada_write(ruta: str, contenido: str) -> str:
    return json.dumps({"tool_name": "Write",
                       "tool_input": {"file_path": ruta, "content": contenido}})


def main():
    if not HOOK.is_file():
        print(f"ERROR: no encuentro el hook en {HOOK}")
        sys.exit(1)

    total = fallos = 0

    for esperado, casos in ((2, BLOQUEAR), (0, PERMITIR)):
        for nombre, (ruta, contenido) in casos.items():
            total += 1
            r = correr(entrada_write(ruta, contenido))
            if r.returncode != esperado:
                fallos += 1
                print(f"FALLA [{nombre}] esperado={esperado} obtenido={r.returncode}")

    for nombre, entrada in ENTRADAS_ROTAS.items():
        total += 1
        r = correr(entrada)
        err = r.stderr.decode("utf-8", errors="replace")
        # la salida tiene que estar en el mensaje: el que queda trabado no puede abrir otro archivo
        if not (r.returncode == 2 and "secretos.py" in err and "no fue evaluado" in err
                and '"disableAllHooks": true' in err and "settings.local.json" in err):
            fallos += 1
            print(f"FALLA [fallar cerrado] {nombre}: exit={r.returncode} stderr={ascii(err.strip()[:120])}")

    # codificacion: la credencial con acentos se detecta y se muestra sin deformar
    total += 1
    r = correr(entrada_write("config.py", 'DB_PASSWORD = "' + CON_ACENTOS + '"'))
    err = r.stderr.decode("utf-8", errors="replace")
    if not (r.returncode == 2 and CON_ACENTOS in err):
        fallos += 1
        print(f"FALLA [codificacion] exit={r.returncode}, el mensaje no muestra "
              f"{CON_ACENTOS!r} tal cual: {ascii(err.strip()[:150])}")

    print(f"\n{total - fallos}/{total} casos pasan" + (f" - {fallos} FALLAN" if fallos else ""))
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
