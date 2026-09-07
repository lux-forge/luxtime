# LuxTime installer

Builds `dist\LuxTime-Setup.msi`: a WiX-based Windows installer that ships its
own embeddable Python, so end users only need Docker Desktop preinstalled.
See [docs/windows-lifecycle.md](../docs/windows-lifecycle.md#msi-installed-machines)
for what it installs and how.

## Build prerequisites (build machine only - never needed by end users)

- .NET SDK (for the WiX CLI)
- WiX v5 CLI and extensions:

  ```powershell
  dotnet tool install --global wix
  wix extension add -g WixToolset.Util.wixext/5.0.2
  wix extension add -g WixToolset.UI.wixext/5.0.2
  ```

## Build

```powershell
pwsh .\installer\build.ps1
```

This runs, in order:

1. [stage-payload.ps1](stage-payload.ps1) - copies the Docker build context
   (`app/`, `web/` source, `docker/`, `db/`) plus `service/`, `tray/`,
   `launcher/` into `installer\build\payload`, excluding dev tooling and
   anything Docker regenerates itself (`web/node_modules`, `web/dist`).
2. [build-python-runtime.ps1](build-python-runtime.ps1) - stages the
   official Windows embeddable Python into `installer\build\python-runtime`,
   enables `site` (required for pywin32's own `.pth`-based DLL-search-path
   fix to run), and `pip install`s `service/requirements.txt` +
   `tray/requirements.txt` into it. No network or pip access is needed at
   MSI install time - this is the only place dependencies are resolved.
3. `wix build` compiles [Product.wxs](Product.wxs) and
   [Components.wxs](Components.wxs) into the MSI.

Pass `-SkipPayload` / `-SkipPythonRuntime` to skip re-staging either input
when iterating on the WiX authoring alone.

## Files

- `Product.wxs` - package metadata, install directory tree
  (`%ProgramData%\LuxTime`), the three uncheckable features, Docker-Desktop
  detection, and the service install/remove custom actions.
- `Components.wxs` - component groups: the always-installed Core payload
  (Python runtime + app/web/docker/db source), the ACL'd `logs`/`.runtime`/
  `db\backups` folders, and the per-feature service/shortcut/tray payloads.
- `assets/` - the shortcut/ARP icon and the license-page RTF.
