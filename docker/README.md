# LuxTime Docker runtime

`docker/compose.yml` defines two containers:

- `luxtime-app` — FastAPI, business logic, Foundry infrastructure, and compiled web UI
- `luxtime-postgres` — PostgreSQL 17 and the durable application volume

Both join the private `luxtime-internal` network. The app reaches PostgreSQL by
the Compose service name `postgres`; credentials come from `.env` or local
defaults. The database schema is mounted read-only at `/db`, while `/backups`
maps to the gitignored host backup directory.

## Ports

- `127.0.0.1:52020` — production-shaped application and frontend
- `127.0.0.1:52022` — native Vite development server
- `127.0.0.1:52023` — native FastAPI development server
- `127.0.0.1:54329` — opt-in localhost-only PostgreSQL development access

No LuxTime user-facing service binds to the LAN. Ports 52024–52029 remain
reserved.

## Operation

```powershell
pwsh .\scripts\run.ps1
docker compose -f .\docker\compose.yml ps
pwsh .\scripts\stop.ps1 -Confirm:$false
```

Both containers have health checks. PostgreSQL must become healthy before the
application starts. Container names and the named network/volume all use the
`luxtime-` prefix.

The base file intentionally does not publish PostgreSQL. Native development and
integration tests that need a direct connection must add the override:

```powershell
docker compose `
  -f .\docker\compose.yml `
  -f .\docker\compose.dev.yml `
  up -d postgres
```

The override binds only `127.0.0.1:${LUXTIME_POSTGRES_PORT:-54329}`. Database
rebuild, verify, backup, and restore scripts use `docker exec` and therefore do
not require the host port.
