[CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'High')]
param(
    [string]$ComposeFile = (Join-Path $PSScriptRoot '..\..\docker\compose.yml')
)

$ErrorActionPreference = 'Stop'
$composePath = (Resolve-Path -LiteralPath $ComposeFile).Path
$dbRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path

function Invoke-Compose {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & docker compose -f $composePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose failed with exit code $LASTEXITCODE."
    }
}

Invoke-Compose -Arguments @('up', '-d', 'postgres')
$databaseUser = [string](& docker compose -f $composePath exec -T postgres printenv POSTGRES_USER)
$databaseName = [string](& docker compose -f $composePath exec -T postgres printenv POSTGRES_DB)
if ($LASTEXITCODE -ne 0 -or -not $databaseUser.Trim() -or -not $databaseName.Trim()) {
    throw 'Could not read PostgreSQL connection settings from the container.'
}
$databaseUser = $databaseUser.Trim()
$databaseName = $databaseName.Trim()
Invoke-Compose -Arguments @('exec', '-T', 'postgres', 'pg_isready', '-U', $databaseUser, '-d', $databaseName)

if (-not $PSCmdlet.ShouldProcess('PostgreSQL schema luxtime', 'Drop and rebuild')) {
    return
}

Invoke-Compose -Arguments @('exec', '-T', 'postgres', 'psql', '-v', 'ON_ERROR_STOP=1', '-U', $databaseUser, '-d', $databaseName, '-c', 'DROP SCHEMA IF EXISTS luxtime CASCADE;')

$schemaFiles = Get-ChildItem -LiteralPath (Join-Path $dbRoot 'schema') -Filter '*.sql' -File | Sort-Object Name
foreach ($schemaFile in $schemaFiles) {
    Invoke-Compose -Arguments @('exec', '-T', 'postgres', 'psql', '-v', 'ON_ERROR_STOP=1', '-U', $databaseUser, '-d', $databaseName, '-f', "/db/schema/$($schemaFile.Name)")
}

$seedFiles = Get-ChildItem -LiteralPath (Join-Path $dbRoot 'seed') -Filter '*.sql' -File | Sort-Object Name
foreach ($seedFile in $seedFiles) {
    Invoke-Compose -Arguments @('exec', '-T', 'postgres', 'psql', '-v', 'ON_ERROR_STOP=1', '-U', $databaseUser, '-d', $databaseName, '-f', "/db/seed/$($seedFile.Name)")
}

& (Join-Path $dbRoot 'verify\verify.ps1') -ComposeFile $composePath
if ($LASTEXITCODE -ne 0) {
    throw 'Database verification failed.'
}
