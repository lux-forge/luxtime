[CmdletBinding()]
param(
    [string]$ComposeFile = (Join-Path $PSScriptRoot '..\..\docker\compose.yml')
)

$ErrorActionPreference = 'Stop'
$composePath = (Resolve-Path -LiteralPath $ComposeFile).Path
$databaseUser = ([string](& docker compose -f $composePath exec -T postgres printenv POSTGRES_USER)).Trim()
$databaseName = ([string](& docker compose -f $composePath exec -T postgres printenv POSTGRES_DB)).Trim()
if ($LASTEXITCODE -ne 0 -or -not $databaseUser -or -not $databaseName) {
    throw 'Could not read PostgreSQL connection settings from the container.'
}

& docker compose -f $composePath exec -T postgres pg_isready -U $databaseUser -d $databaseName
if ($LASTEXITCODE -ne 0) {
    throw 'PostgreSQL connectivity check failed.'
}

& docker compose -f $composePath exec -T postgres psql -v ON_ERROR_STOP=1 -U $databaseUser -d $databaseName -f /db/verify/verify.sql
if ($LASTEXITCODE -ne 0) {
    throw 'LuxTime database verification failed.'
}
