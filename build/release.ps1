[CmdletBinding()]
param(
    [switch]$QuickBuild
)

<#
One-shot, branch-aware release helper:

  - On 'main': warns and stops. Ongoing work shouldn't happen on main.
  - On 'dev': offers to bump VERSION and open a dev -> main PR, then builds.
  - On anything else: offers to push the branch to 'dev', then builds.

VERSION at the repository root is the single source of truth for LuxTime's
version - pyproject.toml reads it dynamically, installer\build.ps1 reads it
for the MSI's ProductVersion, and this script keeps web\package.json and
README.md's "Current release" line in sync with it whenever it bumps.

Pass -QuickBuild to skip restaging the embeddable Python runtime (fast, safe
to skip when service\requirements.txt / tray\requirements.txt haven't
changed since the last build).
#>

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$versionFile = Join-Path $repositoryRoot 'VERSION'
$packageJsonFile = Join-Path $repositoryRoot 'web\package.json'
$readmeFile = Join-Path $repositoryRoot 'README.md'

function Get-CurrentVersion {
    (Get-Content -LiteralPath $versionFile -Raw).Trim()
}

function Set-LuxTimeVersion([string]$NewVersion) {
    Set-Content -LiteralPath $versionFile -Value $NewVersion -NoNewline

    $packageJson = Get-Content -LiteralPath $packageJsonFile -Raw
    $packageJson = $packageJson -replace '"version":\s*"[^"]+"', "`"version`": `"$NewVersion`""
    Set-Content -LiteralPath $packageJsonFile -Value $packageJson -NoNewline

    $readme = Get-Content -LiteralPath $readmeFile -Raw
    $readme = $readme -replace '(?m)^Current release: \*\*[^*]+\*\*$', "Current release: **$NewVersion**"
    Set-Content -LiteralPath $readmeFile -Value $readme -NoNewline
}

function Get-BumpedVersion([string]$Current, [string]$Part) {
    $parts = $Current -split '\.' | ForEach-Object { [int]$_ }
    if ($parts.Count -ne 3) { throw "VERSION file does not contain a MAJOR.MINOR.PATCH value: '$Current'" }
    switch ($Part) {
        'major' { $parts[0]++; $parts[1] = 0; $parts[2] = 0 }
        'minor' { $parts[1]++; $parts[2] = 0 }
        'patch' { $parts[2]++ }
    }
    return "$($parts[0]).$($parts[1]).$($parts[2])"
}

function Invoke-Build {
    $buildArguments = @()
    if ($QuickBuild) { $buildArguments += '-SkipPythonRuntime' }
    Write-Output 'Building LuxTime installer...'
    & (Join-Path $repositoryRoot 'installer\build.ps1') @buildArguments
    if ($LASTEXITCODE -ne 0) { throw "installer\build.ps1 failed with exit code $LASTEXITCODE." }
}

$branch = (git -C $repositoryRoot rev-parse --abbrev-ref HEAD).Trim()
Write-Output "Current branch: $branch"

switch ($branch) {
    'main' {
        Write-Warning "You're on 'main'. Ongoing work belongs on 'dev' or a feature branch - 'main' is reserved for releases via PR. Switch branches and re-run. No build was made."
        return
    }

    'dev' {
        $answer = Read-Host "Bump the version and open a PR to main? [y/N]"
        if ($answer -match '^[Yy]') {
            $current = Get-CurrentVersion
            $part = Read-Host "Bump major/minor/patch? [patch]"
            if ([string]::IsNullOrWhiteSpace($part)) { $part = 'patch' }
            if ($part -notin @('major', 'minor', 'patch')) { throw "Unrecognized bump type '$part'." }

            $newVersion = Get-BumpedVersion -Current $current -Part $part
            Write-Output "Bumping version: $current -> $newVersion"
            Set-LuxTimeVersion -NewVersion $newVersion

            git -C $repositoryRoot add VERSION web/package.json README.md
            if ($LASTEXITCODE -ne 0) { throw 'git add failed.' }
            git -C $repositoryRoot commit -m "Bump version to $newVersion"
            if ($LASTEXITCODE -ne 0) { throw 'git commit failed.' }
            git -C $repositoryRoot push origin dev
            if ($LASTEXITCODE -ne 0) { throw 'git push failed.' }

            gh pr create --base main --head dev --title "Release $newVersion" --body "Version bump: $current -> $newVersion."
            if ($LASTEXITCODE -ne 0) { throw 'gh pr create failed.' }
        }
        else {
            Write-Output 'Skipping PR and version bump.'
        }
    }

    default {
        $answer = Read-Host "Push '$branch' to 'dev'? [y/N]"
        if ($answer -match '^[Yy]') {
            git -C $repositoryRoot push origin "HEAD:dev"
            if ($LASTEXITCODE -ne 0) { throw 'git push failed.' }
        }
        else {
            Write-Output 'Skipping push.'
        }
    }
}

Invoke-Build
