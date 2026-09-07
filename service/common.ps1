$script:LuxTimeServiceName = 'LuxTimeService'
$script:LuxTimeRepositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$script:LuxTimeServicePython = Join-Path $script:LuxTimeRepositoryRoot '.venv-service\Scripts\python.exe'
$script:LuxTimeServiceHost = Join-Path $PSScriptRoot 'windows_service.py'

function Assert-LuxTimeAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'This command requires an elevated PowerShell terminal (Run as administrator).'
    }
}

function Get-LuxTimeWindowsService {
    Get-Service -Name $script:LuxTimeServiceName -ErrorAction SilentlyContinue
}

function Get-LuxTimeServiceDetails {
    $service = Get-LuxTimeWindowsService
    if (-not $service) {
        return [pscustomobject]@{
            Name = $script:LuxTimeServiceName
            Installed = $false
            Status = 'Not installed'
            StartupType = 'Not installed'
        }
    }
    $registryPath = "HKLM:\SYSTEM\CurrentControlSet\Services\$script:LuxTimeServiceName"
    $delayed = (Get-ItemProperty -LiteralPath $registryPath -Name DelayedAutoStart -ErrorAction SilentlyContinue).DelayedAutoStart
    [pscustomobject]@{
        Name = $service.Name
        Installed = $true
        Status = [string]$service.Status
        StartupType = if ($delayed -eq 1) { 'Automatic (Delayed Start)' } else { [string]$service.StartType }
    }
}
