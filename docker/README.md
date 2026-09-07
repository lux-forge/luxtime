# LuxTime Docker runtime

`docker/compose.yml` defines two containers:

- `luxtime-app` — FastAPI, business logic, Foundry infrastructure, and compiled web UI
- `luxtime-postgres` — PostgreSQL 17 and the durable application volume

Both join the private `luxtime-internal` network. The app reaches PostgreSQL by
the Compose service name `postgres`; credentials are fixed in
`docker/compose.yml` — there is no host-side configuration to set. The
database schema is mounted read-only at `/db`, while `/backups` maps to the
gitignored host backup directory.

## Ports

- `127.0.0.1:52020` — production-shaped application and frontend
- `127.0.0.1:52022` — native Vite development server
- `127.0.0.1:52023` — native FastAPI development server
- `127.0.0.1:54329` — localhost-only PostgreSQL access (native dev server and
  integration tests connect here; `db/` scripts use `docker exec` instead)

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

PostgreSQL publishes `127.0.0.1:54329` unconditionally — there's no separate
dev/prod mode, so native development and integration tests can always connect
there directly. Database rebuild, verify, backup, and restore scripts use
`docker exec` instead and don't depend on the host port at all.
