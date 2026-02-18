# /test — Correr tests del proyecto

Ejecuta los tests indicados: $ARGUMENTS

## Instrucciones

### Si se proporciona un módulo o archivo:
```bash
pytest tests/{argumento} -v --tb=short
```

### Si se proporciona "all" o no se proporciona argumento:
```bash
pytest tests/ --cov=auronai --cov-report=term-missing --cov-fail-under=80 -v
```

### Si se proporciona "quick":
```bash
pytest tests/ -x --tb=short -q
```

## Después de correr los tests, reportar:

1. **Resumen**: X passed, Y failed, Z errors
2. **Coverage**: porcentaje total y módulos < 80%
3. **Failures**: para cada test fallido:
   - Nombre del test
   - Error
   - Posible causa y fix sugerido
4. **Recomendaciones**: tests faltantes o mejoras
