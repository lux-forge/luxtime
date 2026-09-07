[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
Assert-LuxTimeAdministrator
$service = Get-LuxTimeWindowsService
if (-not $service) { throw "Windows service $script:LuxTimeServiceName is not installed." }
if ($service.Status -ne 'Stopped') {
    Stop-Service -Name $script:LuxTimeServiceName
    $service.WaitForStatus('Stopped', [TimeSpan]::FromSeconds(30))
}
Get-LuxTimeServiceDetails | Format-Table -AutoSize
Write-Output 'The LuxTime runtime was not stopped; this command stops only the watchdog service.'
