# /deploy — Build y deploy del proyecto

Ejecuta operaciones de build/deploy: $ARGUMENTS

## Instrucciones

### "docker" — Levantar infraestructura:
```bash
docker compose up -d
docker compose ps
docker compose logs --tail=20
```
Verificar que todos los servicios están healthy.

### "install" — Instalar dependencias:
```bash
pip install -e ".[dev]"
```

### "db" — Solo bases de datos:
```bash
docker compose up -d questdb postgres redis
```

### "stop" — Parar todo:
```bash
docker compose down
```

### "status" — Estado actual:
```bash
docker compose ps
```

### Sin argumento — Mostrar opciones disponibles:
Listar los comandos disponibles y el estado actual de la infraestructura.
