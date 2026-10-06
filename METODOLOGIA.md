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
