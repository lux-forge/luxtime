# Contributing to LuxTime

LuxTime is a LuxForge project. Contributions, bug reports, and feature
requests are welcome.

## Scope

LuxTime is intentionally single-user, local-first, and Windows-only for now
(the packaged installer, service, and tray are Windows-specific). The FastAPI
backend and React frontend themselves are platform-agnostic, and a
Linux/macOS equivalent of the service/tray layer is a reasonable community
contribution — but it's not something the maintainer is building. Multi-user
accounts, authentication, or a hosted/cloud mode are explicitly out of scope:
they conflict with the local-first design (see
[README.md](README.md#why-does-it-exist)).

## Getting set up

See [README.md](README.md#development) for environment setup and the local
dev workflow (Postgres via Docker Compose, FastAPI on 52023, the Vite dev
server on 52022).

Before opening a PR, run the same checks CI runs:

```powershell
pwsh .\scripts\build.ps1
```

This typechecks and lints the frontend, builds it, runs backend unit tests,
and builds the container images. Include integration tests
(`LUXTIME_RUN_INTEGRATION=1`, see the README) if your change touches
database access or API behavior.

## Making changes

- Keep the API as the single owner of business truth — the web UI and tray
  should stay thin clients of it (see [docs/architecture.md](docs/architecture.md)).
- `service/` (the Windows watchdog) should have no project/session logic;
  keep it about process lifecycle only.
- Match the existing local-first constraints: no new persistence layer
  beyond PostgreSQL, no port binding beyond `127.0.0.1`, no telemetry.
- Add or update tests under `tests/` for behavior changes.

## Reporting bugs / requesting features

Please use the issue templates. For bugs, include your OS build, whether you
installed via the MSI or a source checkout, and relevant log output (see
[docs/windows-lifecycle.md](docs/windows-lifecycle.md) for log locations).

## Pull requests

Keep PRs focused on one change. Describe *why* the change is needed, not
just what it does — the "why" is what's hard to recover later from a diff
alone.
