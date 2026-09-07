[CmdletBinding()]
param(
    [switch]$NoBuild
)

$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'run.ps1') -NoBuild:$NoBuild
