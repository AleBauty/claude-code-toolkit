# ADR-001: No automatizar la bitácora con un hook Stop

Fecha: 2026-10-11
Estado: aceptado

## Contexto

`BITACORA.md` (METODOLOGIA.md §12) registra en qué está el trabajo, qué se
decidió y qué se intentó y no sirvió. Lo escribe el orquestador, y lo que no se
escribe se pierde cuando la sesión se cierra.

Se propuso un hook `Stop` que escribiera en la bitácora "el rastro mecánico" de
cada sesión, con la ventaja de que un hook no se olvida. Antes de construirlo
se averiguó, en la documentación de hooks, qué puede saber de verdad:

- `Stop` recibe por stdin `session_id`, `transcript_path`, `cwd`,
  `permission_mode`, `hook_event_name`, `stop_hook_active` y
  `last_assistant_message`. **No recibe la lista de archivos tocados ni de
  herramientas usadas.**
- El transcript es un formato interno, sin documentar, y se escribe con
  retraso: no sirve como fuente.
- Lo único confiable es git: commits de la sesión y archivos sin commitear.

## Opciones consideradas

### A — Hook Stop que anota commits y archivos sin commitear

Contras, todos reales:

- **Duplica `git log`.** Lo único que puede anotar ya está en git.
- **Corre en cada turno, no por sesión.** Necesita guardar estado entre turnos
  en una carpeta temporal para reescribir una sola entrada por sesión.
- **Necesita un SessionStart solo para la foto inicial.** Sin saber cómo estaba
  el repo al empezar, no distingue lo de esta sesión de lo que ya estaba sucio,
  o pierde lo que cambió en el primer turno.
- **Ensucia el árbol en cada sesión.** Escribe en un archivo versionado, así que
  `actualizar.py` se niega a correr hasta que se commitee.
- **Un exit 2 por un bug arma un bucle:** en `Stop`, el exit 2 hace que Claude
  siga trabajando en lugar de terminar.

### B — Sin hook: la bitácora la escribe el orquestador

Lo que de verdad se olvida es el **por qué** y el **"no sirvió"**, y eso un
hook no lo puede saber: lo escribe el orquestador o no existe. Lo mecánico ya
está en git.

## Decisión

**B.** No se construye el hook Stop. Fue una decisión tomada y después
revertida: se eligió A cuando se creía que el hook anotaría algo que no estaba
en otro lado; la averiguación mostró que no.

Es mucha maquinaria para duplicar `git log`: el sobredimensionar que
`METODOLOGIA.md` pide evitar.

## Consecuencias

- La bitácora depende de que el orquestador la escriba al cerrar un tramo de
  trabajo. Es una regla de proceso (METODOLOGIA.md §12), no un control.
- **Sí se construye `estado.py`, un hook SessionStart**, porque resuelve otra
  cosa: que la sesión **lea** el Estado actual al arrancar sin que nadie se
  acuerde de pedírselo. Leer es mecánico y barato; escribir el por qué, no.
- Si alguien lee METODOLOGIA.md §12 y piensa que "falta automatizar la
  bitácora": este ADR es la respuesta. Para reabrirlo hace falta que el hook
  pueda saber algo que no esté en git.
