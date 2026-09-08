[CmdletBinding()]
param(
    [ValidateSet('Menu', 'Start', 'Stop', 'Rebuild', 'Build', 'Publish')]
    [string]$Action = 'Menu',
    [string]$ReleaseVersion,
    [ValidateRange(1, 600)]
    [int]$WaitSeconds = 120
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$composeFile = Join-Path $repositoryRoot 'docker\compose.yml'
$stopMarker = Join-Path $repositoryRoot '.runtime\intentional-stop'

function Get-LuxTimeDockerCommand {
    $command = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $command) {
        throw 'Docker CLI was not found. Install and start Docker Desktop, then retry.'
    }
    & $command.Source info *> $null
    if ($LASTEXITCODE -ne 0) {
        throw 'Docker Engine is unavailable. Start Docker Desktop, wait until it is ready, then retry.'
    }
    return $command.Source
}

function Wait-LuxTimeHealthy {
    param([string]$DockerCommand)

    Write-Output "Waiting up to $WaitSeconds seconds for LuxTime..."
    $deadline = (Get-Date).AddSeconds($WaitSeconds)
    $healthy = $false
    do {
        $containerStates = foreach ($containerName in @('luxtime-postgres', 'luxtime-app')) {
            $state = [string](& $DockerCommand inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' $containerName 2>$null)
            if ($LASTEXITCODE -eq 0) { $state.Trim() } else { 'absent' }
        }
        $containersHealthy = $containerStates.Count -eq 2 -and $containerStates.Where({ $_ -eq 'healthy' }).Count -eq 2
        try {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:52020/api/health' -TimeoutSec 3
            $healthy = $containersHealthy -and $health.status -eq 'healthy' -and $health.database -eq 'connected'
        }
        catch {
            $healthy = $false
        }
        if (-not $healthy) { Start-Sleep -Seconds 2 }
    } while (-not $healthy -and (Get-Date) -lt $deadline)

    & $DockerCommand compose -f $composeFile ps
    if (-not $healthy) {
        throw "LuxTime did not become healthy within $WaitSeconds seconds."
    }
    Write-Output 'LuxTime is ready at http://127.0.0.1:52020'
}

function Start-LuxTimeDocker {
    param([switch]$Rebuild)

    $dockerCommand = Get-LuxTimeDockerCommand
    if (Test-Path -LiteralPath $stopMarker) {
        Remove-Item -LiteralPath $stopMarker -Force
    }

    $arguments = @('compose', '-f', $composeFile, 'up', '-d')
    if ($Rebuild) { $arguments += '--build' }
    & $dockerCommand @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "LuxTime Docker startup failed with exit code $LASTEXITCODE."
    }
    Wait-LuxTimeHealthy -DockerCommand $dockerCommand
}

function Get-LuxTimeReleaseVersion {
    $pyprojectPath = Join-Path $repositoryRoot 'pyproject.toml'
    $applicationPath = Join-Path $repositoryRoot 'app\__init__.py'
    $pyprojectContent = [IO.File]::ReadAllText($pyprojectPath)
    $applicationContent = [IO.File]::ReadAllText($applicationPath)
    $pyprojectMatch = [regex]::Match($pyprojectContent, '(?m)^version = "([0-9]+\.[0-9]+\.[0-9]+)"(?=\r?$)')
    $applicationMatch = [regex]::Match($applicationContent, '(?m)^__version__ = "([0-9]+\.[0-9]+\.[0-9]+)"(?=\r?$)')

    if (-not $pyprojectMatch.Success -or -not $applicationMatch.Success) {
        throw 'Could not read the release version from pyproject.toml and app\__init__.py.'
    }
    if ($pyprojectMatch.Groups[1].Value -ne $applicationMatch.Groups[1].Value) {
        throw 'Release versions disagree between pyproject.toml and app\__init__.py.'
    }
    return $pyprojectMatch.Groups[1].Value
}

