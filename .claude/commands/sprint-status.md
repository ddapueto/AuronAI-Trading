# /sprint-status — Ver estado del sprint actual

Muestra el estado del sprint actual o del indicado: $ARGUMENTS

## Instrucciones

1. Consultar milestones del repo `ddapueto/AuronAI-Trading` en GitHub
2. Si se indica un número de sprint, mostrar ese. Si no, mostrar el milestone abierto más próximo.
3. Listar todos los issues del milestone con su estado.

### Output:

```
## Sprint N: [Nombre] — Due: [fecha]
Progress: X/Y issues (Z%)

### Done ✓
- #N: título

### In Progress →
- #N: título (assignee)

### Pending ○
- #N: título

### Blockers
- #N bloqueado por #M (razón)
```

4. Dar recomendación de cuál issue abordar primero (basado en dependencias y prioridad).
