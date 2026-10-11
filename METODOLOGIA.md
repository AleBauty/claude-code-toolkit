# Metodología

Reglas de proceso. Aplican a **todos** los agentes de esta carpeta, sin excepción.

Inspiradas en la metodología de `obra/superpowers`, adaptadas a este contexto.

---

## 1. Evidencia sobre afirmaciones

**No declares nada terminado sin haberlo verificado.**

Prohibido decir "listo", "funciona" o "corregido" sin haber corrido algo que lo
demuestre. Si no pudiste verificar, la frase correcta es: *"escribí X, no lo pude
probar porque Y"*.

Formas válidas de verificar, según el caso:
- El test pasa (y lo viste pasar)
- El compilador/type checker no da error
- El linter no se queja
- El endpoint responde lo esperado
- La migración corre y se puede revertir

"Lo revisé y está bien" no es verificación.

## 2. TDD cuando hay lógica real

Para lógica de negocio, cálculos, validaciones y transformaciones de datos:

1. **RED** — escribir el test primero y **verlo fallar**. Si pasa de entrada, el
   test está mal escrito.
2. **GREEN** — el código mínimo que lo hace pasar.
3. **REFACTOR** — limpiar con el test en verde.
4. Commit.

No aplica a todo: maquetado visual, configuración y scripts de una sola vez no
necesitan TDD. Usar criterio y decir cuándo se decide no aplicarlo.

## 3. Baseline antes de empezar

Antes de tocar código en un proyecto existente: **correr los tests y anotar el
estado**. Si ya había 3 fallando, eso no lo rompiste vos — pero hay que saberlo
de antemano para no perseguir un fantasma.

## 4. Un cambio por vez

Si cambiás dos cosas y algo se rompe, no sabés cuál fue. Aplica a código,
configuración, dependencias y constantes.

## 5. Causa raíz, no síntoma

Cuando algo falla:
1. Reproducir el fallo de forma consistente.
2. Encontrar **por qué** pasa, no dónde se manifiesta.
3. Arreglar la causa.
4. Agregar un test que lo cubra para que no vuelva.

Un `try/catch` que silencia el error no es un arreglo: es esconder el problema.

## 6. Revisión con ojos frescos

El código importante lo revisa un agente que **no lo escribió**. Un autor
revisando su propio trabajo repite sus propios supuestos.

Hallazgos ordenados por severidad:
- **Bloqueante** — no se mergea así. Bug, agujero de seguridad, pérdida de datos.
- **Importante** — se arregla antes de cerrar la tarea.
- **Sugerencia** — mejora, no bloquea.

## 7. Decisiones registradas

Toda decisión de arquitectura que sea difícil de revertir va a un ADR en
`datos/adr/`. Formato: contexto, opciones consideradas, decisión, consecuencias.

Sin esto, en tres meses nadie se acuerda por qué se eligió Postgres sobre Mongo,
y se rediscute.

## 8. Honestidad sobre los límites

- Si no podés verificar algo, decilo. No lo presentes como hecho.
- Si una librería o API puede haber cambiado, buscá la documentación actual en
  vez de responder de memoria.
- Si no entendés el requisito, preguntá antes de construir. Código que resuelve
  el problema equivocado es peor que no haber hecho nada.
- Si una decisión no conviene a largo plazo, decilo aunque no lo hayan preguntado.

## 9. Regla anti-dependencia

Este espacio es para aprender, no solo para producir.

**Para lo que el usuario ya puede hacer: preguntá qué intentó antes de resolverlo.**
Mostrá el error, señalá la línea, explicá el porqué — no entregues la solución
completa.

**Para terreno nuevo:** mostrá el panorama primero. Qué opciones existen, qué hace
cada una, sus trade-offs. La decisión la toma él.

Si el usuario pide explícitamente la solución directa, dásela: su pedido del
momento pisa esta regla.

## 10. Seguridad desde el principio

- Credenciales **nunca** en archivos versionados. Van en `.env`, siempre en
  `.gitignore`.
- Validar toda entrada que venga de afuera.
- Consultas parametrizadas, nunca concatenación de strings en SQL.
- Dependencias: revisar que no tengan vulnerabilidades conocidas antes de sumarlas.

Agregar seguridad al final cuesta diez veces más que hacerlo bien desde el inicio.

## 11. Traspaso entre agentes

Un agente encuentra 14 cosas con detalle; si el orquestador lo resume para
pasárselo al siguiente, el detalle se pierde. Y lo que se intentó y no sirvió
vive solo en el chat: cuando la sesión se cierra, desaparece. Por eso los
agentes que producen análisis dejan su salida en un archivo y devuelven un
puntero. Esta es la regla, y va copiada tal cual en cada uno de esos agentes
(`tests/test_traspaso.py` del repo claude-code-toolkit vigila que no se
desincronice):

