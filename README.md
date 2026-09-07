# LuxTime

## What is this?

LuxTime is LuxForge's single-user, local time and effort accounting tool.
You start, pause, resume, and stop work sessions against one or more
projects — including several at once — and LuxTime keeps two separate
numbers honest: **elapsed time** (wall-clock time you were actually
working, pauses excluded) and **project-attributed time** (the sum of time
attributed to each project, which can exceed elapsed time when projects
overlap). Pause/resume history is preserved as session segments rather than
rewriting timestamps, so the record of *how* a session was worked stays
intact, not just the total.

It ships as a small local web app (React frontend, FastAPI backend,
PostgreSQL storage) plus a Windows tray icon and background service that
keep it running. It is not an HR, payroll, or employee timesheet system,
and it has no multi-tenant or authentication model — every port it opens
binds only to `127.0.0.1`.

## Why does it exist?

Most time trackers assume one timer at a time, or push your data to a
cloud service you don't control. LuxTime exists for the opposite case:
someone working across several concurrent projects on one machine, who
wants an accurate record of both real elapsed time and per-project
attribution, kept entirely on that machine.

That local-first goal shapes the rest of the design: PostgreSQL is the only
persistence layer (no ORM, no SQLite fallback — see
[docs/architecture.md](docs/architecture.md)), the API is the single owner
of business truth so the web UI and tray are both thin clients of it, and
the Windows service/tray exist so LuxTime behaves like a normal installed
application — available after sign-in without a manual start step — rather
than something you remember to launch from a terminal.

## How do I install it?

**Recommended:** run the packaged `LuxTime-Setup.msi` (built from
[installer/](installer/)). It bundles its own Python runtime, so nothing
beyond Docker Desktop needs to be preinstalled. Running it installs, by
default, all three of:

- the `LuxTimeService` Windows service (delayed auto-start; keeps the local
  Docker application healthy),
- a Start Menu shortcut, and
- a tray icon that starts at sign-in,

and each can be unchecked during setup. Clicking the Start Menu shortcut
starts the service if it isn't already running and opens LuxTime in your
browser — no elevation prompt, even as a standard user.

Docker Desktop must be installed and configured to start at sign-in; the
installer detects and warns (but does not block) if it isn't found. See
[docs/windows-lifecycle.md](docs/windows-lifecycle.md#msi-installed-machines)
for exactly what gets installed, logs, and the uninstall/removal behavior.

**From a source checkout** (development, or building the installer itself),
install Docker Desktop, Python 3.11+, and PowerShell 7 first, then from an
elevated PowerShell 7 terminal:

```powershell
pwsh .\scripts\install.ps1
```

This installs the same `LuxTimeService`, starts the stack, and registers
the tray for the current user's Startup folder. See
[docs/windows-lifecycle.md](docs/windows-lifecycle.md) for component-specific
commands, startup/recovery behavior, logs, and the reboot/sign-in checklist.

Before either path, copy `.env.example` to `.env` and change
`POSTGRES_PASSWORD` before ongoing use — Compose's defaults are intentionally
local-only, and the example password is not appropriate outside a local
developer machine.

## How do I run it?

Once installed, LuxTime runs itself: the service keeps the application
healthy in the background, and the tray icon (or the Start Menu shortcut)
gets you to it. Open it directly at any time at
<http://127.0.0.1:52020> — the API shares this origin under `/api`, with
interactive API documentation at `/api/docs`.

From a source checkout, the equivalent manual commands are:

```powershell
pwsh .\scripts\start.ps1                 # build and start the production-shaped stack
pwsh .\scripts\stop.ps1 -Confirm:$false  # stop intentionally
pwsh .\scripts\restart.ps1 -Confirm:$false
pwsh .\scripts\status.ps1                # check service, Docker, API, and tray state
```

`stop.ps1` writes `.runtime/intentional-stop`, so an installed watchdog
won't immediately restart LuxTime; `start.ps1` clears that marker.

## Privacy & security

No data leaves your machine, no accounts, no telemetry. LuxTime has no
multi-tenant or authentication model because there's nothing to authenticate
against remotely — every port it opens (the web UI, the API, PostgreSQL in
dev mode) binds only to `127.0.0.1`. The only outbound network access
involved is Docker Compose pulling/building images and Docker Desktop's own
updates; the running application itself talks to nothing but its own local
PostgreSQL container.

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
- `launcher/` — the Start Menu shortcut's target: starts the service if
  needed and opens the browser.
- `installer/` — builds the packaged `LuxTime-Setup.msi`.
- `scripts/` — thin local operator commands.
- `tests/` — domain, API-surface, and PostgreSQL integration tests.

See [docs/architecture.md](docs/architecture.md) for the responsibility and
data-flow details.

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

## Removing LuxTime

If installed via `LuxTime-Setup.msi`, uninstall it from Settings > Apps (or
`msiexec /x`) — this stops and removes the service and both shortcuts, but
never touches `db\backups\` contents or the PostgreSQL Docker volume.

From a source checkout, from an elevated PowerShell terminal:

```powershell
pwsh .\scripts\uninstall.ps1 -Confirm:$false
```

This removes the service and the current user's tray registration and, by
default, intentionally stops the Compose stack. Persistent PostgreSQL data is
not deleted. Lock/unlock, sleep/resume, and idle detection remain intentionally
deferred.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for scope, dev setup, and PR
expectations.

## License

[MIT](LICENSE) &copy; LuxForge
