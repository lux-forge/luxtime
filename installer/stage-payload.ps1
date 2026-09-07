[CmdletBinding()]
param(
    [string]$StagingDir = (Join-Path $PSScriptRoot 'build\payload')
)

<#
Copies the subset of the repository that the installed product actually
needs at runtime - the Docker build context (app/, web/ source, docker/,
db/) plus the host-side Python packages (service/, tray/, launcher/) and
top-level metadata Docker's build reads (pyproject.toml, README.md).

Deliberately excluded: dev tooling (.venv*, node_modules, .git, tests,
.pytest_cache, egg-info), anything already-built that Docker regenerates
itself (web/dist), and runtime state that must never ship with the
installer (logs/, .runtime/, db/backups - the latter may hold a real
developer's local dump files, never packaging artifacts).
#>

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path

if (Test-Path -LiteralPath $StagingDir) {
    Remove-Item -LiteralPath $StagingDir -Recurse -Force
}
New-Item -ItemType Directory -Path $StagingDir -Force | Out-Null

# Bare names so robocopy's /XD matches them at any depth (e.g. web\node_modules,
# and __pycache__ under any package), plus the two root-relative paths that
# need to stay narrow so they don't accidentally match an unrelated folder.
$excludeNames = @(
    '.venv', '.venv-service', '.venv-tray', '.git', '.vscode', '.pytest_cache',
    'tests', 'logs', '.runtime', 'node_modules', 'dist', 'luxtime.egg-info',
    'installer', '__pycache__'
)
$excludePaths = @(
    (Join-Path $repositoryRoot 'db\backups')
)

robocopy $repositoryRoot $StagingDir /E /XD $excludeNames $excludePaths /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed while staging the installer payload (exit $LASTEXITCODE)." }

Write-Output "Payload staged at $StagingDir"
