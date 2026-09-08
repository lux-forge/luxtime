[CmdletBinding()]
param(
    [switch]$NoBuild,
    [ValidateRange(1, 600)]
    [int]$WaitSeconds = 120
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$composeFile = Join-Path $repositoryRoot 'docker\compose.yml'
$stopMarker = Join-Path $repositoryRoot '.runtime\intentional-stop'

$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCommand) {
    throw 'Docker CLI was not found. Install and start Docker Desktop, then retry.'
}
& $dockerCommand.Source info *> $null
if ($LASTEXITCODE -ne 0) {
    throw 'Docker Engine is unavailable. Start Docker Desktop, wait until it is ready, then retry.'
}

if (Test-Path -LiteralPath $stopMarker) {
    Remove-Item -LiteralPath $stopMarker -Force
}

$arguments = @('compose', '-f', $composeFile, 'up', '-d')
if (-not $NoBuild) {
    $arguments += '--build'
}
& $dockerCommand.Source @arguments
if ($LASTEXITCODE -ne 0) {
    throw "LuxTime startup failed with exit code $LASTEXITCODE."
}

Write-Output "Waiting up to $WaitSeconds seconds for the LuxTime API..."
$deadline = (Get-Date).AddSeconds($WaitSeconds)
$healthy = $false
do {
    $containerStates = @(
        (& $dockerCommand.Source inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' luxtime-postgres 2>$null),
        (& $dockerCommand.Source inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' luxtime-app 2>$null)
    )
    $containersHealthy = $containerStates.Count -eq 2 -and $containerStates.Where({ $_.Trim() -eq 'healthy' }).Count -eq 2
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:52020/api/health' -TimeoutSec 3
        $healthy = $containersHealthy -and $health.status -eq 'healthy' -and $health.database -eq 'connected'
    }
    catch {
        $healthy = $false
    }
    if (-not $healthy) { Start-Sleep -Seconds 2 }
} while (-not $healthy -and (Get-Date) -lt $deadline)

& $dockerCommand.Source compose -f $composeFile ps
if (-not $healthy) {
    throw "LuxTime containers started, but the API did not become healthy within $WaitSeconds seconds."
}
Write-Output 'LuxTime: http://127.0.0.1:52020'
