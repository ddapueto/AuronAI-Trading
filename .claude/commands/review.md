# /review — Code review de cambios actuales

Revisa los cambios actuales pendientes de commit o un PR: $ARGUMENTS

## Instrucciones

### Si no se proporciona argumento (cambios locales):
1. Correr `git diff` y `git diff --staged` para ver cambios
2. Revisar cada archivo modificado

### Si se proporciona un número de PR:
1. Leer el PR del repo `ddapueto/AuronAI-Trading`
2. Revisar los archivos cambiados

### Checklist de revisión:

#### Correctitud Trading
- [ ] Sin look-ahead bias
- [ ] Cálculos de indicadores correctos
- [ ] Position sizing respeta límites (1-2% risk)
- [ ] Stop loss presente en toda estrategia
- [ ] Manejo de edge cases (gaps, splits, NaN)

#### Calidad de Código
- [ ] Type hints presentes
- [ ] Docstrings en funciones públicas
- [ ] Error handling apropiado
- [ ] Logging (no print)
- [ ] Tests para código nuevo

#### Seguridad
- [ ] Sin hardcoded secrets
- [ ] Inputs validados
- [ ] Rate limiting en APIs externas

#### Performance
- [ ] Sin operaciones O(n²) innecesarias
- [ ] Cache usado donde corresponde
- [ ] Async para I/O

### Output:
Para cada archivo, dar feedback estructurado:
```
### archivo.py
✅ [lo que está bien]
⚠️ [advertencias]
❌ [problemas que deben arreglarse]
💡 [sugerencias opcionales]
```

### Veredicto final: APPROVE / REQUEST CHANGES / COMMENT
