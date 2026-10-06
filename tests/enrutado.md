# Prueba de enrutado de agentes

Verifica que cada consulta llegue al agente que corresponde, mirando solo las
descripciones (el campo `description:` de `.claude/agents/*.md`), que es lo
único que ve el modelo al enrutar.

> **Advertencia: esto es un chequeo de humo, no una garantía.**
> Un 15/15 en una corrida no prueba que el enrutado sea estable. El modelo que
> enruta no es determinista: en otra pasada puede elegir distinto, sobre todo
> en las consultas ambiguas (A1–A3). En la primera corrida, A3 falló. Un
> resultado limpio quiere decir "no encontramos un problema grueso", no "el
> enrutado está certificado". Si una decisión depende de que el enrutado sea
> confiable, correr la prueba varias veces y mirar en qué casos cambia.

## Cuándo correrla

- Al agregar un agente. **Un agente nuevo entra solo si pasa esta prueba**
  (ver `datos/fuentes.md`, "La razón de parar en 15").
- Al cambiar la `description:` de cualquier agente.
- Si en el uso real un agente empieza a atender cosas que no le tocan.

## Protocolo

1. **Lo esperado se anota ANTES de correr.** Si se escribe después de ver el
   resultado, la prueba no prueba nada.
2. **Enruta un subagente que no escribió las descripciones.** Quien las
   escribió las lee con su intención en la cabeza, no con lo que dicen.
3. **Recibe las descripciones exactas** de los archivos, copiadas tal cual. No
   recibe resúmenes ni el cuerpo de los agentes.
4. **Las consultas van mezcladas y con IDs neutros** (Q1…Q15), sin el grupo y
   sin el agente esperado, ni pistas en el orden.
5. **Si falla un caso, se ajusta la descripción, nunca el caso.** Ajustar el
   caso para que pase es esconder el problema.
6. **Después de un ajuste se corre todo de nuevo**, no solo el caso que falló,
   con un subagente nuevo, sin memoria de la corrida anterior. Un ajuste para
   arreglar un caso puede romper otro.

### Cómo están armadas las consultas

| Grupo | Cantidad | Para qué |
|---|---|---|
| D — descubrimiento | 3 | Que lo claro de un lado llegue |
| R — requisitos | 3 | Que lo claro del otro lado llegue |
| A — ambiguas | 3 | Ninguna dice si ya se decidió construir. La regla: sin decisión explícita, va a `descubrimiento` |
| O — otros agentes | 6 | **La prueba de verdad.** Si `descubrimiento` captura alguna, su descripción es demasiado amplia |

En O hay dos trampas a propósito: O4 dice "¿conviene…?" (vocabulario de
descubrimiento, pero es elegir tecnología dentro de algo ya decidido) y O6
dice "¿llegamos?" (suena a viabilidad, pero es plazo).

## Consultas y agente esperado

| ID | Orden en la corrida | Consulta | Esperado |
|---|---|---|---|
| D1 | Q10 | Tengo una inmobiliaria chica y estoy pensando en hacer un sistema propio para gestionar los alquileres. ¿Vale la pena o hay algo que ya lo resuelva? | descubrimiento |
| D2 | Q5 | Un cliente me pide un CRM a medida para su equipo de ventas de 5 personas. Antes de cotizarlo, ¿le conviene que se lo desarrolle o que use algo como HubSpot? | descubrimiento |
| D3 | Q15 | En el estudio contable pierden varias horas por semana conciliando extractos bancarios a mano. ¿Tiene sentido armar algo para eso o no justifica el esfuerzo? | descubrimiento |
| R1 | Q8 | Ya decidimos desarrollar el sistema de turnos para la clínica. Armá las historias de usuario con criterios de aceptación para el módulo de reserva. | requisitos |
| R2 | Q3 | El cliente aprobó el desarrollo del portal de proveedores. Necesito el SRS con requisitos funcionales y no funcionales. | requisitos |
| R3 | Q13 | En el módulo de facturación que estamos construyendo no está claro qué pasa cuando se anula una factura que ya se envió al cliente. Definamos el comportamiento y los criterios de aceptación. | requisitos |
| A1 | Q2 | Quiero hacer un sistema de turnos para mi consultorio. | descubrimiento |
| A2 | Q12 | Mi viejo tiene una ferretería y quiere una app para controlar el stock. ¿Por dónde empiezo? | descubrimiento |
| A3 | Q7 | Necesito una herramienta para que los profesores de la facultad carguen las notas. ¿Me ayudás a definirla? | descubrimiento |
| O1 | Q4 | El listado de pedidos tarda 12 segundos en cargar. El EXPLAIN muestra un seq scan sobre la tabla pedidos, que tiene 3 millones de filas. | base-datos |
| O2 | Q14 | El deploy a producción falla: el contenedor arranca y se reinicia en loop con "connection refused" al conectarse a la base. | infraestructura |
| O3 | Q11 | Necesito un componente de selector de fechas accesible en React para el formulario de reserva, con mensajes de error y navegación por teclado. | frontend |
| O4 | Q1 | Para el sistema de turnos que ya decidimos construir, ¿conviene usar Firebase o armar nuestro propio backend con Postgres? Somos dos desarrolladores. | arquitecto |
| O5 | Q9 | Encontré que cualquier usuario logueado puede ver las facturas de otro cambiando el id en la URL /facturas/123. | seguridad |
| O6 | Q6 | El cliente quiere el portal para el 15 de diciembre. ¿Llegamos? Partime el trabajo y estimá en rangos. | gestion-entrega |

