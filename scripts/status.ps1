[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Strict
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$results = [System.Collections.Generic.List[object]]::new()

function Add-LuxTimeStatus {
    param([string]$Name, [string]$State, [string]$Detail, [Nullable[bool]]$Healthy)
    $results.Add([pscustomobject]@{
        Name = $Name
        State = $State
        Detail = $Detail
        Healthy = $Healthy
    })
}

. (Join-Path $repositoryRoot 'service\common.ps1')
$service = Get-LuxTimeServiceDetails
Add-LuxTimeStatus 'LuxTime Service' $service.Status $service.StartupType ($service.Installed -and $service.Status -eq 'Running')

$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
$dockerAvailable = $false
if ($dockerCommand) {
    & docker info *> $null
    $dockerAvailable = $LASTEXITCODE -eq 0
}
Add-LuxTimeStatus 'Docker' $(if ($dockerAvailable) { 'Available' } else { 'Unavailable' }) $(if ($dockerCommand) { $dockerCommand.Source } else { 'CLI not found' }) $dockerAvailable

foreach ($containerName in @('luxtime-postgres', 'luxtime-app')) {
    if ($dockerAvailable) {
        $containerState = ([string](& docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' $containerName 2>$null)).Trim()
        if ($LASTEXITCODE -ne 0 -or -not $containerState) { $containerState = 'Absent' }
        Add-LuxTimeStatus $containerName $containerState 'Docker container health' ($containerState -eq 'healthy')
    }
    else {
        Add-LuxTimeStatus $containerName 'Not checked' 'Docker unavailable' $false
    }
}

try {
    $api = Invoke-RestMethod -Uri 'http://127.0.0.1:52020/api/health' -TimeoutSec 3
    $apiHealthy = $api.status -eq 'healthy' -and $api.database -eq 'connected'
    Add-LuxTimeStatus 'API' $(if ($apiHealthy) { 'Healthy' } else { 'Unhealthy' }) "database=$($api.database)" $apiHealthy
}
catch {
    Add-LuxTimeStatus 'API' 'Unreachable' $_.Exception.Message $false
}

try {
    $frontend = Invoke-WebRequest -Uri 'http://127.0.0.1:52020/' -TimeoutSec 3
    Add-LuxTimeStatus 'Frontend' $(if ($frontend.StatusCode -eq 200) { 'Reachable' } else { "HTTP $($frontend.StatusCode)" }) 'http://127.0.0.1:52020' ($frontend.StatusCode -eq 200)
}
catch {
    Add-LuxTimeStatus 'Frontend' 'Unreachable' $_.Exception.Message $false
}

$intentionalMarker = Join-Path $repositoryRoot '.runtime\intentional-stop'
$intentionallyStopped = Test-Path -LiteralPath $intentionalMarker
Add-LuxTimeStatus 'Intentional Stop' $(if ($intentionallyStopped) { 'Yes' } else { 'No' }) $intentionalMarker (-not $intentionallyStopped)

. (Join-Path $repositoryRoot 'tray\common.ps1')
$tray = Get-LuxTimeTrayDetails
Add-LuxTimeStatus 'Tray Startup' $tray.StartupRegistration $tray.Shortcut ($tray.StartupRegistration -eq 'Installed')
Add-LuxTimeStatus 'Tray Process' $tray.Process $(if ($tray.ProcessId) { "PID $($tray.ProcessId)" } else { 'Interactive user session' }) ($tray.Process -eq 'Running')

if ($Json) {
    $results | ConvertTo-Json
}
else {
    $results | Format-Table Name, State, Detail -AutoSize
}

if ($Strict -and $results.Where({ $_.Healthy -eq $false }).Count -gt 0) {
    throw 'One or more LuxTime lifecycle checks failed.'
}
