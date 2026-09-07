[CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile,
    [string]$ComposeFile = (Join-Path $PSScriptRoot '..\..\docker\compose.yml')
)

$ErrorActionPreference = 'Stop'
$composePath = (Resolve-Path -LiteralPath $ComposeFile).Path
$backupRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\backups')).Path
$backupPath = (Resolve-Path -LiteralPath $BackupFile).Path
$databaseUser = ([string](& docker compose -f $composePath exec -T postgres printenv POSTGRES_USER)).Trim()
$databaseName = ([string](& docker compose -f $composePath exec -T postgres printenv POSTGRES_DB)).Trim()
if ($LASTEXITCODE -ne 0 -or -not $databaseUser -or -not $databaseName) {
    throw 'Could not read PostgreSQL connection settings from the container.'
}

$relativeBackupPath = [System.IO.Path]::GetRelativePath($backupRoot, $backupPath)
if ([System.IO.Path]::IsPathRooted($relativeBackupPath) -or $relativeBackupPath.StartsWith('..')) {
    throw "Restore files must be placed under $backupRoot."
}

$fileName = Split-Path -Leaf $backupPath
& docker compose -f $composePath exec -T postgres pg_restore --list "/backups/$fileName" | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw 'The selected file is not a readable PostgreSQL backup.'
}

if (-not $PSCmdlet.ShouldProcess('PostgreSQL schema luxtime', "Restore $fileName")) {
    return
}

& docker compose -f $composePath exec -T postgres psql -v ON_ERROR_STOP=1 -U $databaseUser -d $databaseName -c 'DROP SCHEMA IF EXISTS luxtime CASCADE;'
if ($LASTEXITCODE -ne 0) {
    throw 'Could not clear the existing LuxTime schema.'
}

& docker compose -f $composePath exec -T postgres pg_restore -U $databaseUser -d $databaseName --exit-on-error --no-owner --no-privileges "/backups/$fileName"
if ($LASTEXITCODE -ne 0) {
    throw 'PostgreSQL restore failed.'
}

& (Join-Path $PSScriptRoot '..\verify\verify.ps1') -ComposeFile $composePath
