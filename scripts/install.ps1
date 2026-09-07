[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
& (Join-Path $repositoryRoot 'service\install-service.ps1')
& (Join-Path $PSScriptRoot 'start.ps1')
& (Join-Path $repositoryRoot 'tray\install-startup.ps1')
& (Join-Path $PSScriptRoot 'status.ps1')
