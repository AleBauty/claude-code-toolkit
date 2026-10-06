# Sistema nuevo

**Un repo por sistema.** Esta carpeta es la caja de herramientas: los 15
agentes, los hooks y la metodologia. El sistema va en su propio repositorio.

---

## Paso 1 — Requisitos antes de elegir stack

Usar `requisitos`. Que tiene que hacer, criterios de aceptacion, alcance.

Si el alcance no se puede escribir en una linea, no esta claro todavia.
Construir antes de tener claro el requisito es la forma mas cara de
equivocarse.

## Paso 2 — Como se usa, antes de como se construye

Usar `ux-ui`. Que pantallas hay y los 5 estados de cada una que muestra datos:
vacio, cargando, con datos, error, sin permiso.

Va **antes** de `arquitecto`. Decidir el stack sin saber como se usa la
pantalla es descubrir a mitad de camino que el modelo de datos no soporta el
flujo que hacia falta.

## Paso 3 — Panorama de stack, con trade-offs

Usar `arquitecto`. Que opciones existen, que hace cada una, que implica operar
cada una. **La decision la toma el usuario.**

Sesgo del espacio: lo simple primero. Antes de proponer algo complejo,
verificar que el problema lo justifique.

Lo dificil de revertir va a un ADR.

## Paso 4 — Crear el repo

```
python3 nuevo.py ~/repos/<sistema>
```

Copia los 15 agentes, los hooks activos y la metodologia, crea la estructura,
inicia git y commitea **solo el .gitignore** como primer commit.

Despues:

1. Crear el repo remoto y conectarlo.
2. `git check-ignore -v .env` — si no devuelve nada, ese archivo se sube.
3. Probar que los hooks bloquean. Exit code 2, no asumirlo.
4. Abrir Claude Code **en el repo del sistema** y verificar con `/agents`.

## Paso 5 — Completar los datos antes de construir

| Archivo | Que va |
|---|---|
| `datos/stack.csv` | lo decidido. Lo que falta queda en **TBD** |
| `datos/convenciones.md` | estilo del proyecto |
| `datos/adr/` | las decisiones dificiles de revertir |

Mientras `stack.csv` diga TBD, los agentes preguntan en vez de asumir. Es
intencional: un agente que asume stack escribe codigo que hay que tirar.

## Paso 6 — Registrar

Agregar la entrada en `INDICE-SISTEMAS.md`, con la ruta del repo y la version
de la caja de herramientas con la que se creo.