<!-- traspaso:inicio -->
Tu salida completa va a un archivo, no al chat. El orquestador no la resume:
le pasa al siguiente agente la ruta, y el siguiente lee el archivo.

1. Escribí todo lo que encontraste en `docs/<tu-nombre>/<AAAA-MM-DD>-<tema>.md`
   (por ejemplo `docs/revisor/2026-10-11-login.md`). Un directorio por agente:
   dos agentes en paralelo no se pisan. Si el archivo ya existe, agregá `-2`,
   `-3`: nunca pises uno anterior.
2. Incluí también lo que probaste y no sirvió, y por qué. Eso no queda en
   ningún otro lado.
3. Devolvé al orquestador solo esto:

       Detalle: docs/<tu-nombre>/<archivo>.md
       Conteo: <n> críticos, <n> altos, <n> medios, <n> bajos
       Más grave: <una línea por cada crítico o alto, máximo 3>

   Si tu trabajo no se mide por severidad, el conteo va por tipo
   (por ejemplo: 9 historias, 4 preguntas abiertas que bloquean).
4. Si te pasan una ruta de otro agente, leé el archivo completo. No trabajes
   sobre un resumen.
<!-- traspaso:fin -->

**El orquestador** (la sesión principal, que no es un agente) al delegar pasa
rutas, no resúmenes. Lo que le muestra al usuario sale del puntero: el conteo
y lo más grave, con la ruta para ver el resto.

**Quiénes la llevan:** `revisor`, `seguridad`, `qa`, `requisitos`, `ux-ui`,
`arquitecto`, `gestion-entrega`, `descubrimiento` y `datos-analitica`. Producen
análisis que otro agente consume. Los ADR de `arquitecto` siguen en
`datos/adr/`: el archivo de traspaso es el análisis, el ADR es la decisión.

**Quiénes no:** `backend`, `frontend`, `mobile`, `base-datos`,
`infraestructura` y `documentacion`. Su producto ya es un archivo del repo
(código, migraciones, configuración, documentos) y lo que devuelven es corto.

**Alcance de escritura.** `revisor` y `seguridad` tienen Write solo para dejar
su salida en `docs/<su-nombre>/`. El hook `alcance.py` bloquea cualquier Edit o
Write suyo fuera de esa carpeta: el revisor no escribe lo que revisa. Límite
conocido: también tienen Bash y podrían escribir por ahí. No se cierra a
propósito: el riesgo real es editar código por error, y para eso se usa Write;
cerrar Bash rompería los greps y los tests que necesitan.

No escriben por Bash (heredoc) en lugar de Write: `secretos.py` corre en
Edit|Write y no en Bash, así que eso esquivaría el único hook que impide
filtrar una credencial, justo en el agente que cita las que encontró.

## 12. Bitácora

Cada repo de trabajo tiene un `BITACORA.md` en la raíz (lo crea `nuevo.py`; a
los repos anteriores se lo agrega `actualizar.py`, sin pisar uno que ya
exista). El `git log` dice qué quedó; nada más dice qué se probó y se descartó,
ni en qué quedó el trabajo. Para eso es la bitácora. Tres secciones:

- **Estado actual** — 3 a 6 líneas. Se **reescribe**, no se acumula: en qué
  etapa está, qué está bloqueado y esperando qué.
- **Decisiones cerradas** — una línea por decisión, con fecha
  (`- AAAA-MM-DD — decisión`). Solo lo que no se vuelve a discutir.
- **Historico** — append-only, lo nuevo arriba (`### AAAA-MM-DD — tema`). Qué
  se hizo, qué se intentó y **no sirvió, y por qué**.

**Qué se lee y cuándo.** Solo el Estado actual se lee siempre: el hook
`estado.py` lo inyecta al abrir la sesión (y al retomarla, después de `/clear`
y después de compactar). El Histórico se lee cuando alguien pregunta por algo
viejo. Si se leyera entero en cada sesión, la bitácora sería un impuesto fijo
de contexto. Por lo mismo, si el Estado actual pasa de 1500 caracteres,
`estado.py` lo corta y avisa: hay que reescribirlo, no dejarlo crecer.

**Quién la escribe.** El orquestador, al cerrar un tramo de trabajo:
reescribe el Estado actual, agrega las decisiones que se cerraron y anota en el
Histórico lo que se hizo y lo que no sirvió. Los agentes no la tocan: su
detalle va en `docs/<agente>/` (§11), y la bitácora apunta ahí.

**No se automatiza la escritura.** Un hook no puede saber el por qué ni el "no
sirvió", y lo mecánico (commits, archivos tocados) ya está en git. Por qué se
descartó un hook que la escribiera: ADR-001 en `datos/adr/` del repo
claude-code-toolkit.
