# ADR — registros de decisiones de arquitectura

Una decisión difícil de revertir, un archivo. Numerados: `001-titulo.md`.

Sin esto, en tres meses nadie recuerda por qué se eligió X sobre Y y se
rediscute la misma decisión.

## Plantilla

```markdown
# ADR-001: <decisión en una línea>

Fecha: YYYY-MM-DD
Estado: propuesto | aceptado | reemplazado por ADR-XXX

## Contexto
Qué problema hay. Qué restricciones aplican (plazo, equipo, presupuesto, volumen).

## Opciones consideradas
### A — <nombre>
Pros / contras reales.
### B — <nombre>
Pros / contras reales.

## Decisión
Cuál se eligió y por qué. Qué pesó más.

## Consecuencias
Qué habilita. Qué cierra. Qué deuda genera. Qué hay que vigilar.
```

Un ADR no se edita cuando la decisión cambia: se escribe uno nuevo que lo
reemplaza, y el viejo pasa a estado "reemplazado". El historial de por qué se
cambió de opinión tiene valor.
