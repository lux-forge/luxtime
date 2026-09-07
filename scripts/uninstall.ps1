[CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'High')]
param(
    [switch]$KeepRuntime
)

$ErrorActionPreference = 'Stop'
if (-not $PSCmdlet.ShouldProcess('LuxTime Windows service and tray startup', 'Uninstall')) { return }
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
& (Join-Path $repositoryRoot 'tray\uninstall-startup.ps1') -StopTray
if (-not $KeepRuntime) {
    & (Join-Path $PSScriptRoot 'stop.ps1') -Confirm:$false
}
& (Join-Path $repositoryRoot 'service\uninstall-service.ps1')
& (Join-Path $PSScriptRoot 'status.ps1')
