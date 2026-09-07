[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
$process = Get-LuxTimeTrayProcess
if (-not $process) {
    Write-Output 'LuxTime tray is already stopped.'
    return
}
& $script:LuxTimeTrayPython -m tray.control exit
if ($LASTEXITCODE -ne 0) { throw 'Could not signal the LuxTime tray to exit.' }
try {
    [void]$process.WaitForExit(10000)
}
catch {
    throw 'LuxTime tray did not exit within ten seconds.'
}
if (-not $process.HasExited) { throw 'LuxTime tray did not exit within ten seconds.' }
Write-Output 'LuxTime tray stopped; the LuxTime backend was not stopped.'
