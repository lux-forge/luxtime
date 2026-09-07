[CmdletBinding()]
param(
    [string]$PythonVersion = '3.12.7',
    [string]$StagingDir = (Join-Path $PSScriptRoot 'build\python-runtime')
)

<#
Stages a self-contained Windows embeddable Python runtime with the LuxTime
service and tray dependencies pre-installed, so the MSI never needs network
or pip access at install time - it just copies this folder.

Building it once here (rather than as an MSI custom action) also lets
pywin32's own "no postinstall was run" fallback run at build time: pip-installed
pywin32 ships a `pywin32.pth` file that adds `win32`/`win32\lib` to sys.path
and calls `pywin32_bootstrap` (which registers the `pywin32_system32` DLL
directory) - but that only fires once `import site` is enabled, which the
plain embeddable distribution disables by default. Once enabled, calling
`win32serviceutil.LocatePythonServiceExe()` triggers pywin32's own known
relocation of `pythonservice.exe` (and its `pywintypesXXX.dll` dependency)
from `Lib\site-packages\win32\` to the interpreter's own root directory,
which is where Windows' DLL search order and CPython's own `._pth`-relative
path config need it to be for the service host to work when *any* other
program (the SCM's `pythonservice.exe`) loads `pythonXXX.dll`.
#>

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path

if (Test-Path -LiteralPath $StagingDir) {
    Remove-Item -LiteralPath $StagingDir -Recurse -Force
}
New-Item -ItemType Directory -Path $StagingDir -Force | Out-Null

$shortVersion = ($PythonVersion -split '\.')[0..1] -join ''
$embedZip = Join-Path $env:TEMP "python-$PythonVersion-embed-amd64.zip"
if (-not (Test-Path -LiteralPath $embedZip)) {
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip" -OutFile $embedZip
}
Expand-Archive -LiteralPath $embedZip -DestinationPath $StagingDir -Force

$pthFile = Join-Path $StagingDir "python$shortVersion._pth"
(Get-Content -LiteralPath $pthFile) -replace '^#\s*import site', 'import site' | Set-Content -LiteralPath $pthFile

$getPip = Join-Path $env:TEMP 'get-pip.py'
if (-not (Test-Path -LiteralPath $getPip)) {
    Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile $getPip
}

$python = Join-Path $StagingDir 'python.exe'
& $python $getPip --no-warn-script-location
if ($LASTEXITCODE -ne 0) { throw 'Could not bootstrap pip into the embeddable Python runtime.' }

& $python -m pip install `
    -r (Join-Path $repositoryRoot 'service\requirements.txt') `
    -r (Join-Path $repositoryRoot 'tray\requirements.txt') `
    --no-warn-script-location
if ($LASTEXITCODE -ne 0) { throw 'Could not install service/tray dependencies into the embeddable Python runtime.' }

& $python -c 'import win32serviceutil; win32serviceutil.LocatePythonServiceExe()'
if ($LASTEXITCODE -ne 0) { throw 'Could not stage pythonservice.exe next to the embeddable Python runtime.' }

# pip itself isn't needed once dependencies are installed - drop it to keep the MSI payload lean.
& $python -m pip uninstall --yes pip
Get-ChildItem -LiteralPath $StagingDir -Recurse -Directory -Filter '__pycache__' |
    Remove-Item -Recurse -Force

Write-Output "Python runtime staged at $StagingDir"
