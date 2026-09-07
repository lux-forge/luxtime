# Windows lifecycle

## MSI-installed machines

`LuxTime-Setup.msi` (built from [installer/](../installer/), see
[installer/build.ps1](../installer/build.ps1)) is the recommended install
path for a machine that isn't a source checkout. It installs everything
under `%ProgramData%\LuxTime`, including a bundled, self-contained Python -
nothing beyond Docker Desktop needs to be preinstalled.

Running the installer offers three independently-uncheckable features, all
on by default:

- **LuxTime Service** - registers and starts `LuxTimeService` exactly as
  `service\windows_service.py`'s `ensure-installed` verb would from a source
  checkout (same delayed-auto-start and failure-recovery configuration).
  Unchecking it means the Windows service is never created.
- **Start Menu Shortcut** - installs a `LuxTime` shortcut that runs
  `launcher\main.py`: it starts `LuxTimeService` if it isn't already
  running, waits for `/api/health`, then opens `http://127.0.0.1:52020` in
  the default browser. The service's ACL is extended at install time to let
  any signed-in user start it, so clicking this shortcut never prompts for
  elevation.
- **Tray icon at sign-in** - registers the same per-user Startup-folder
  shortcut as `tray\install-startup.ps1` does for a source checkout, for the
  user who ran the installer.

Uninstalling (`msiexec /x` or via Settings > Apps) stops and removes the
service and both shortcuts, but never touches `db\backups\` contents or the
`luxtime-postgres-data` Docker volume - matches
`scripts\uninstall.ps1 -KeepRuntime` semantics on a source checkout.

Docker Desktop is not bundled or required at install time: the installer
only warns (via the finish-page text) if it isn't found at its default
location, since `service\watchdog.py` already tolerates Docker being
unavailable at service start with bounded retries. The first `docker compose
up` still **builds** the application image from the installed payload (the
same `app/`, `web/`, `docker/` source a checkout would have), so first start
after install needs internet access and can take several minutes.

## Installed components (source checkout)

- `LuxTimeService` is a native Windows service configured as **Automatic
  (Delayed Start)**. It runs the lifecycle watchdog in session 0 and never owns
  timer or session data.
- `LuxTime Tray.lnk` is installed in the current user's Startup folder. It
  launches the tray in that user's interactive session.
- Docker Desktop supplies the Docker Engine and must be enabled to start at
  sign-in. The watchdog tolerates delayed engine availability with bounded
  retries; it does not modify Docker Desktop's private settings.

The expected startup sequence is: Windows starts the delayed service, Docker
Desktop makes its engine available, the watchdog runs Compose, PostgreSQL and
the application become healthy, and the user's Startup shortcut launches the
tray. The tray reconnects to API-owned state at `http://127.0.0.1:52020`.

## Installation and removal

Run the coordinated installer from an elevated PowerShell 7 terminal:

```powershell
Set-Location L:\LuxTime
pwsh .\scripts\install.ps1
```

The operation is repeatable: the existing service is updated instead of a
duplicate being created, and the same per-user shortcut is replaced. To manage
the components separately:

```powershell
pwsh .\service\install-service.ps1
pwsh .\service\status-service.ps1
pwsh .\service\uninstall-service.ps1
pwsh .\tray\install-startup.ps1
pwsh .\tray\status.ps1
pwsh .\tray\uninstall-startup.ps1 -StopTray
```

Remove the complete installation without deleting the PostgreSQL volume:

```powershell
pwsh .\scripts\uninstall.ps1 -Confirm:$false
```

## Operator commands

```powershell
pwsh .\scripts\start.ps1            # clear intentional stop and ensure healthy
pwsh .\scripts\stop.ps1 -Confirm:$false # set intentional stop, then stop stack
pwsh .\scripts\restart.ps1 -Confirm:$false
pwsh .\scripts\status.ps1
pwsh .\scripts\status.ps1 -Strict   # nonzero/terminating result if any check fails

pwsh .\service\start-service.ps1    # elevated; watchdog only
pwsh .\service\stop-service.ps1     # elevated; backend is left alone
pwsh .\tray\start.ps1
pwsh .\tray\stop.ps1                # exit tray only; backend is left alone
```

`Exit Tray` and `tray/stop.ps1` close only the tray process. `Stop LuxTime` and
`scripts/stop.ps1` first create `.runtime/intentional-stop`, then stop Compose.
The watchdog observes that marker and suppresses recovery. A supported start
removes the marker before starting Compose. An unexpected missing/unhealthy
container has no marker, so the watchdog restores the stack.

## Logs and troubleshooting

- lifecycle/watchdog: `L:\LuxTime\logs\service\`
- tray startup and connectivity: `L:\LuxTime\logs\tray\`
- application/API: `L:\LuxTime\logs\app\`
- Windows service control failures: Windows Event Viewer, **Windows Logs →
  Application**, source `LuxTimeService`

Run `pwsh .\scripts\status.ps1` first. If Docker is unavailable, open Docker
Desktop and confirm **Start Docker Desktop when you sign in** is enabled. If the
service is absent or stopped, use the service status/install/start commands from
an elevated terminal. If the tray is absent, inspect the Startup shortcut with
`tray/status.ps1` and relaunch it with `tray/start.ps1`. Normal healthy polling
does not emit repeated logs; state transitions and retry intervals do.

The service install records the Docker executable and named-pipe endpoint in
`.runtime/service-config.json`. If Docker Desktop is moved or its engine changes,
rerun `service/install-service.ps1` to refresh it.

## Reboot and sign-in verification

An actual reboot must be checked on the target Windows account; do not infer it
from an in-session restart. Before reboot, ensure Docker Desktop is enabled at
sign-in and run `scripts/status.ps1 -Strict`. Then reboot and sign in normally,
without manually launching LuxTime. After Docker Desktop has settled, run:

```powershell
Set-Location L:\LuxTime
pwsh .\scripts\status.ps1 -Strict
```

Confirm all of the following:

1. `LuxTime Service` is `Running` with `Automatic (Delayed Start)`.
2. Docker is available; `luxtime-postgres` and `luxtime-app` are healthy.
3. API and frontend checks succeed on port 52020.
4. the tray icon appeared automatically and shows the current API state.
5. no manual LuxTime start command was used.

For sign-out/sign-in, start or leave a session in a known state, sign out, sign
back in, and run the same status command. The backend is service-managed and
must remain healthy; the newly launched tray must display the state refetched
from the API. A tray process ending at sign-out is not a backend failure.

Lock/unlock, sleep/resume, and idle event detection are explicitly deferred.
No polling or simulated Windows-event automation is implemented here.
