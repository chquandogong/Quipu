param(
  [switch]$DryRun,
  [switch]$NoStart,
  [string]$TaskName = "Quipu Collector Windows",
  [string]$ServerUrl = "",
  [string]$Token = "",
  [string]$DeviceId = "",
  [string]$DeviceAlias = "",
  [string]$Interval = "300",
  [string]$ConfigPath = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$collectorDir = Join-Path $repoRoot "apps\collector"
$windowsOpsDir = Join-Path $collectorDir "ops\windows"
$startScript = Join-Path $windowsOpsDir "start-quipu-collector.ps1"
$defaultConfig = Join-Path $windowsOpsDir "collector.env.ps1"
$config = if ($ConfigPath) { $ConfigPath } else { $defaultConfig }
$powershellExe = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$user = (whoami).Trim()

function Write-Step {
  param([string]$Message)
  if ($DryRun) {
    Write-Output "DRY RUN: $Message"
  } else {
    Write-Output $Message
  }
}

function Quote-PowerShellString {
  param([string]$Value)
  return '"' + $Value.Replace('`', '``').Replace('"', '`"') + '"'
}

if (-not (Test-Path -LiteralPath $startScript)) {
  throw "Collector startup script not found: $startScript"
}

if (-not (Test-Path -LiteralPath $config)) {
  $configLines = @(
    ('$env:QUIPU_SERVER_URL = ' + (Quote-PowerShellString $ServerUrl)),
    ('$env:QUIPU_AGENT_TOKEN = ' + (Quote-PowerShellString $Token)),
    '$env:QUIPU_COLLECTOR_ROOT = "/"',
    ('$env:QUIPU_COLLECTOR_DEVICE_ID = ' + (Quote-PowerShellString $DeviceId)),
    ('$env:QUIPU_COLLECTOR_DEVICE_ALIAS = ' + (Quote-PowerShellString $DeviceAlias)),
    '$env:QUIPU_COLLECTOR_BIN = ""',
    ('$env:QUIPU_COLLECTOR_INTERVAL = ' + (Quote-PowerShellString $Interval)),
    '$env:QUIPU_SPOOL_DIR = "$HOME\.local\state\quipu\collector-spool"',
    '$env:QUIPU_SPOOL_MAX_BATCHES = "288"',
    '$env:QUIPU_STATE_DIR = "$HOME\.local\state\quipu\collector-state"'
  )
  Write-Step "Create config $config"
  if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $config) | Out-Null
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllLines($config, [string[]]$configLines, $utf8)
  }
} else {
  Write-Step "Keep existing config $config"
}

$actionArgs = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$startScript`" -ConfigPath `"$config`""
Write-Step "Register scheduled task '$TaskName' for $user"

if (-not $DryRun) {
  $action = New-ScheduledTaskAction -Execute $powershellExe -Argument $actionArgs -WorkingDirectory $collectorDir
  $trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
  $principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
  $settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

  Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description "Start Quipu collector at user logon." `
    -Force | Out-Null

  if (-not $NoStart) {
    Start-ScheduledTask -TaskName $TaskName
  }
}

Write-Step "Quipu collector scheduled task installed."
