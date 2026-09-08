[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$webRoot = Join-Path $repositoryRoot 'web'
$nodeModules = Join-Path $webRoot 'node_modules'
$viteCache = Join-Path $webRoot '.vite'
$buildRuntime = Join-Path $repositoryRoot '.runtime\build'
$pnpmStore = Join-Path $buildRuntime 'pnpm-store'
$versionMatch = (Select-String -LiteralPath (Join-Path $repositoryRoot 'pyproject.toml') -Pattern '^version = "([0-9]+\.[0-9]+\.[0-9]+)"$').Matches
if ($versionMatch.Count -ne 1) {
    throw 'Could not determine the LuxTime version from pyproject.toml.'
}
$applicationVersion = $versionMatch[0].Groups[1].Value

function Remove-LuxTimeBuildPath {
    param([Parameter(Mandatory)][string]$Path)

    $fullPath = [IO.Path]::GetFullPath($Path)
    $rootPrefix = [IO.Path]::GetFullPath($repositoryRoot).TrimEnd('\') + '\'
    if (-not $fullPath.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a build path outside the repository: $fullPath"
    }
    if (Test-Path -LiteralPath $fullPath) {
        Remove-Item -LiteralPath $fullPath -Recurse -Force
    }
}

# A full build is intentionally clean and non-interactive. The pnpm content
# store is local to this run and removed afterward, so no package cache remains.
Remove-LuxTimeBuildPath -Path $nodeModules
Remove-LuxTimeBuildPath -Path $viteCache
Remove-LuxTimeBuildPath -Path $buildRuntime
New-Item -ItemType Directory -Path $pnpmStore -Force | Out-Null

$previousCi = $env:CI
$previousNpmYes = $env:npm_config_yes
$env:CI = 'true'
$env:npm_config_yes = 'true'

Push-Location $webRoot
try {
    pnpm install --frozen-lockfile --store-dir $pnpmStore
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
    $env:CI = $previousCi
    $env:npm_config_yes = $previousNpmYes
    Remove-LuxTimeBuildPath -Path $buildRuntime
    Remove-LuxTimeBuildPath -Path $viteCache
}

$python = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Create .venv and install .[dev] before running the build script.'
}
Push-Location $repositoryRoot
try {
    & $python -m pytest (Join-Path $repositoryRoot 'tests') -m 'not integration'
    if ($LASTEXITCODE -ne 0) { throw 'Backend unit tests failed.' }
}
finally {
    Pop-Location
}

Write-Output "Building LuxTime $applicationVersion container image..."
docker compose -f (Join-Path $repositoryRoot 'docker\compose.yml') build --no-cache --build-arg "LUXTIME_VERSION=$applicationVersion"
if ($LASTEXITCODE -ne 0) { throw 'Container build failed.' }