## Prompt del subagente

Se usó un subagente `general-purpose`. Para repetir la prueba, reemplazar
`<DESCRIPCIONES>` por la salida del comando de abajo, y `<CONSULTAS>` por las
consultas de la tabla en el orden de la columna "Orden en la corrida", con el
formato `- Q1: ...`.

```
Sos el enrutador de un equipo de 15 agentes especializados en desarrollo de
software. Para cada consulta de usuario, elegí UN solo agente: el que debería
atenderla primero. Decidí solo a partir de las descripciones de abajo.

Reglas:
- No uses herramientas. No leas archivos. Usá únicamente las descripciones que
  están en este mensaje (si en tu entorno ves otras definiciones de agentes,
  ignoralas).
- Exactamente un agente por consulta, con el nombre tal cual aparece en la lista.
- Respondé con una tabla markdown con columnas: ID | agente elegido | motivo
  (una línea). Nada más.

## Agentes

<DESCRIPCIONES>

## Consultas

<CONSULTAS>
```

Para sacar las descripciones exactas (desde la raíz del repo, en bash):

```bash
for f in .claude/agents/*.md; do
  echo "- **$(basename "$f" .md)**: $(grep -m1 '^description:' "$f" | sed 's/^description: //')"
done
```

## Resultados

### 2026-10-05 — alta de `descubrimiento` (agente 15)

| ID | Esperado | Corrida 1 | Corrida 2 |
|---|---|---|---|
| D1 | descubrimiento | descubrimiento | descubrimiento |
| D2 | descubrimiento | descubrimiento | descubrimiento |
| D3 | descubrimiento | descubrimiento | descubrimiento |
| R1 | requisitos | requisitos | requisitos |
| R2 | requisitos | requisitos | requisitos |
| R3 | requisitos | requisitos | requisitos |
| A1 | descubrimiento | descubrimiento | descubrimiento |
| A2 | descubrimiento | descubrimiento | descubrimiento |
| A3 | descubrimiento | **requisitos ✗** | descubrimiento |
| O1 | base-datos | base-datos | base-datos |
| O2 | infraestructura | infraestructura | infraestructura |
| O3 | frontend | frontend | frontend |
| O4 | arquitecto | arquitecto | arquitecto |
| O5 | seguridad | seguridad | seguridad |
| O6 | gestion-entrega | gestion-entrega | gestion-entrega |
| | | **14/15** | **15/15** |

En las dos corridas, ninguna de las 6 consultas de otros agentes (O1–O6) cayó
en `descubrimiento`, incluidas las dos trampas.

**Falla de A3 en la corrida 1.** El subagente justificó: "la necesidad está
planteada y pide definir qué tiene que hacer la herramienta". Leyó "necesito"
como si la decisión ya estuviera tomada, y "definirla" coincidió con el "Define
QUÉ" de `requisitos`. Hubo dos causas en las descripciones:

1. `requisitos` no exigía que la decisión de construir fuera **explícita**, y su
   cláusula "cuando una funcionalidad no está clara" servía para cualquier pedido.
2. `descubrimiento` no decía que es el punto de entrada para un pedido de
   sistema nuevo.

**Qué se cambió (en las descripciones, no en el caso):**

- `requisitos`: "Usar **solo cuando la decisión de construir está explícita**
  (aprobado, decidido, en construcción), o para una funcionalidad no clara de un
  sistema **que ya se está construyendo**. Un pedido de un sistema o herramienta
  nueva sin esa decisión explícita, aunque pida 'definirlo', va primero a
  descubrimiento."
- `descubrimiento`: "Es el punto de entrada para toda idea o pedido de un
  **sistema, app o herramienta nueva** […] mientras nadie haya decidido
  explícitamente construirlo." Se limita a sistemas nuevos, no a componentes ni
  a cosas en construcción, para no agrandarlo hacia los otros agentes. También
  se agregaron dos exclusiones que lo achican: "no elige tecnologías de algo ya
  decidido (arquitecto) ni estima plazos (gestion-entrega)".

La corrida 2 se hizo con un subagente nuevo, sobre las 15 consultas completas.

**Lo que este resultado no dice:** A3 pasó de fallar a pasar con un cambio de
redacción. Eso muestra que el caso está cerca del límite entre los dos
agentes, y que en otra pasada puede volver a caer en `requisitos`. Si en el
uso real `requisitos` empieza a recibir ideas que nadie evaluó, este es el
primer lugar donde mirar.
