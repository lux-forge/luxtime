[CmdletBinding()]
param(
    [ValidateSet('Menu', 'Start', 'Stop', 'Rebuild', 'Build')]
    [string]$Action = 'Menu',
    [ValidateRange(1, 600)]
    [int]$WaitSeconds = 120
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$composeFile = Join-Path $repositoryRoot 'docker\compose.yml'
$stopMarker = Join-Path $repositoryRoot '.runtime\intentional-stop'

function Get-LuxTimeDockerCommand {
    $command = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $command) {
        throw 'Docker CLI was not found. Install and start Docker Desktop, then retry.'
    }
    & $command.Source info *> $null
    if ($LASTEXITCODE -ne 0) {
        throw 'Docker Engine is unavailable. Start Docker Desktop, wait until it is ready, then retry.'
    }
    return $command.Source
}

function Wait-LuxTimeHealthy {
    param([string]$DockerCommand)

    Write-Output "Waiting up to $WaitSeconds seconds for LuxTime..."
    $deadline = (Get-Date).AddSeconds($WaitSeconds)
    $healthy = $false
    do {
        $containerStates = foreach ($containerName in @('luxtime-postgres', 'luxtime-app')) {
            $state = [string](& $DockerCommand inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' $containerName 2>$null)
            if ($LASTEXITCODE -eq 0) { $state.Trim() } else { 'absent' }
        }
        $containersHealthy = $containerStates.Count -eq 2 -and $containerStates.Where({ $_ -eq 'healthy' }).Count -eq 2
        try {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:52020/api/health' -TimeoutSec 3
            $healthy = $containersHealthy -and $health.status -eq 'healthy' -and $health.database -eq 'connected'
        }
        catch {
            $healthy = $false
        }
        if (-not $healthy) { Start-Sleep -Seconds 2 }
    } while (-not $healthy -and (Get-Date) -lt $deadline)

    & $DockerCommand compose -f $composeFile ps
    if (-not $healthy) {
        throw "LuxTime did not become healthy within $WaitSeconds seconds."
    }
    Write-Output 'LuxTime is ready at http://127.0.0.1:52020'
}

function Start-LuxTimeDocker {
    param([switch]$Rebuild)

    $dockerCommand = Get-LuxTimeDockerCommand
    if (Test-Path -LiteralPath $stopMarker) {
        Remove-Item -LiteralPath $stopMarker -Force
    }

    $arguments = @('compose', '-f', $composeFile, 'up', '-d')
    if ($Rebuild) { $arguments += '--build' }
    & $dockerCommand @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "LuxTime Docker startup failed with exit code $LASTEXITCODE."
    }
    Wait-LuxTimeHealthy -DockerCommand $dockerCommand
}

function Invoke-LuxTimeAction {
    param([string]$SelectedAction)

    switch ($SelectedAction) {
        'Start' { Start-LuxTimeDocker }
        'Stop' { & (Join-Path $PSScriptRoot 'stop.ps1') -Confirm:$false }
        'Rebuild' { Start-LuxTimeDocker -Rebuild }
        'Build' { & (Join-Path $PSScriptRoot 'build.ps1') }
    }
}

if ($Action -ne 'Menu') {
    Invoke-LuxTimeAction -SelectedAction $Action
    return
}

while ($true) {
    Write-Host ''
    Write-Host 'LuxTime' -ForegroundColor Cyan
    Write-Host '1. Refresh / start Docker'
    Write-Host '2. Stop Docker'
    Write-Host '3. Rebuild Docker'
    Write-Host '4. Run build script'
    Write-Host '5. Exit'
    Write-Host ''

    $selection = Read-Host 'Choose an option'
    if ($selection -eq '5') { return }

    $selectedAction = switch ($selection) {
        '1' { 'Start' }
        '2' { 'Stop' }
        '3' { 'Rebuild' }
        '4' { 'Build' }
        default { $null }
    }
    if (-not $selectedAction) {
        Write-Host 'Please choose 1, 2, 3, 4, or 5.' -ForegroundColor Yellow
        continue
    }

    try {
        Invoke-LuxTimeAction -SelectedAction $selectedAction
    }
    catch {
        Write-Host "Operation failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}
