[CmdletBinding()]
param(
    [switch]$SkipPythonRuntime,
    [switch]$SkipPayload,
    [string]$OutFile = (Join-Path $PSScriptRoot '..\dist\LuxTime-Setup.msi')
)

<#
Builds the LuxTime WiX MSI end to end:

  1. Stage the Docker-build-context + host-side source payload (stage-payload.ps1)
  2. Stage a self-contained embeddable Python with the service/tray
     dependencies pre-installed (build-python-runtime.ps1)
  3. Compile installer\*.wxs into a single MSI with `wix build`

Requires the WiX v5 CLI on PATH (`dotnet tool install --global wix`, then
`wix extension add -g WixToolset.Util.wixext/5.0.2` and
`WixToolset.UI.wixext/5.0.2`) - this is a build-machine-only requirement,
never needed on the end user's machine.
#>

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$payloadDir = Join-Path $PSScriptRoot 'build\payload'
$pythonRuntimeDir = Join-Path $PSScriptRoot 'build\python-runtime'

if (-not (Get-Command wix -ErrorAction SilentlyContinue)) {
    throw 'The WiX v5 CLI ("wix") was not found on PATH. Install it with: dotnet tool install --global wix'
}

if (-not $SkipPayload) {
    & (Join-Path $PSScriptRoot 'stage-payload.ps1') -StagingDir $payloadDir
}
if (-not $SkipPythonRuntime) {
    & (Join-Path $PSScriptRoot 'build-python-runtime.ps1') -StagingDir $pythonRuntimeDir
}

$pyprojectVersion = (Select-String -LiteralPath (Join-Path $repositoryRoot 'pyproject.toml') -Pattern '^version = "(.+)"').Matches[0].Groups[1].Value

$outDir = Split-Path -Parent $OutFile
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$OutFile = (Resolve-Path -LiteralPath $outDir).Path | Join-Path -ChildPath (Split-Path -Leaf $OutFile)

# Product.wxs/Components.wxs reference assets\... with paths relative to the
# installer\ folder, so wix build must run from there.
Push-Location $PSScriptRoot
try {
    wix build 'Product.wxs' 'Components.wxs' `
        -ext WixToolset.Util.wixext -ext WixToolset.UI.wixext `
        -d LuxTimeVersion=$pyprojectVersion `
        -d PayloadDir=$payloadDir `
        -d PythonRuntimeDir=$pythonRuntimeDir `
        -arch x64 `
        -out $OutFile
    if ($LASTEXITCODE -ne 0) { throw 'wix build failed.' }
}
finally {
    Pop-Location
}

Write-Output "LuxTime installer built at $OutFile"
