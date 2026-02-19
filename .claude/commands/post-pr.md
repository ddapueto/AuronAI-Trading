# /post-pr — Evaluación Post-PR y Mejora Continua

Ejecuta un proceso de evaluación completo después de mergear un PR. Identifica gaps de calidad y genera issues de mejora.

## Workflow

### Paso 1: Ejecutar QA completo
```bash
make qa
```
Captura la salida de lint, typecheck y tests. Si falla, reportar los errores antes de continuar.

### Paso 2: Analizar coverage por módulo
```bash
pytest --cov=auronai --cov-report=json:coverage.json --no-header -q
```
Leer `coverage.json` y extraer el porcentaje de cada módulo en `src/auronai/`.

### Paso 3: Identificar gaps de coverage
Clasificar módulos en:
- **Críticos (0% coverage)**: No tienen ningún test
- **Bajo coverage (<50%)**: Necesitan más tests
- **Bajo objetivo (<80%)**: Necesitan tests adicionales
- **OK (>=80%)**: Cumplen el objetivo

### Paso 4: Revisar archivos del último PR
```bash
git log --oneline -1
git diff HEAD~1 --name-only
```
Identificar qué módulos fueron tocados y si tienen tests correspondientes.

### Paso 5: Evaluar agentes y skills
Revisar los archivos en `.claude/agents/` y `.claude/commands/`:
- ¿Hay skills que deberían actualizarse por los cambios del PR?
- ¿Hay agentes cuyas responsabilidades cambiaron?
- ¿Se necesitan nuevos skills para funcionalidad agregada?

### Paso 6: Generar lista de issues
Para cada problema encontrado, generar un issue con este template:

```markdown
**Título**: [tipo] Descripción breve
**Labels**: testing, improvement, coverage (según corresponda)
**Descripción**:
- **Problema**: Qué se detectó
- **Módulo**: Ruta del archivo/módulo afectado
- **Coverage actual**: X%
- **Objetivo**: 80%
- **Acción sugerida**: Qué tests agregar o qué mejorar
```

### Paso 7: Generar reporte final
Producir un reporte markdown con:

```markdown
## Reporte Post-PR

### Resumen QA
- Lint: ✅/❌
- Typecheck: ✅/❌
- Tests: ✅/❌ (X passed, Y failed)
- Coverage global: X%

### Coverage por módulo
| Módulo | Coverage | Estado |
|--------|----------|--------|
| core   | 85%      | ✅ OK  |
| risk   | 72%      | ⚠️ Bajo objetivo |
| data   | 0%       | ❌ Sin tests |

### Archivos del PR sin tests
- `src/auronai/xxx/yyy.py` — sin test correspondiente

### Issues sugeridos
1. [testing] Agregar tests para módulo X (coverage: 0% → 80%)
2. [improvement] Actualizar skill /qa con nuevo paso
3. ...

### Próximos pasos
- Prioridad alta: ...
- Prioridad media: ...
```

## Notas
- Este skill es manual (no se ejecuta automáticamente en CI)
- Requiere contexto humano para evaluar si los issues sugeridos son relevantes
- Los issues se presentan como sugerencias — el usuario decide cuáles crear en GitHub
