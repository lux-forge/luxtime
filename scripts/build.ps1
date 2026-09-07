[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path

Push-Location (Join-Path $repositoryRoot 'web')
try {
    pnpm install --frozen-lockfile
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
    pnpm typecheck
    if ($LASTEXITCODE -ne 0) { throw 'Frontend typecheck failed.' }
    pnpm lint
    if ($LASTEXITCODE -ne 0) { throw 'Frontend lint failed.' }
    pnpm build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
}
finally {
    Pop-Location
}

$python = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Create .venv and install .[dev] before running the build script.'
}
& $python -m pytest -m 'not integration'
if ($LASTEXITCODE -ne 0) { throw 'Backend unit tests failed.' }

docker compose -f (Join-Path $repositoryRoot 'docker\compose.yml') build
if ($LASTEXITCODE -ne 0) { throw 'Container build failed.' }
