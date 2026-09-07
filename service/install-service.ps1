[CmdletBinding()]
param(
    [switch]$NoStart
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
Assert-LuxTimeAdministrator

$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCommand) {
    throw 'Docker CLI was not found. Install Docker Desktop before installing LuxTime Service.'
}
$dockerHost = ([string](& docker context inspect --format '{{.Endpoints.docker.Host}}')).Trim()
if ($LASTEXITCODE -ne 0 -or -not $dockerHost) {
    throw 'The active Docker endpoint could not be determined.'
}

$runtimeRoot = Join-Path $script:LuxTimeRepositoryRoot '.runtime'
New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
@{
    docker_executable = $dockerCommand.Source
    docker_host = $dockerHost
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtimeRoot 'service-config.json') -Encoding utf8

if (-not (Test-Path -LiteralPath $script:LuxTimeServicePython)) {
    python -m venv (Join-Path $script:LuxTimeRepositoryRoot '.venv-service')
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the LuxTime service Python environment.' }
}

& $script:LuxTimeServicePython -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Service dependency installation failed.' }

$existing = Get-LuxTimeWindowsService
$operation = if ($existing) { 'update' } else { 'install' }
Push-Location $script:LuxTimeRepositoryRoot
try {
    & $script:LuxTimeServicePython $script:LuxTimeServiceHost --startup delayed $operation
    if ($LASTEXITCODE -ne 0) { throw "Windows service $operation failed." }
}
finally {
    Pop-Location
}

& sc.exe failure $script:LuxTimeServiceName 'reset=' 86400 'actions=' 'restart/15000/restart/30000/restart/60000' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Could not configure Windows service failure recovery.' }
& sc.exe failureflag $script:LuxTimeServiceName 1 | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Could not enable Windows service failure recovery.' }

if (-not $NoStart) {
    $service = Get-LuxTimeWindowsService
    if ($service.Status -ne 'Running') {
        Start-Service -Name $script:LuxTimeServiceName
        $service.WaitForStatus('Running', [TimeSpan]::FromSeconds(30))
    }
}

Get-LuxTimeServiceDetails | Format-Table -AutoSize
