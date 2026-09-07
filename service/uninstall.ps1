[CmdletBinding()]
param()

& (Join-Path $PSScriptRoot 'uninstall-service.ps1')
if ($LASTEXITCODE -ne 0) { throw 'LuxTime service removal failed.' }
