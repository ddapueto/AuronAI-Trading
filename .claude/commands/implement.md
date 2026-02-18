# /implement — Implementar un issue del proyecto

Implementa el issue de GitHub indicado: $ARGUMENTS

## Instrucciones

1. **Leer el issue** en `ddapueto/AuronAI-Trading` (usar el número proporcionado)
2. **Entender el contexto**: leer archivos relacionados mencionados en el issue
3. **Crear branch**: `feature/{numero}-{descripcion-corta}`
4. **Implementar** siguiendo los acceptance criteria del issue
5. **Escribir tests** unitarios para cada componente nuevo
6. **Correr QA**: ruff check + mypy + pytest
7. **Commit** con mensaje descriptivo referenciando el issue
8. **Reportar** qué se hizo y qué queda pendiente

## Reglas
- Leer código existente ANTES de escribir código nuevo
- Seguir patrones y convenciones del proyecto (ver CLAUDE.md)
- Un commit por unidad lógica de trabajo
- No over-engineer — implementar lo mínimo que cumpla los acceptance criteria
- Si el issue es muy grande, proponer dividirlo en sub-tareas
- Comunicar en español
