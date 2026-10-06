# De dónde salió esto

## Criterio de selección

El pedido fue explícito: **lo funcional antes que lo popular.**

Revisadas las colecciones principales de agentes y skills de Claude Code. El
hallazgo: la enorme mayoría son **archivos de instrucciones**, no herramientas
de verificación. Un agente que escribe código y afirma que está bien no es
mejor que preguntarle a Claude directamente.

Lo que sí aporta valor real es lo que **verifica de forma determinista**.

## Lo que se tomó

**`obra/superpowers`** — metodología de desarrollo para agentes, no catálogo.
Principios adoptados en `METODOLOGIA.md`:
- "Evidence over claims — verify before declaring success"
- Ciclo TDD RED-GREEN-REFACTOR obligatorio, no sugerido
- Validación del baseline de tests antes de empezar
- Revisión de código que bloquea por severidad
- Depuración sistemática con análisis de causa raíz

**Hooks de Claude Code** — el mecanismo determinista del propio Claude Code.
Eventos `PreToolUse` y `PostToolUse` con matchers por herramienta; un hook que
sale con **código 2 bloquea la acción** y devuelve el error al modelo.
Los tres scripts de `.claude/hooks/` son propios, escritos para este espacio
y probados.

## Lo que se revisó y no se copió

- **VoltAgent/awesome-claude-code-subagents** — 154 agentes en 10 categorías.
  Cobertura amplia, pero descripciones superpuestas: instalar la colección
  entera ensucia el enrutado. Sirve como referencia de qué dominios cubrir.
- **ComposioHQ/awesome-claude-skills**, **alirezarezvani/claude-skills**,
  **VoltAgent/awesome-agent-skills** — catálogos grandes de skills. Útiles para
  buscar algo puntual, no para instalar en bloque.
- **anthropics/skills** — las oficiales. Ya vienen disponibles en el entorno.

## Advertencia sobre instalar colecciones enteras

Claude enruta según las descripciones de los agentes. Con 150 descripciones
parecidas, el enrutado se degrada: vas a terminar con un `backend-developer`
genérico respondiendo lo que debía contestar el agente específico.

Si algo de una colección sirve, **copiá ese archivo suelto**, no la colección.

## Seguridad al instalar de terceros

Las skills y agentes son instrucciones en texto plano, no código aislado. Antes
de instalar algo de un repositorio desconocido, leer el archivo: puede contener
instrucciones de acceso al sistema de archivos o ejecución de comandos.

---

## Agentes que cubren el equipo completo (agregados después)

Se agregaron tres agentes para cerrar huecos de un equipo de desarrollo real.
Ninguno viene de una colección externa: son diseño propio para este contexto.

| Agente | Hueco que cerraba |
|---|---|
| `ux-ui` | Producto y diseño existían implícitos dentro de `frontend`. El resultado de eso es que el diseño sale de lo que es fácil de programar |
| `datos-analitica` | `base-datos` modela para transacciones. Modelar para preguntas es otro problema con otras respuestas |
| `gestion-entrega` | Partir el trabajo, estimar y controlar alcance no era de nadie. Es donde se pierde más tiempo en proyectos de una persona |

**La razón de parar en 14.** Cada agente nuevo suma una descripción que compite
con las demás en el enrutado. 14 ya es bastante: si uno de estos nunca se usa,
conviene borrarlo en vez de dejarlo. La métrica no es cuántos hay, es si cada
uno se activa cuando corresponde.
