# Bitacora — claude-code-toolkit

## Estado actual

<!-- 3 a 6 lineas. Se REESCRIBE, no se acumula: etapa, que esta bloqueado y
     esperando que. Es lo unico que se lee en cada sesion. -->
- Etapa: caja con traspaso entre agentes (§11), bitácora (§12), `alcance.py` y `estado.py`; `actualizar.py` lleva todo a los repos generados.
- **Pendiente:** prueba de punta a punta de `alcance.py` con el `revisor` real, en la primera sesión reiniciada: escribir en `docs/revisor/` tiene que pasar; en `src/`, bloquearse con "Bloqueado por alcance.py". En la sesión que lo creó no se pudo: los agentes se cargan al arrancar.
- **Pendiente:** automatizacion no recibió ninguno de los arreglos de hoy, ni los de la auditoría de hooks. Correr `actualizar.py` desde su sesión, mirando antes su `git status`.
- **Pendiente:** stocky está en `17a2971`: le faltan `alcance.py`, `estado.py`, el traspaso de los 9 agentes y la §11/§12. Mismo camino.

## Decisiones cerradas

<!-- Una linea por decision: "- AAAA-MM-DD — decision". Solo lo que no se
     vuelve a discutir. -->
- 2026-10-06 — `INDICE-SISTEMAS.md` no se versiona: tiene rutas locales y nombres de clientes, y este repo es público. Se versiona la plantilla `.example`.
- 2026-10-06 — `descubrimiento` es el paso 0: decide *si* se construye, antes de `requisitos`.
- 2026-10-10 — Los hooks se configuran con ruta absoluta: `"${CLAUDE_PROJECT_DIR}/.claude/hooks/x.py"`, entre comillas.
- 2026-10-10 — Hooks de SEGURIDAD (`proteger.py`, `secretos.py`, `alcance.py`) fallan cerrado: ante cualquier error salen con 2, y la salida de un bloqueo por bug (`disableAllHooks` en `settings.local.json`) va en el propio mensaje. Hooks de CALIDAD (`verificar.py`, `estado.py`) avisan con exit 1 y nunca bloquean. No unificar los dos criterios.
- 2026-10-10 — Los hooks leen stdin como bytes UTF-8 y escriben stderr en UTF-8: que funcionen por diseño, no por cómo viene configurado el entorno.
- 2026-10-10 — El aviso de "no hay `settings.json`" es una instrucción en `CLAUDE.md`, no un hook: un aviso en shell tendría el mismo modo de falla que vino a resolver, y es un recordatorio, no un control que evita daño.
- 2026-10-10 — `secretos.py` no ve lo que se escribe por Bash: límite del enfoque, documentado, no bug.
- 2026-10-10 — Los comentarios y mensajes de los hooks se explican solos: `SETUP.md` y `tests/` no viajan a los repos generados, solo valen como puntero a esta caja.
- 2026-10-11 — `actualizar.py` decide por dueño, no por archivo: lo de la caja se sobrescribe, lo del repo no se toca, `.env.example` y `BITACORA.md` se crean si faltan y no se pisan nunca.
- 2026-10-11 — `nuevo.py` valida todo antes de crear, no saltea nada en silencio y verifica lo que afirma al terminar.
- 2026-10-11 — Probar un hook es exigir el exit esperado **y** una marca de su mensaje propio: un exit 2 solo no prueba nada.
- 2026-10-11 — `activar-hooks.py` prueba primero y escribe `settings.json` después.
- 2026-10-11 — Regla de traspaso (§11) en 9 agentes: salida completa en `docs/<agente>/`, al orquestador solo un puntero.
- 2026-10-11 — `revisor` y `seguridad` tienen Write, limitado por `alcance.py` a `docs/<agente>/`. Bash no se cierra. Si el costo molesta, fusionar con `secretos.py`, no sacar el chequeo.
- 2026-10-11 — No hay hook Stop que escriba la bitácora (ADR-001). Sí hay `estado.py` (SessionStart), que la lee.
- 2026-10-11 — Un test nuevo que pasa de entrada se verifica rompiendo a propósito lo que debería detectar.

## Historico

<!-- Append-only, lo nuevo arriba. "### AAAA-MM-DD — tema": que se hizo, y
     "  - No sirvio: ... (por que)". Se lee solo cuando se pregunta por algo viejo. -->

