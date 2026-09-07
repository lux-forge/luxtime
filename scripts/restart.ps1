[CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'Medium')]
param(
    [switch]$Build
)

$ErrorActionPreference = 'Stop'
if (-not $PSCmdlet.ShouldProcess('LuxTime Compose stack', 'Restart intentionally')) { return }
& (Join-Path $PSScriptRoot 'stop.ps1') -Confirm:$false
& (Join-Path $PSScriptRoot 'start.ps1') -NoBuild:(-not $Build)
