# Building LuxTime from source

This is for people who want to build LuxTime themselves rather than run the
prebuilt `LuxTime-Setup.msi`. If you just want to use the app, see the
[top-level README](../README.md#how-do-i-install-it) instead. If you want to
change LuxTime's code, see [CONTRIBUTING.md](../CONTRIBUTING.md).

## Prerequisites

- Docker Desktop
- Python 3.11+
- Node.js + pnpm (for `web/`)
- PowerShell 7
- To build the MSI specifically: the WiX v5 CLI - see
  [installer/README.md](../installer/README.md#build-prerequisites-build-machine-only---never-needed-by-end-users)

## Versioning

[`VERSION`](../VERSION) at the repository root is the single source of truth
for LuxTime's version number:

- `pyproject.toml` reads it dynamically (`[tool.setuptools.dynamic]`), so the
  installed Python package version always matches it.
- `installer\build.ps1` reads it directly for the MSI's `ProductVersion`.
- `web/package.json` and this repository's `README.md` ("Current release")
  are kept in sync with it by `release.ps1` (below) whenever it bumps the
  version - don't hand-edit the version in either place.

## Building and running the app

```powershell
pwsh .\scripts\build.ps1   # frontend typecheck/lint/build, backend unit tests, container build
pwsh .\scripts\run.ps1     # build (if needed) and start the full stack at http://127.0.0.1:52020
```

See the [top-level README](../README.md#development) for the native
(non-Docker) development workflow.

## Building the MSI

```powershell
pwsh .\build\release.ps1
```

This is the one command that ties branch, version, and the MSI together:

- **On `main`:** warns and stops. `main` is for releases via PR, not ongoing
  work - if you're here, you probably meant to be on `dev` or a feature
  branch.
- **On `dev`:** asks whether to bump `VERSION` (major/minor/patch) and open a
  PR to `main`. Say no to just build with the current version unchanged.
- **On anything else:** asks whether to push the current branch to `dev`.
  Say no to just build from the branch as-is.

Either way, it finishes by running [installer/build.ps1](../installer/build.ps1)
and leaves a fresh `dist\LuxTime-Setup.msi`. Pass `-QuickBuild` to skip
restaging the embeddable Python runtime when `service/requirements.txt` and
`tray/requirements.txt` haven't changed since your last build - it's the slow
step and is safe to skip most of the time.

For the low-level details of what the MSI build actually does (WiX
authoring, payload staging, the embeddable Python runtime), see
[installer/README.md](../installer/README.md).

## Deploying a new MSI release

`release.ps1`'s `dev` path (bump version, open a PR to `main`) is the release
process: once that PR merges, `dist\LuxTime-Setup.msi` from the matching
build is what gets attached to a new [GitHub release](https://github.com/lux-forge/luxtime/releases).
