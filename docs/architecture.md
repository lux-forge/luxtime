# LuxTime architecture

## Invariants

**API owns business truth. Web and tray consume the API. Service owns lifecycle
only. Database schema is owned by `/db`.**

LuxTime is a single-user local application. There is no authentication or
multi-tenant boundary in this foundation, so every user-facing port binds to
`127.0.0.1`.

## Components

### Application and API

`app/` is the canonical application. FastAPI exposes project, session,
settings, status, and insight operations. Domain services validate state
transitions and use request-scoped database connections. The compiled React
frontend is served by this process in normal operation.

The application uses Foundry 0.2.0 for:

- `foundry.logger` structured, redacting console/file logging;
- `foundry.postgres.PostgresManager` connectivity, transactions, strict SQL
  execution, and dictionary query results.

LuxTime owns all project/session/insight rules. SQL execution during operator
rebuilds and PostgreSQL dump/restore remain native PostgreSQL operations because
the durable SQL under `/db` is the authoritative input.

### Sessions and concurrency

A work session owns one or more active-time segments. Pause closes the open
segment; resume opens another. Stopping closes any open segment and marks the
session stopped. The total duration is the sum of segments, so pauses never
rewrite historical timestamps.

Several sessions may be running at once. Only overlapping segments within the
same session are forbidden. Insight calculations merge all segment intervals
to derive real elapsed time and separately sum every project interval for
attributed time. Concurrent attribution is `attributed - elapsed`.

### PostgreSQL and `/db`

PostgreSQL is the only persistence layer. Explicit SQL files create schema,
tables, constraints, indexes, triggers, and views. A rebuild drops only the
`luxtime` application schema, applies files in lexical order, seeds the singleton
settings row, and verifies invariants. No ORM schema or SQLite fallback exists.

### Web

The React application preserves the existing LuxTime design. A central API
client performs all HTTP calls. React state contains fetched query results,
loading/error state, navigation, and temporary form input—not canonical timers.

### Tray

The interactive tray polls `/api/status`, `/api/projects`, and `/api/active`.
Start, pause, resume, and stop actions call the same API routes as the web UI.
`Exit Tray` closes only the tray process. `Stop LuxTime` is a separately named,
confirmed lifecycle operation.

The tray is a per-user singleton. A Startup-folder shortcut launches
`pythonw.exe -m tray.main` in the interactive sign-in session. A named Windows
event supports a clean `Exit Tray` request without coupling tray lifetime to the
backend. It stores no session state; reconnecting simply refetches API state.

### Windows service

The service checks Docker and `/api/health`, starts the Compose stack when
needed, and uses bounded exponential backoff. It never reads or writes project
or session data. `.runtime/intentional-stop` suppresses recovery after an
explicit full stop; `scripts/start.ps1` clears it.

`LuxTimeService` is a delayed-auto-start native Windows service. Its install
step records the absolute Docker CLI path and the active named-pipe engine
endpoint in `.runtime/service-config.json`, because a LocalSystem service cannot
depend on an interactive user's `PATH` or Docker CLI context. The file contains
no credentials. Docker availability, container health, and API health are
separate lifecycle signals and only their state transitions are logged.

### Docker

`luxtime-postgres` stores data in a named volume. `luxtime-app` connects over an
internal Compose network and serves API plus frontend at `127.0.0.1:52020`.
PostgreSQL is also published at `127.0.0.1:54329` unconditionally — there is
no separate dev/prod Compose mode.

## Native lock/sleep/idle events

`tray/system_events.py` detects Windows session lock/unlock
(`WM_WTSSESSION_CHANGE`), system suspend/resume (`WM_POWERBROADCAST`), and
idle input (polled `GetLastInputInfo`) from a hidden message-only window and
a polling thread, both running on their own background threads inside the
tray process. Detection only runs in the tray - not the service - because
both mechanisms require the interactive user session, which a Windows
service (session 0) does not have.

`TrayApplication` (`tray/main.py`) owns the policy: it checks the singleton
`settings` row's `stop_on_lock` / `stop_on_sleep` / `idle_detection` before
acting, calls `POST /api/active/stop-all` with the matching `stop_reason`
(`lock` / `sleep` / `idle`) for whatever was running or paused, and remembers
which projects it stopped. When the session unlocks, the system resumes, or
input resumes after an idle stop, it checks `resume_prompt` and - if set -
shows a native Yes/No prompt offering to start fresh sessions for those same
projects (a stopped session is terminal; "resuming" here means starting a new
one, not reopening the old one).
