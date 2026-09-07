[CmdletBinding()]
param(
    [switch]$NoStart
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')

if (-not (Test-Path -LiteralPath $script:LuxTimeTrayPython)) {
    python -m venv (Join-Path $script:LuxTimeRepositoryRoot '.venv-tray')
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the LuxTime tray Python environment.' }
}
& $script:LuxTimeTrayPython -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Tray dependency installation failed.' }

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($script:LuxTimeTrayShortcut)
$shortcut.TargetPath = $script:LuxTimeTrayPythonw
$shortcut.Arguments = '-m tray.main'
$shortcut.WorkingDirectory = $script:LuxTimeRepositoryRoot
$shortcut.Description = 'LuxTime interactive system tray application'
$shortcut.Save()

if (-not $NoStart) {
    & (Join-Path $PSScriptRoot 'start.ps1')
}
Get-LuxTimeTrayDetails | Format-Table -AutoSize
