[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
Get-LuxTimeServiceDetails | Format-Table -AutoSize
