param(
  [switch]$DryRun,
  [switch]$StopCollector,
  [switch]$PurgeConfig,
  [string]$TaskName = "Quipu Collector Windows",
  [string]$ConfigPath = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$collectorDir = Join-Path $repoRoot "apps\collector"
$windowsOpsDir = Join-Path $collectorDir "ops\windows"
$defaultConfig = Join-Path $windowsOpsDir "collector.env.ps1"
$config = if ($ConfigPath) { $ConfigPath } else { $defaultConfig }

function Write-Step {
  param([string]$Message)
  if ($DryRun) {
    Write-Output "DRY RUN: $Message"
  } else {
    Write-Output $Message
  }
}

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
  Write-Step "Unregister scheduled task '$TaskName'"
  if (-not $DryRun) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
  }
} else {
  Write-Step "Scheduled task '$TaskName' is not registered"
}

if ($StopCollector) {
  $collectorProcesses = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -ne "powershell.exe" -and
    $_.CommandLine -like "*quipu-collector*"
  }
  if ($collectorProcesses) {
    Write-Step "Stop collector processes: $($collectorProcesses.ProcessId -join ',')"
    if (-not $DryRun) {
      Stop-Process -Id $collectorProcesses.ProcessId -Force
    }
  } else {
    Write-Step "No collector process is running"
  }
}

if ($PurgeConfig -and (Test-Path -LiteralPath $config)) {
  Write-Step "Remove config $config"
  if (-not $DryRun) {
    Remove-Item -LiteralPath $config -Force
  }
}

Write-Step "Quipu collector scheduled task uninstalled."
