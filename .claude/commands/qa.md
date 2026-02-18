# /qa — QA completo de cierre de sprint

Ejecuta el QA completo del proyecto o del sprint indicado: $ARGUMENTS

## Instrucciones

Correr en orden y reportar resultado de cada paso:

### 1. Linting
```bash
ruff check src/
ruff format --check src/
```
Reportar: número de errores, archivos afectados.

### 2. Type Checking
```bash
mypy src/auronai/
```
Reportar: número de errores por tipo (missing return, incompatible type, etc.)

### 3. Tests + Coverage
```bash
pytest tests/ --cov=auronai --cov-report=term-missing --cov-fail-under=80 -v
```
Reportar: passed/failed, coverage total y por módulo.

### 4. Security Check
- Buscar hardcoded secrets: API keys, passwords, tokens en el código
- Verificar que `.env` está en `.gitignore`
- Verificar que no hay `print()` sueltos (usar logging)

### 5. Trading-Specific Checks
- Buscar posibles look-ahead bias en estrategias
- Verificar position sizing no excede límites
- Verificar que todas las estrategias tienen stop loss

### 6. Reporte Final

```
## QA Report — Sprint X

### Linting: ✅/❌ (N errores)
### Type Check: ✅/❌ (N errores)
### Tests: ✅/❌ (N passed, M failed, coverage X%)
### Security: ✅/❌
### Trading Checks: ✅/❌

### Issues encontrados:
1. ...
2. ...

### Recomendaciones:
1. ...
```
