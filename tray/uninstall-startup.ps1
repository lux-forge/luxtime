[CmdletBinding()]
param(
    [switch]$StopTray
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
if ($StopTray) {
    & (Join-Path $PSScriptRoot 'stop.ps1')
}
if (Test-Path -LiteralPath $script:LuxTimeTrayShortcut) {
    Remove-Item -LiteralPath $script:LuxTimeTrayShortcut -Force
}
Get-LuxTimeTrayDetails | Format-Table -AutoSize
