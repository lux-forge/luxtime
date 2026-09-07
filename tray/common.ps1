$script:LuxTimeRepositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$script:LuxTimeTrayPython = Join-Path $script:LuxTimeRepositoryRoot '.venv-tray\Scripts\python.exe'
$script:LuxTimeTrayPythonw = Join-Path $script:LuxTimeRepositoryRoot '.venv-tray\Scripts\pythonw.exe'
$script:LuxTimeTrayPidFile = Join-Path $script:LuxTimeRepositoryRoot '.runtime\tray.pid'
$script:LuxTimeTrayShortcut = Join-Path ([Environment]::GetFolderPath('Startup')) 'LuxTime Tray.lnk'

function Get-LuxTimeTrayProcess {
    if (-not (Test-Path -LiteralPath $script:LuxTimeTrayPidFile)) { return $null }
    $pidValue = 0
    if (-not [int]::TryParse((Get-Content -Raw -LiteralPath $script:LuxTimeTrayPidFile), [ref]$pidValue)) {
        return $null
    }
    $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if (-not $process) { return $null }
    $command = (Get-CimInstance Win32_Process -Filter "ProcessId = $pidValue" -ErrorAction SilentlyContinue).CommandLine
    if ($command -notmatch 'tray\.main') { return $null }
    return $process
}

function Get-LuxTimeTrayDetails {
    $process = Get-LuxTimeTrayProcess
    [pscustomobject]@{
        StartupRegistration = if (Test-Path -LiteralPath $script:LuxTimeTrayShortcut) { 'Installed' } else { 'Not installed' }
        Process = if ($process) { 'Running' } else { 'Not running' }
        ProcessId = if ($process) { $process.Id } else { $null }
        Shortcut = $script:LuxTimeTrayShortcut
    }
}
