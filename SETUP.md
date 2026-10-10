# Tarea de setup — ejecutar una sola vez

> **Para el usuario:** abrí Claude Code en esta carpeta y escribí:
> `Leé SETUP.md y ejecutalo`

---

## Instrucciones para Claude

Tarea guiada. **Preguntá antes de cada instalación** y mostrá el comando.
No instales nada sin confirmación. Llevá lista de tareas visible.

### Paso 0 — Diagnóstico

```bash
uname -a 2>/dev/null || ver
python --version 2>/dev/null || python3 --version
node --version 2>/dev/null
git --version
code --version
```

Mostrá qué está y qué falta. **Los hooks necesitan Python** — si no está,
avisalo: sin Python no hay verificación automática.

### Paso 1 — Activar los hooks

Esto es lo más importante del setup.

```bash
python3 activar-hooks.py
```

En Windows suele ser `python activar-hooks.py`.

Escribe `.claude/settings.json` con el intérprete que funciona en esta máquina
(prueba `python3` y `python`, y mira la salida, no solo el exit code). Ese
archivo no se versiona: depende de cada máquina. Si no encuentra Python, falla
con un mensaje en vez de dejar hooks muertos.

Probá que funcionan antes de seguir, con el intérprete que informó el script:

```bash
echo '{"tool_input":{"command":"rm -rf /tmp/prueba"}}' | python3 .claude/hooks/proteger.py
```

Tiene que imprimir "Comando bloqueado" y salir con código 2. Si sale 0, el hook
no está funcionando.

Avisale al usuario que a partir de ahora:
- los comandos destructivos quedan bloqueados
- si escribe una credencial en un archivo, se bloquea
- si el lint o el typecheck fallan tras una edición, se bloquea hasta corregir

Y que si un hook molesta, se ajusta editando el script correspondiente.

### Paso 2 — Git

Si no hay repositorio:

```bash
git init
```

El `.gitignore` ya está y cubre credenciales. Primer commit.

### Paso 3 — Extensiones de VS Code

Si `code` está disponible, ofrecé las que apliquen al stack. Como todavía está
en TBD, por ahora solo las generales:

```bash
code --install-extension ms-python.python
code --install-extension mechatroner.rainbow-csv
code --install-extension eamodio.gitlens
```

Las específicas (ESLint, Prettier, Prisma, etc.) se instalan cuando se defina el
stack. Si un ID falla, decile que la busque por nombre; no inventes otro ID.

### Paso 4 — Verificación

```bash
python .claude/hooks/verificar.py < /dev/null
git status --short
ls .claude/agents/ | wc -l
```

Tienen que aparecer 15 agentes.

Probá que leen el contexto. Pedile al usuario que escriba:

```
¿Qué agentes hay y en qué orden conviene usarlos?
```

Debería nombrar el flujo descubrimiento → requisitos → arquitecto → construcción → verificación.

### Paso 5 — Cierre

Resumen de qué quedó, qué falta y por qué.

**Recordale que el stack está en TBD.** El próximo paso real es definir qué se
va a construir: ahí entra el agente `requisitos` y después `arquitecto`.

---

## Notas

- Si algo falla, decilo. No lo ocultes ni lo des por hecho.
- Adaptá los comandos al sistema operativo detectado en el paso 0.

### Si los hooks no bloquean

No editar `settings.json` a mano: volver a correr `activar-hooks.py`, que elige
el intérprete que funciona. Después repetir la prueba de bloqueo.

El síntoma de que no andan no es un error: es que **no bloquean nada**. Por eso
la prueba no es opcional.

### Si un hook bloquea todo

`proteger.py` y `secretos.py` fallan cerrado: si el hook mismo se rompe, bloquea
en vez de dejar pasar. El mensaje empieza con `FALLO EL HOOK`, y eso quiere
decir que el problema es el hook, no tu comando ni tu archivo.

Si eso pasa con todo, Claude no puede arreglarlo: el hook corre antes que
cualquier Bash, PowerShell, Edit o Write, incluidos los que lo arreglarían.
Hay que salir a mano:

1. Fuera de Claude Code (con el editor), crear o editar
   `.claude/settings.local.json` y poner:

   ```json
   { "disableAllHooks": true }
   ```

   Se aplica en la sesión abierta, sin reiniciar. Usar `settings.local.json`
   y no `settings.json`: está ignorado por git y `activar-hooks.py` no lo pisa.
2. Con los hooks apagados, arreglar el script que falla. Mientras tanto
   **no hay ninguna protección**: nada de comandos destructivos ni credenciales.
3. Volver a activarlos: sacar `disableAllHooks` (o ponerlo en `false`) y
   repetir la prueba de bloqueo del paso 1.
