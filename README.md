# Claude Code Toolkit

Caja de herramientas para construir software. 15 agentes, una metodología y
tres hooks de verificación automática.

> Proyecto personal, no oficial. No está afiliado a Anthropic ni avalado por
> Anthropic; "Claude" y "Claude Code" son marcas de Anthropic.

**No es un repo de trabajo.** Cada sistema va en su propio repositorio;
`nuevo.py` lo crea copiándole los agentes y los hooks.

## Instalación

1. Abrir esta carpeta en VS Code.
2. Abrir Claude Code **desde esta carpeta**.
3. `Leé SETUP.md y ejecutalo`
4. Preguntarle a Claude "¿Qué subagentes tenés disponibles?" y verificar que
   aparezcan los 15.

## Lo que hace distinto a este espacio

La mayoría de las colecciones de agentes son **prompts**: un "backend-developer"
que escribe código y dice que está bien.

Acá hay tres capas:

**1. Agentes** — uno por dominio real, con criterios concretos y sesgo explícito
hacia la solución simple.

**2. Metodología** (`METODOLOGIA.md`) — reglas de proceso que aplican a todos.
La central: *evidencia sobre afirmaciones*. Nada se declara terminado sin haberlo
corrido.

**3. Hooks** — verificación determinista que no depende del modelo:

| Hook | Cuándo | Qué hace |
|---|---|---|
| `verificar.py` | después de editar | lint + typecheck, **bloquea** si fallan |
| `proteger.py` | antes de un Bash | **bloquea** `rm -rf`, `DROP TABLE`, `--force`, `curl \| sh` |
| `secretos.py` | antes de escribir | **bloquea** si detecta API keys, tokens, claves privadas |

Un hook que sale con código 2 **corta la acción** y le devuelve el error a Claude
para que lo corrija. No es una promesa: es un script.

**Límite conocido de `secretos.py`:** solo revisa Edit y Write. Un archivo
escrito desde Bash o PowerShell (heredoc, `echo >`, `python -c`,
`Set-Content`) **no pasa por el hook**. No tiene solución completa con hooks:
habría que interpretar cada comando de shell para saber si escribe un archivo
y qué escribe. Es un límite del enfoque, no un bug. La red de fondo es el
`.gitignore` (`.env`) y revisar el diff antes de cada commit.

## Los 15 agentes

Pensados como un equipo de desarrollo completo, no como una lista de roles.

| Etapa | Agentes |
|---|---|
| Antes de codear | `descubrimiento`, `requisitos`, `ux-ui`, `arquitecto` |
| Construcción | `backend`, `frontend`, `mobile`, `base-datos`, `datos-analitica` |
| Verificación | `qa`, `revisor`, `seguridad` |
| Operación | `infraestructura`, `documentacion` |
| Coordinación | `gestion-entrega` |

Cuatro separaciones que son a propósito:

**`descubrimiento` aparte de `requisitos`** — uno decide *si* se construye
(construir, comprar algo existente o no hacer nada); el otro define *qué*.
Si es el mismo, la pregunta "¿conviene comprarlo?" nunca se hace: quien
especifica ya asumió que se construye. Va primero.

**`revisor` aparte de `qa`** — revisar con ojos frescos solo funciona si no
escribiste vos el código.

**`ux-ui` aparte de `frontend`** — uno decide cómo se usa, el otro lo
construye. Si es el mismo, el diseño sale de lo que es fácil de programar en
vez de lo que la persona necesita. Y va **antes** de `arquitecto`.

**`datos-analitica` aparte de `base-datos`** — transaccional (escribir rápido,
un registro por vez) contra analítico (leer mucho, agregar, histórico). El
mismo esquema no sirve bien para las dos cosas; mezclarlos es lo que hace que
un dashboard tire abajo la base de producción.

## Estructura

```
claude-code-toolkit/
├── CLAUDE.md             contexto y enrutado
├── METODOLOGIA.md        reglas de proceso
├── SETUP.md              instalación
├── .claude/
│   ├── agents/           los 15
│   ├── hooks/            verificación automática
│   └── settings.json.example   base; activar-hooks.py genera settings.json
├── datos/
│   ├── stack.csv         plantilla de decisiones técnicas (todo en TBD)
│   ├── convenciones.md   estilo del proyecto
│   └── adr/              decisiones de arquitectura
├── tests/                red de proteger.py (python3 tests/test_proteger.py) y prueba de enrutado
├── activar-hooks.py      activa los hooks con el Python de esta máquina
├── nuevo.py              crea el repo de un sistema, con todo copiado
├── COMO-CREAR-SISTEMA.md los 6 pasos
├── INDICE-SISTEMAS.example.md  plantilla del índice
└── INDICE-SISTEMAS.md    qué sistemas hay y dónde está cada repo (local, no versionado)
```

## Cómo se arranca un sistema

0. `descubrimiento` — si conviene construir, comprar algo existente o no hacer nada
1. `requisitos` — qué tiene que hacer, criterios de aceptación, alcance
2. `ux-ui` — cómo se usa; qué pantallas y los 5 estados de cada una
3. `arquitecto` — stack y estructura, con ADR de lo difícil de revertir
4. Completar `datos/stack.csv` y `datos/convenciones.md`
5. Recién ahí, construir

`gestion-entrega` entra en el 1-2 para partir el trabajo y poner rangos de
estimación. Pedirle un número único es pedirle que invente precisión.

Mientras `stack.csv` diga TBD, los agentes preguntan en vez de asumir. Es
intencional.

## Ajustar los hooks

Si un hook molesta, editá su script. Si bloquea algo legítimo, agregá la
excepción — no lo desactives entero.

`verificar.py` detecta el tipo de proyecto solo (package.json, pyproject.toml,
go.mod, Cargo.toml). Si usás otro stack, agregalo en `comandos_para()`.

## Mantener

Cuando se decida algo que estaba en TBD, actualizá `stack.csv` o
`convenciones.md`. Un agente con datos viejos da consejos viejos.

## Licencia

MIT © 2026 Alexis Bautista (AleBauty). Ver [LICENSE](LICENSE).
