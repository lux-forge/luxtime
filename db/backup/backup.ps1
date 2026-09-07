[CmdletBinding()]
param(
    [string]$ComposeFile = (Join-Path $PSScriptRoot '..\..\docker\compose.yml')
)

$ErrorActionPreference = 'Stop'
$composePath = (Resolve-Path -LiteralPath $ComposeFile).Path
$backupRoot = Join-Path $PSScriptRoot '..\backups'
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
$databaseUser = ([string](& docker compose -f $composePath exec -T postgres printenv POSTGRES_USER)).Trim()
$databaseName = ([string](& docker compose -f $composePath exec -T postgres printenv POSTGRES_DB)).Trim()
if ($LASTEXITCODE -ne 0 -or -not $databaseUser -or -not $databaseName) {
    throw 'Could not read PostgreSQL connection settings from the container.'
}

$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$fileName = "luxtime-$stamp.dump"
$hostPath = Join-Path $backupRoot $fileName
if (Test-Path -LiteralPath $hostPath) {
    throw "Backup already exists: $hostPath"
}

& docker compose -f $composePath exec -T postgres pg_dump -U $databaseUser -d $databaseName -Fc --schema=luxtime -f "/backups/$fileName"
if ($LASTEXITCODE -ne 0) {
    throw 'PostgreSQL backup failed.'
}

& docker compose -f $composePath exec -T postgres pg_restore --list "/backups/$fileName" | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw 'Backup was created but PostgreSQL could not read it.'
}

Write-Output $hostPath
