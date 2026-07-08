param(
  [string]$ConfigPath = ""
)

$ErrorActionPreference = "Stop"

$collectorDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$collectorExe = Join-Path $collectorDir ".venv\Scripts\quipu-collector.exe"
$logDir = Join-Path $collectorDir "logs"
$outLog = Join-Path $logDir "quipu-collector.out.log"
$errLog = Join-Path $logDir "quipu-collector.err.log"
$statusLog = Join-Path $logDir "quipu-collector-startup.log"
$defaultConfig = Join-Path $PSScriptRoot "collector.env.ps1"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Write-StartupLog {
  param([string]$Message)
  "$(Get-Date -Format o) $Message" | Out-File -FilePath $statusLog -Append -Encoding utf8
}

if (-not $ConfigPath) {
  $ConfigPath = if ($env:QUIPU_COLLECTOR_ENV) { $env:QUIPU_COLLECTOR_ENV } else { $defaultConfig }
}

if (Test-Path -LiteralPath $ConfigPath) {
  . $ConfigPath
} else {
  Write-StartupLog "config file not found, using process environment: $ConfigPath"
}

if (-not $env:QUIPU_SERVER_URL) {
  Write-StartupLog "QUIPU_SERVER_URL is required"
  exit 64
}

if (-not $env:QUIPU_AGENT_TOKEN) {
  Write-StartupLog "QUIPU_AGENT_TOKEN is required"
  exit 64
}

$collectorBin = if ($env:QUIPU_COLLECTOR_BIN) { $env:QUIPU_COLLECTOR_BIN } else { $collectorExe }
$collectorInterval = if ($env:QUIPU_COLLECTOR_INTERVAL) { $env:QUIPU_COLLECTOR_INTERVAL } else { "300" }
$collectorRoot = if ($env:QUIPU_COLLECTOR_ROOT) { $env:QUIPU_COLLECTOR_ROOT } else { "/" }
$spoolDir = if ($env:QUIPU_SPOOL_DIR) { $env:QUIPU_SPOOL_DIR } else { "$HOME\.local\state\quipu\collector-spool" }
$spoolMaxBatches = if ($env:QUIPU_SPOOL_MAX_BATCHES) { $env:QUIPU_SPOOL_MAX_BATCHES } else { "288" }
$stateDir = if ($env:QUIPU_STATE_DIR) { $env:QUIPU_STATE_DIR } else { "$HOME\.local\state\quipu\collector-state" }
$deviceId = $env:QUIPU_COLLECTOR_DEVICE_ID

if (-not (Test-Path -LiteralPath $collectorBin)) {
  Write-StartupLog "collector executable not found: $collectorBin"
  exit 1
}

$runningCollector = Get-CimInstance Win32_Process | Where-Object {
  $_.ProcessId -ne $PID -and
  $_.CommandLine -like "*quipu-collector*" -and
  $_.CommandLine -like "*$($env:QUIPU_SERVER_URL)*" -and
  (-not $deviceId -or $_.CommandLine -like "*--device-id $deviceId*")
}

if ($runningCollector) {
  Write-StartupLog "collector already running: $($runningCollector.ProcessId -join ',')"
  exit 0
}

$collectorArgs = @(
  "--root", $collectorRoot,
  "--server-url", $env:QUIPU_SERVER_URL,
  "--token", $env:QUIPU_AGENT_TOKEN,
  "--offline-buffer",
  "--interval", $collectorInterval,
  "--spool-dir", $spoolDir,
  "--spool-max-batches", $spoolMaxBatches,
  "--state-dir", $stateDir
)

if ($env:QUIPU_COLLECTOR_DEVICE_ID) {
  $collectorArgs += @("--device-id", $env:QUIPU_COLLECTOR_DEVICE_ID)
}

if ($env:QUIPU_COLLECTOR_DEVICE_ALIAS) {
  $collectorArgs += @("--device-alias", $env:QUIPU_COLLECTOR_DEVICE_ALIAS)
}

$process = Start-Process `
  -FilePath $collectorBin `
  -ArgumentList $collectorArgs `
  -WorkingDirectory $collectorDir `
  -RedirectStandardOutput $outLog `
  -RedirectStandardError $errLog `
  -WindowStyle Hidden `
  -PassThru

Write-StartupLog "started collector pid=$($process.Id)"
