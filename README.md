# LuxTime

LuxTime is LuxForge's single-user, local time and effort accounting tool. It
tracks one or more projects concurrently, preserves pause/resume history as
session segments, and calculates elapsed time separately from project-attributed
time. It is not an HR, payroll, or employee timesheet system.

## Architecture

- `app/` — FastAPI, domain services, Foundry-backed PostgreSQL access, and the
  production frontend host. The API owns business truth.
- `web/` — the existing React interface. It consumes the API and owns only UI,
  request, and temporary form state.
- `db/` — canonical SQL, legitimate defaults, verification, rebuild, backup,
  and restore tooling.
- `docker/` — the `luxtime-app` and `luxtime-postgres` runtime.
- `service/` — Windows lifecycle watchdog; it has no project/session logic.
- `tray/` — interactive Windows tray client using the same API as the web UI.
- `scripts/` — thin local operator commands.
- `tests/` — domain, API-surface, and PostgreSQL integration tests.

See [docs/architecture.md](docs/architecture.md) for the responsibility and
data-flow details.

## Prerequisites

- Windows 11 with PowerShell 7
- Docker Desktop with Compose
- Python 3.11 or newer
- Node.js 22 and pnpm for native frontend development

Copy `.env.example` to `.env` and change `POSTGRES_PASSWORD` before ongoing use.
Compose defaults are intentionally local-only, but the example password is not
appropriate outside a local developer machine.

## Install on Windows

Docker Desktop must be configured to start when the user signs in. From an
elevated PowerShell 7 terminal, install the delayed-auto-start lifecycle service,
start the stack, and register the tray for the current user's Startup folder:

```powershell
pwsh .\scripts\install.ps1
```

The Windows service name is `LuxTimeService`. The service runs the lifecycle
watchdog only; the interactive tray always runs in the signed-in user's session.
See [docs/windows-lifecycle.md](docs/windows-lifecycle.md) for component-specific
commands, startup/recovery behavior, logs, and the reboot/sign-in checklist.

## Start, stop, and status

Build and start the production-shaped local stack:

```powershell
pwsh .\scripts\start.ps1
```

LuxTime is then available at <http://127.0.0.1:52020>. The API shares this
origin under `/api`; interactive API documentation is at `/api/docs`.

Stop the complete stack intentionally:

```powershell
pwsh .\scripts\stop.ps1 -Confirm:$false
```

This writes `.runtime/intentional-stop`, so an installed watchdog will not
immediately restart LuxTime. `start.ps1` clears that marker. Restart and inspect
the complete lifecycle with:

```powershell
pwsh .\scripts\restart.ps1 -Confirm:$false
pwsh .\scripts\status.ps1
```

## Development

Create a Python environment and install the application plus test tools:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Start PostgreSQL, rebuild the schema, and run the API on development port 52023:

```powershell
docker compose -f .\docker\compose.yml -f .\docker\compose.dev.yml up -d postgres
pwsh .\db\rebuild\rebuild.ps1 -Confirm:$false
$env:LUXTIME_DB_PORT = '54329'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 52023 --reload
```

In a second terminal, start the frontend on port 52022:

```powershell
Set-Location .\web
pnpm install --frozen-lockfile
pnpm dev
```

Run the complete local build (frontend typecheck/lint/build, backend unit tests,
and container build):

```powershell
pwsh .\scripts\build.ps1
```

The development override is what exposes PostgreSQL on localhost port 54329;
the normal production-shaped stack has no database host binding. With that
override running, include integration tests with:

```powershell
$env:LUXTIME_RUN_INTEGRATION = '1'
$env:LUXTIME_DB_PORT = '54329'
.\.venv\Scripts\python.exe -m pytest
```

## Database operations

Rebuild the application schema from canonical SQL:

```powershell
pwsh .\db\rebuild\rebuild.ps1 -Confirm:$false
```

Create a timestamped native PostgreSQL backup:

```powershell
pwsh .\db\backup\backup.ps1
```

Restore a selected dump already under `db/backups/`:

```powershell
pwsh .\db\backup\restore.ps1 -BackupFile .\db\backups\luxtime-YYYYMMDDTHHMMSSZ.dump -Confirm:$false
```

See [db/README.md](db/README.md) before destructive database operations.

## Remove the Windows installation

From an elevated PowerShell terminal:

```powershell
pwsh .\scripts\uninstall.ps1 -Confirm:$false
```

This removes the service and the current user's tray registration and, by
default, intentionally stops the Compose stack. Persistent PostgreSQL data is
not deleted. Lock/unlock, sleep/resume, and idle detection remain intentionally
deferred.
