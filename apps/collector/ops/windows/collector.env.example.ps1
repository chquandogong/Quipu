# Quipu collector Windows scheduled-task environment.
#
# Copy this file to apps/collector/ops/windows/collector.env.ps1 and edit it
# before registering the scheduled task.

$env:QUIPU_SERVER_URL = "http://127.0.0.1:8000"
$env:QUIPU_AGENT_TOKEN = "replace-with-enrollment-token"
$env:QUIPU_COLLECTOR_ROOT = "/"

# Optional: override the generated device ID.
$env:QUIPU_COLLECTOR_DEVICE_ID = ""

# Optional: friendly name shown beside the hostname in the Quipu UI.
$env:QUIPU_COLLECTOR_DEVICE_ALIAS = ""

# Optional: override the collector binary path when installed outside the repo
# virtual environment.
$env:QUIPU_COLLECTOR_BIN = ""

# Optional: background loop interval in seconds.
$env:QUIPU_COLLECTOR_INTERVAL = "300"

# Optional: offline buffer settings. 288 five-minute batches is roughly one day.
$env:QUIPU_SPOOL_DIR = "$HOME\.local\state\quipu\collector-spool"
$env:QUIPU_SPOOL_MAX_BATCHES = "288"

# Optional: collector state used to calculate NVMe read/write bytes per second.
$env:QUIPU_STATE_DIR = "$HOME\.local\state\quipu\collector-state"

# Optional: explicit paths when smartmontools or LibreHardwareMonitor are not discoverable.
$env:QUIPU_SMARTCTL_BIN = ""
$env:QUIPU_LIBRE_HARDWARE_MONITOR_DLL = ""
