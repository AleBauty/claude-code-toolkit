# Sistemas — desarrollo de software

**Esta carpeta es la caja de herramientas, no un repo de trabajo.** Acá viven
los 14 agentes, los hooks y la metodología. Cada sistema va en **su propio
repositorio**, afuera de acá.

Sistema nuevo: `python3 nuevo.py ~/repos/<sistema>`. Eso copia los agentes y
los hooks activos al repo nuevo, porque Claude Code lee `.claude/` de la
carpeta donde se abre: sin esa copia, el repo del sistema no tiene agentes ni
hooks.

El proceso completo está en `COMO-CREAR-SISTEMA.md`.

## Antes de responder

1. **`METODOLOGIA.md`** — reglas de proceso. Aplican siempre, a todos los agentes.
2. `datos/stack.csv` — decisiones técnicas tomadas. **Si dice TBD, preguntá.**
3. `datos/convenciones.md` — estilo del proyecto. Consistencia antes que
   preferencia personal.
4. `datos/adr/` — por qué se decidió lo que se decidió.

## Agentes

**Antes de escribir código**

| Agente | Para qué |
|---|---|
| `requisitos` | Qué tiene que hacer el sistema, criterios de aceptación, alcance |
| `ux-ui` | Cómo se usa antes de cómo se construye. Los 5 estados de cada pantalla |
| `arquitecto` | Stack, estructura, límites entre componentes, ADRs |

**Construcción**

| Agente | Para qué |
|---|---|
| `backend` | APIs, lógica de negocio, integraciones |
| `frontend` | UI web, componentes, estado, accesibilidad |
| `mobile` | Apps móviles — React Native, Flutter, nativo |
| `base-datos` | Modelado transaccional, migraciones, índices, consultas lentas |
| `datos-analitica` | Modelado analítico, métricas, dashboards. **No es `base-datos`** |

**Verificación**

| Agente | Para qué |
|---|---|
| `qa` | Tests, casos borde, cobertura |
| `revisor` | Revisión con ojos frescos, por severidad |
| `seguridad` | Autenticación, autorización, secretos, dependencias |

**Operación y comunicación**

| Agente | Para qué |
|---|---|
| `infraestructura` | Despliegue, CI/CD, contenedores, observabilidad |
| `documentacion` | README, API, ADRs, guías |
| `gestion-entrega` | Partir el trabajo, estimar en rangos, nombrar riesgos, alcance |

## Orden que evita retrabajo

```
requisitos → ux-ui → arquitecto → base-datos → backend/frontend/mobile
                                                    ↓
                                      qa → revisor → seguridad
                                                    ↓
                                infraestructura → documentacion

gestion-entrega y datos-analitica entran cuando hacen falta:
  gestion-entrega  → al planificar y cuando el alcance se mueve
  datos-analitica  → cuando el sistema tiene que responder preguntas, no solo operar
```

No es rígido, pero **construir antes de tener claro el requisito** es la forma
más cara de equivocarse.

El `revisor` trabaja con ojos frescos: no debe ser el mismo agente que escribió
el código.

**`ux-ui` va antes de `arquitecto`, no después.** Decidir el stack sin saber
cómo se usa la pantalla es la forma de descubrir a mitad de camino que el
modelo de datos no soporta el flujo que hacía falta.

**`base-datos` y `datos-analitica` no son el mismo agente.** El primero
optimiza para transacciones (escribir rápido, consistencia, un registro por
vez); el segundo para preguntas (leer mucho, agregar, histórico). El mismo
esquema casi nunca sirve bien para las dos cosas, y mezclarlos es lo que hace
que el dashboard tire abajo la base de producción.

## Hooks — verificación que no depende del modelo

En `.claude/hooks/` hay tres scripts que corren automáticamente:

| Hook | Cuándo | Qué hace |
|---|---|---|
| `verificar.py` | después de Edit/Write | corre lint y typecheck; **bloquea** si fallan |
| `proteger.py` | antes de Bash | **bloquea** comandos destructivos |
| `secretos.py` | antes de Edit/Write | **bloquea** si detecta credenciales |

Esto es lo que diferencia este espacio de un catálogo de prompts: no es el modelo
prometiendo que revisó, es un script que verifica y corta.

Se activan corriendo `activar-hooks.py`, que escribe `.claude/settings.json`
con el intérprete de Python que funciona en esa máquina. Ese archivo no se
versiona.

## Reglas de trabajo

Las de `METODOLOGIA.md`, en resumen:

- **Evidencia sobre afirmaciones** — nada se declara listo sin haberlo corrido.
- **TDD donde hay lógica real** — test primero, verlo fallar.
- **Un cambio por vez.**
- **Causa raíz, no síntoma.**
- **Decisiones difíciles de revertir → ADR.**
- **Para lo que el usuario ya sabe hacer: preguntá qué intentó** antes de
  resolverlo. Para terreno nuevo: mostrá el panorama con trade-offs.
- **Honestidad** — si no se pudo verificar, decirlo. Si una decisión no conviene
  a largo plazo, decirlo aunque no lo hayan preguntado.

## Sesgo explícito: lo simple primero

El error más caro en este espacio es sobredimensionar. Microservicios para 50
usuarios, Kubernetes para un proyecto de una persona, un store global para tres
componentes.

**Antes de proponer algo complejo, verificar que el problema lo justifique.**
Si la opción simple alcanza, decirlo aunque suene poco ambiciosa.

## Git

Esta carpeta es un repo propio: la caja de herramientas versionada. Cada
sistema es otro repo, con sus propias reglas en su `CLAUDE.md`.

**Este repo es público.** Decidido, no se vuelve a discutir. Todo lo que se
commitea acá lo puede leer cualquiera: nada de datos personales, rutas
privadas ni información de clientes.

- **El primer commit es solo el `.gitignore`.** Para que no exista la ventana
  en la que un archivo con credenciales se puede colar.
- **Antes de cada commit, mostrar qué entra y esperar aprobación.** No
  commitear sin que el usuario haya visto el diff.
- **Credenciales nunca en archivos versionados.** Van en `.env`, que está
  ignorado.
- **Si una credencial se filtró: rotarla.** Borrar el commit no arregla nada —
  el historial queda y hay bots escaneando GitHub. Decirlo directo, sin
  suavizarlo.

## Primera vez

Leer `SETUP.md` y ejecutarlo.

Tono: español neutro, técnico, directo. Sin relleno.
