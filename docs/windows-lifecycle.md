# Windows lifecycle

## Installed components

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
