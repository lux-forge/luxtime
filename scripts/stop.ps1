[CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'Medium')]
param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$composeFile = Join-Path $repositoryRoot 'docker\compose.yml'
$runtimeRoot = Join-Path $repositoryRoot '.runtime'
$stopMarker = Join-Path $runtimeRoot 'intentional-stop'

if (-not $PSCmdlet.ShouldProcess('LuxTime Compose stack', 'Stop intentionally')) {
    return
}

New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
Set-Content -LiteralPath $stopMarker -Value (Get-Date).ToUniversalTime().ToString('O') -NoNewline

$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCommand) {
    throw 'Docker CLI was not found. The intentional-stop marker was set, but the runtime could not be stopped.'
}
& $dockerCommand.Source compose --project-directory $repositoryRoot -f $composeFile down
if ($LASTEXITCODE -ne 0) {
    throw "LuxTime shutdown failed with exit code $LASTEXITCODE."
}
