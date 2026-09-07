[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
Assert-LuxTimeAdministrator
$service = Get-LuxTimeWindowsService
if (-not $service) {
    Write-Output "Windows service $script:LuxTimeServiceName is already absent."
    return
}
if ($service.Status -ne 'Stopped') {
    Stop-Service -Name $script:LuxTimeServiceName
    $service.WaitForStatus('Stopped', [TimeSpan]::FromSeconds(30))
}

Push-Location $script:LuxTimeRepositoryRoot
try {
    & $script:LuxTimeServicePython $script:LuxTimeServiceHost remove
    if ($LASTEXITCODE -ne 0) { throw 'Windows service removal failed.' }
}
finally {
    Pop-Location
}

Get-LuxTimeServiceDetails | Format-Table -AutoSize