### 2026-10-11 — Traspaso, bitácora, `alcance.py` y `estado.py`

- Regla de traspaso en `METODOLOGIA.md` §11 y en 9 agentes, vigilada por `tests/test_traspaso.py`. Bitácora en §12, con plantilla en `nuevo.py`, calcada de la que stocky escribió a mano. `alcance.py` limita la escritura de `revisor` y `seguridad`. `estado.py` inyecta el Estado actual al abrir la sesión.
  - No sirvió: el hook Stop que iba a escribir el "rastro mecánico". Solo podía anotar lo que ya está en git, y costaba mucho (ADR-001).
  - No sirvió: dar por bueno el `agent_type` documentado sin verlo. Se verificó en vivo con un hook temporal: llegó `"revisor"`.
  - No sirvió: probar `alcance.py` con el `revisor` real en la misma sesión. Las definiciones de agentes se cargan al arrancar y el `revisor` todavía no tenía Write.
  - No sirvió: `os.path.commonpath()` con una ruta en otra unidad de Windows. Lanzaba `ValueError`, y el mensaje decía "FALLO EL HOOK" en vez de un bloqueo normal, lo que invita a desactivarlo.
  - No sirvió: dar Write a `revisor` y `seguridad` escribiendo por Bash (heredoc). Habría esquivado `secretos.py`, justo en el agente que cita credenciales.

### 2026-10-11 — `nuevo.py`, `actualizar.py` y `activar-hooks.py`: nada en silencio

- Validación antes de crear, verificación al terminar, prueba de los tres hooks, `actualizar.py` por dueño.
  - No sirvió (falso OK): la prueba de `proteger.py` aceptaba cualquier exit 2. Sin el archivo, Python sale con 2 ("can't open file"), así que con `proteger.py` ausente decía "OK: proteger.py bloquea" y escribía `settings.json`. Ahora se exige además la marca del mensaje propio.
  - No sirvió: validar una carpeta con "tiene algo": `__pycache__` cuenta como algo, y con 0 agentes `0 == 0` pasaba como éxito.
  - No sirvió: `activar-hooks.py` escribía `settings.json` y después probaba. Si la prueba fallaba, quedaba un repo que afirmaba hooks activos.
  - No sirvió: `nuevo.py` salteaba en silencio lo que faltaba. `.env.example` no existía en la caja y ningún repo lo recibió.

### 2026-10-10 — Auditoría de hooks (bloques A a E) y propagación

- Rutas absolutas, fallo cerrado, UTF-8 explícito, `verificar.py` con raíz y aviso, límites documentados.
  - No sirvió: las rutas relativas en `settings.json`. En la sesión de stocky, al cambiar el directorio de trabajo, Python no encontraba el hook, salía con 2 y quedaron bloqueados todos los Bash, PowerShell, Edit y Write, sin un mensaje que explicara la causa.
  - No sirvió: hooks de seguridad que salían con 0 (JSON inválido) o con 1 (excepción). En los dos casos la acción pasaba.
  - No sirvió: el bloque C (UTF-8) dejó `verificar.py` afuera. Lo encontró la actualización de stocky: con una "Í" podía salir con 0 sin verificar nada. Se arregló aparte (`287a456`).
  - No sirvió: `activar-hooks.py` imprimía un comando de prueba con el patrón destructivo escrito en la línea. El propio hook lo bloqueaba, y además usaba ruta relativa. Ahora la prueba la corre el script.
  - La sospecha de que `cp1252` hacía que `secretos.py` dejara pasar credenciales en archivos con "Í" no se reprodujo (`surrogateescape`). Igual se pasó a UTF-8 explícito: detalle en `SETUP.md`.

### 2026-10-05 — Creación de la caja

- Agentes, hooks, metodología, `nuevo.py`.
  - No sirvió: `write_text` sin `encoding` en `nuevo.py`. Con `cp1252`, un carácter dejaba el `CLAUDE.md` generado con UTF-8 inválido (`970387f`).
  - No sirvió: un `git rebase --root` en automatizacion con los hooks activos. Llevó la carpeta a un commit sin `.claude/hooks/`: Python salía con 2 y quedó bloqueado todo Bash y PowerShell, incluido el comando para deshacerlo. Se salió desde una terminal propia. La regla quedó en `CLAUDE.md` (`8639c4d`).
