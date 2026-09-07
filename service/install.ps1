[CmdletBinding()]
param([switch]$NoStart)

& (Join-Path $PSScriptRoot 'install-service.ps1') -NoStart:$NoStart
if ($LASTEXITCODE -ne 0) { throw 'LuxTime service installation failed.' }
