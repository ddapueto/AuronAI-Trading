# /lint — Correr linting y type checking

Ejecuta linting y opcionalmente corrige: $ARGUMENTS

## Instrucciones

### Default (sin argumentos) — solo check:
```bash
ruff check src/
mypy src/auronai/
```

### Con argumento "fix" — corregir automáticamente:
```bash
ruff check src/ --fix
ruff format src/
```
Luego reportar qué se corrigió.

### Con argumento de archivo específico:
```bash
ruff check {archivo}
mypy {archivo}
```

## Output:
```
## Lint Report

### Ruff: X errores (Y auto-fixable)
- E501: line too long (N ocurrencias)
- F841: unused variable (N ocurrencias)
- ...

### Mypy: X errores
- Missing return type (N)
- Incompatible types (N)
- ...

### Archivos más afectados:
1. archivo.py (N errores)
2. ...
```
