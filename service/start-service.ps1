[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
Assert-LuxTimeAdministrator
$service = Get-LuxTimeWindowsService
if (-not $service) { throw "Windows service $script:LuxTimeServiceName is not installed." }
if ($service.Status -ne 'Running') {
    Start-Service -Name $script:LuxTimeServiceName
    $service.WaitForStatus('Running', [TimeSpan]::FromSeconds(30))
}
Get-LuxTimeServiceDetails | Format-Table -AutoSize
