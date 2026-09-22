# Debug Commands

## Project Root

```powershell
cd c:\Users\Deepak\RA_project
```

## Start And Stop

```powershell
docker compose up -d
docker compose down
```

## Check Containers

```powershell
docker compose ps
```

## Logs

```powershell
docker compose logs db --tail 50
docker compose logs api --tail 50
docker compose logs -f api
```

## Open Database Shell

```powershell
docker compose exec db psql -U postgres -d ra_app
```

## Database Checks

```powershell
docker compose exec db psql -U postgres -d ra_app -c "\dn"
docker compose exec db psql -U postgres -d ra_app -c "\dt core.*"
docker compose exec db psql -U postgres -d ra_app -c "\dt static.*"
docker compose exec db psql -U postgres -d ra_app -c "\dt tracking.*"
docker compose exec db psql -U postgres -d ra_app -c "\dt intelligence.*"
```

## Alembic

```powershell
docker compose run --rm api alembic history
docker compose run --rm api alembic current
docker compose run --rm api alembic upgrade head
docker compose run --rm api alembic downgrade -1
```

## Run API

```powershell
docker compose up -d api
```

## Health Check

```powershell
curl http://localhost:8000/health
```

## If API Is Not Working

```powershell
docker compose logs api --tail 100
docker compose exec db psql -U postgres -d ra_app -c "SELECT version_num FROM core.alembic_version;"
```

## If DB Looks Wrong

```powershell
docker compose exec db psql -U postgres -d ra_app -c "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema IN ('core','static','tracking','intelligence') ORDER BY table_schema, table_name;"
```

## Rebuild API Image

```powershell
docker compose build api
docker compose up -d api
```

## Full Reset

Warning: this deletes Docker Postgres volume data.

```powershell
docker compose down -v
docker compose up -d
```

## Project Rule

- Use local PowerShell to launch commands.
- Use Docker `api` and `db` services for this project.
- Avoid host-side `.\venv\Scripts\alembic.exe ...` for normal project work.
- Avoid host-side `psql -h localhost ...` unless intentionally testing local Windows PostgreSQL.
