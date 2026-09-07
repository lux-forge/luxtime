[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
if (-not (Test-Path -LiteralPath $script:LuxTimeTrayPythonw)) {
    throw 'LuxTime tray dependencies are not installed. Run tray\install-startup.ps1 first.'
}
$existing = Get-LuxTimeTrayProcess
if ($existing) {
    Write-Output "LuxTime tray is already running (PID $($existing.Id))."
    return
}
if (Test-Path -LiteralPath $script:LuxTimeTrayPidFile) {
    Remove-Item -LiteralPath $script:LuxTimeTrayPidFile -Force
}

$process = Start-Process -FilePath $script:LuxTimeTrayPythonw `
    -ArgumentList @('-m', 'tray.main') `
    -WorkingDirectory $script:LuxTimeRepositoryRoot `
    -WindowStyle Hidden `
    -PassThru
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    Start-Sleep -Milliseconds 250
    if ($process.HasExited) { throw "LuxTime tray exited during startup with code $($process.ExitCode)." }
    $running = Get-LuxTimeTrayProcess
    if ($running) {
        Write-Output "LuxTime tray started (PID $($running.Id))."
        return
    }
}
throw 'LuxTime tray did not report a running process within five seconds.'
