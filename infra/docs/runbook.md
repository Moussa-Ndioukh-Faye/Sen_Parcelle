# Runbook — Sen_Parcelle Production

## Services

| Container      | Port(s)        | Description                        |
|----------------|----------------|------------------------------------|
| `sen_db`       | 5432 (int.)    | PostgreSQL + PostGIS 16            |
| `sen_redis`    | 6379 (int.)    | Redis 7 (broker + cache)           |
| `sen_backend`  | 8000 (int.)    | Django / Gunicorn API              |
| `sen_celery`   | —              | Celery worker (async tasks)        |
| `sen_beat`     | —              | Celery Beat (scheduled tasks)      |
| `sen_nginx`    | 80, 443        | Reverse proxy (TLS, rate limiting) |

## Common Commands

```bash
# View all logs
docker compose -f infra/docker/docker-compose.yml logs -f

# Logs for a specific service
docker compose -f infra/docker/docker-compose.yml logs -f backend

# Restart a service
docker compose -f infra/docker/docker-compose.yml restart backend

# Shell into a container
docker compose -f infra/docker/docker-compose.yml exec backend bash

# Django management commands
docker compose -f infra/docker/docker-compose.yml exec backend python manage.py <command>

# Celery task monitoring
docker compose -f infra/docker/docker-compose.yml exec celery_worker celery -A config.celery.app inspect active
docker compose -f infra/docker/docker-compose.yml exec celery_worker celery -A config.celery.app inspect stats
```

## Health Checks

Each service has a Docker health check. Verify all are healthy:

```bash
docker compose -f infra/docker/docker-compose.yml ps
```

Expected output shows `healthy` for all services.

## Backup & Restore

### Backup (automatic)
```bash
# Linux
./infra/scripts/backup.sh

# Windows
infra\scripts\backup.bat
```

Backups are stored in `./backups/` with filenames like `sen_parcelle_<db>_<datetime>.sql`.

### Restore from backup
```bash
# List available backups
ls -la ./backups/

# Restore the latest backup
pg_restore \
  -h localhost \
  -p 5432 \
  -U sen_parcelle \
  -d sen_parcelle \
  -c \
  ./backups/sen_parcelle_sen_parcelle_20260519_120000.sql
```

## Monitoring

### Manual health check
```bash
curl -s https://your-server/api/health/ | jq .
```

### Sentry
Open your Sentry project dashboard for error monitoring.

### Resource usage
```bash
docker stats sen_backend sen_db sen_redis sen_nginx sen_celery sen_beat
```

## Log Management

Logs are written to Docker's logging driver. For persistent logging:

```bash
# Tail logs to a file
docker compose -f infra/docker/docker-compose.yml logs -f --tail=1000 > /var/log/sen-parcelle/combined.log
```

## Incident Response

### API not responding

```bash
# 1. Check Nginx logs
docker compose logs nginx

# 2. Check backend health
docker compose exec backend curl -sf http://localhost:8000/api/health/

# 3. Check backend logs
docker compose logs --tail=50 backend

# 4. Check database connectivity
docker compose exec db pg_isready -U sen_parcelle

# 5. Restart if needed
docker compose restart backend
```

### Database full / slow

```bash
# 1. Check disk usage
docker system df

# 2. Check DB connections
docker compose exec db psql -U sen_parcelle -c "SELECT count(*) FROM pg_stat_activity;"

# 3. Run VACUUM (safe in production)
docker compose exec db psql -U sen_parcelle -c "VACUUM ANALYZE;"

# 4. Ensure backups are pruning old files
# Check: infra/scripts/backup.sh retention is 30 days
```

### Celery tasks stuck

```bash
# 1. Revoke all active tasks
docker compose exec celery_worker celery -A config.celery.app purge -f

# 2. Restart worker
docker compose restart celery_worker

# 3. Check task queue length
docker compose exec redis redis-cli --pass $REDIS_PASSWORD LLEN celery
```

### SSL cert expired

```bash
# 1. Check expiry
openssl x509 -in infra/nginx/ssl/sen-parcelle-dev.crt -noout -dates

# 2. Regenerate (dev certs)
./infra/scripts/gen-ssl-dev.sh

# 3. Reload Nginx
docker compose exec nginx nginx -s reload
```

### Full stack restart (scheduled maintenance)

```bash
# 1. Notify users (maintenance window: 5 min)
# 2. Take backup
./infra/scripts/backup.sh

# 3. Graceful teardown
docker compose -f infra/docker/docker-compose.yml down --timeout 30

# 4. Restart
docker compose -f infra/docker/docker-compose.yml up -d

# 5. Verify all healthy
docker compose -f infra/docker/docker-compose.yml ps
```

## Performance Tweaks

| Parameter                  | Default | When to increase               |
|----------------------------|---------|---------------------------------|
| `GUNICORN_WORKERS`         | 4       | > 4 CPU cores: `workers = 2*CPU` |
| `GUNICORN_THREADS`         | 2       | I/O-heavy loads: up to 4-8      |
| `CELERY_CONCURRENCY`       | 4       | Many tasks: up to 8             |
| `CONN_MAX_AGE` (DB)        | 60s     | High traffic: up to 300         |
| `nginx worker_connections` | 4096    | Many concurrent clients         |
| DB memory limit            | 1G      | Large datasets: up to 4G        |

## Useful Links

- Swagger API docs: `https://your-server/api/docs/`
- ReDoc: `https://your-server/api/redoc/`
- Django Admin: `https://your-server/admin/`
- Health check: `https://your-server/api/health/`