function Set-LuxTimeReleaseVersion {
    param([Parameter(Mandatory)][string]$NewVersion)

    $versionFiles = @(
        @{
            Path = Join-Path $repositoryRoot 'pyproject.toml'
            Pattern = '(?m)^version = "[0-9]+\.[0-9]+\.[0-9]+"(?=\r?$)'
            Replacement = "version = `"$NewVersion`""
        },
        @{
            Path = Join-Path $repositoryRoot 'app\__init__.py'
            Pattern = '(?m)^__version__ = "[0-9]+\.[0-9]+\.[0-9]+"(?=\r?$)'
            Replacement = "__version__ = `"$NewVersion`""
        }
    )

    foreach ($versionFile in $versionFiles) {
        $content = [IO.File]::ReadAllText($versionFile.Path)
        $matches = [regex]::Matches($content, $versionFile.Pattern)
        if ($matches.Count -ne 1) {
            throw "Expected one release version in $($versionFile.Path), found $($matches.Count)."
        }
        $updated = [regex]::Replace($content, $versionFile.Pattern, $versionFile.Replacement)
        [IO.File]::WriteAllText($versionFile.Path, $updated, [Text.UTF8Encoding]::new($false))
    }
}

function Publish-LuxTime {
    param([string]$RequestedVersion)

    $dockerCommand = Get-LuxTimeDockerCommand
    $currentVersion = Get-LuxTimeReleaseVersion
    if ([string]::IsNullOrWhiteSpace($RequestedVersion)) {
        Write-Host "Current release: $currentVersion" -ForegroundColor DarkGray
        $RequestedVersion = Read-Host 'New release version (x.y.z)'
    }
    if ($RequestedVersion -notmatch '^[0-9]+\.[0-9]+\.[0-9]+$') {
        throw 'Release version must use numeric x.y.z format, for example 0.2.0.'
    }
    if ([version]$RequestedVersion -le [version]$currentVersion) {
        throw "Release version must be greater than the current version, $currentVersion."
    }

    Write-Output "Preparing LuxTime $RequestedVersion..."
    Set-LuxTimeReleaseVersion -NewVersion $RequestedVersion
    try {
        & (Join-Path $PSScriptRoot 'build.ps1')
    }
    catch {
        Set-LuxTimeReleaseVersion -NewVersion $currentVersion
        throw "Release build failed and version $currentVersion was restored. $($_.Exception.Message)"
    }

    if (Test-Path -LiteralPath $stopMarker) {
        Remove-Item -LiteralPath $stopMarker -Force
    }
    & $dockerCommand compose -f $composeFile up -d --no-build postgres
    if ($LASTEXITCODE -ne 0) {
        throw "LuxTime database startup failed with exit code $LASTEXITCODE."
    }
    & $dockerCommand compose -f $composeFile up -d --no-build --no-deps --force-recreate app
    if ($LASTEXITCODE -ne 0) {
        throw "LuxTime $RequestedVersion deployment failed with exit code $LASTEXITCODE."
    }
    Wait-LuxTimeHealthy -DockerCommand $dockerCommand
    Write-Output "LuxTime $RequestedVersion is live locally at http://127.0.0.1:52020"
}

function Invoke-LuxTimeAction {
    param([string]$SelectedAction)

    switch ($SelectedAction) {
        'Start' { Start-LuxTimeDocker }
        'Stop' { & (Join-Path $PSScriptRoot 'stop.ps1') -Confirm:$false }
        'Rebuild' { Start-LuxTimeDocker -Rebuild }
        'Build' { & (Join-Path $PSScriptRoot 'build.ps1') }
        'Publish' { Publish-LuxTime -RequestedVersion $ReleaseVersion }
    }
}

if ($Action -ne 'Menu') {
    Invoke-LuxTimeAction -SelectedAction $Action
    return
}

while ($true) {
    Write-Host ''
    Write-Host 'LuxTime' -ForegroundColor Cyan
    Write-Host '1. Refresh / start Docker'
    Write-Host '2. Stop Docker'
    Write-Host '3. Rebuild Docker'
    Write-Host '4. Run build script'
    Write-Host '5. Publish versioned build live'
    Write-Host '6. Exit'
    Write-Host ''

    $selection = Read-Host 'Choose an option'
    if ($selection -eq '6') { return }

    $selectedAction = switch ($selection) {
        '1' { 'Start' }
        '2' { 'Stop' }
        '3' { 'Rebuild' }
        '4' { 'Build' }
        '5' { 'Publish' }
        default { $null }
    }
    if (-not $selectedAction) {
        Write-Host 'Please choose 1, 2, 3, 4, 5, or 6.' -ForegroundColor Yellow
        continue
    }

    try {
        Invoke-LuxTimeAction -SelectedAction $selectedAction
    }
    catch {
        Write-Host "Operation failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}
