# Quipu User Manual

이 문서는 Quipu를 로컬에서 실행하고, 노트북/컴퓨터 데이터를 수집하고, 화면의
조사 정보를 해석하는 운영자용 매뉴얼입니다. 저장소에 포함된 collector는 읽기
전용 collector입니다. Linux에서는 procfs/sysfs를 읽고, Windows에서는
PowerShell/CIM/netsh/LibreHardwareMonitor가 노출하는 신호를 best-effort로
읽습니다. 외부 collector도 같은 ingest API 계약으로 관측값을 보내면 같은
화면에 표시됩니다.

## 1. 대상 사용자

Quipu는 다음 사용자를 기준으로 설계했습니다.

- Linux 노트북이나 개발 워크스테이션을 직접 운영하는 개발자.
- 팀 장비의 발열, 그래픽 오류, Wi-Fi, 저장장치, 재부팅 문제를 조사하는 운영자.
- 조치 전후 결과와 팀 인계 메모를 남겨야 하는 기술 리더.

Quipu는 원격 수리 도구가 아닙니다. collector는 읽기 전용이고, 서버는 받은
관측값을 저장한 뒤 규칙 기반으로 조사 항목을 만듭니다.

## 2. 준비

필요한 도구:

- Python 3.11 이상 (CI는 3.12에서 검증합니다)
- Node.js 20 이상 (CI는 24에서 검증합니다)
- npm
- Linux 환경: 저장소에 포함된 collector와 systemd timer를 직접 실행할 때 필요합니다.
- Windows 환경: 같은 collector 패키지를 PowerShell scheduled-task wrapper로
  실행할 수 있습니다.

저장소 루트는 이 문서에서 `/home/chquan/Quipu`로 가정합니다. 다른 경로를 쓰면
명령의 경로만 바꾸면 됩니다.

## 3. 서버와 웹 UI 실행

API 서버를 실행합니다. 스크립트가 가상환경 생성과 설치까지 처리하고
`0.0.0.0:8000`에 바인딩하므로, 같은 LAN의 다른 장비 collector도 접근할 수
있습니다. DB 파일은 `data/quipu.sqlite3`입니다.

```bash
cd /home/chquan/Quipu
scripts/dev-server.sh
```

다른 터미널에서 웹 UI를 실행합니다.

```bash
cd /home/chquan/Quipu/apps/web
npm install
npm run dev
```

브라우저:

```text
http://127.0.0.1:5173
```

서버는 시작할 때 데이터를 자동으로 만들지 않습니다. 처음 실행하면 장비가
없는 빈 화면이 정상입니다.

### 샘플 fleet 시딩 (선택)

UI를 먼저 구경하고 싶다면 샘플 fixture(3개 장비: `thinkpad-p1`, `xps-13`,
`framework-13`)를 수동으로 시딩합니다.

```bash
cd /home/chquan/Quipu/apps/server
. .venv/bin/activate
python -m quipu_server.seed ../../fixtures/ingest/team-sample.json \
  --database ../../data/quipu.sqlite3
```

## 4. 샘플 DB를 지우고 이 노트북만 표시

기존 API 서버를 멈춘 뒤 DB 파일을 지웁니다.

```bash
cd /home/chquan/Quipu
rm -f data/quipu.sqlite3 data/quipu.sqlite3-wal data/quipu.sqlite3-shm
```

서버를 다시 시작합니다 (`scripts/dev-server.sh` 또는 직접 uvicorn 실행).

```bash
cd /home/chquan/Quipu/apps/server
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
QUIPU_DATABASE_PATH=../../data/quipu.sqlite3 uvicorn quipu_server.app:app --host 127.0.0.1 --port 8000 --reload
```

다른 터미널에서 collector를 준비하고 한 번 전송합니다.

```bash
cd /home/chquan/Quipu/apps/collector
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
quipu-collector \
  --server-url http://127.0.0.1:8000 \
  --token dev-token \
  --device-id local-computer \
  --device-alias "내 노트북"
```

웹 UI를 새로고침하면 현재 노트북 하나만 표시됩니다.

## 5. 다른 노트북/컴퓨터 연결

Quipu는 여러 노트북이나 워크스테이션이 같은 서버로 관측값을 보내는 구조입니다.
서버가 떠 있는 컴퓨터의 LAN IP를 확인합니다.

```bash
hostname -I
```

`scripts/dev-server.sh`는 `0.0.0.0`에 바인딩하므로 그대로 사용하면 됩니다.
uvicorn을 직접 실행한다면 `--host 0.0.0.0`을 지정합니다.

```bash
cd /home/chquan/Quipu/apps/server
. .venv/bin/activate
QUIPU_DATABASE_PATH=../../data/quipu.sqlite3 uvicorn quipu_server.app:app --host 0.0.0.0 --port 8000
```

방화벽을 쓰고 있다면 TCP `8000` 접근을 허용해야 합니다.

다른 Linux 노트북에서 저장소에 포함된 collector를 설치하고 전송합니다.

```bash
sudo apt-get install smartmontools
cd /path/to/Quipu/apps/collector
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
quipu-collector \
  --server-url http://<server-ip>:8000 \
  --token dev-token \
  --device-id office-gram \
  --device-alias "사무실 그램"
```

규칙:

- `--device-id`는 장비마다 다르게 유지합니다. 나중에 바꾸면 새 장비처럼 보입니다.
- `--device-alias`는 화면에 보일 별명입니다. 바꿔도 같은 `device-id`면 같은 장비로
  업데이트됩니다.
- 별명이 있으면 UI는 `사무실 그램 · office-hostname`처럼 표시합니다.
- 같은 `device-id`의 다음 batch가 `display_name`이나 `cpu_model`을 생략해도
  서버는 기존 별명과 CPU 모델을 보존합니다.
- 빠른 테스트는 `dev-token`으로 가능하지만, 반복 운용은 장치별 token을 권장합니다.

Windows에서는 같은 collector 패키지를 PowerShell scheduled-task wrapper로 실행할
수 있습니다. 같은 server URL, token, 안정적인 `device_id`, 화면용 `display_name`
또는 별명을 사용해 observation batch를 보내면 UI의 `Devices` 목록에 함께 표시됩니다.

Windows 장비에 최신 릴리스를 반영하려면 관리자 PowerShell에서 다음을 실행합니다.

```powershell
cd C:\path\to\Quipu\apps\collector
py -3 -m venv .venv
.\.venv\Scripts\pip.exe install -e .
cd C:\path\to\Quipu
powershell.exe -ExecutionPolicy Bypass -File scripts\install-collector-scheduled-task.ps1 `
  -InstallSensorTools `
  -Highest `
  -ServerUrl http://<server-ip>:8000 `
  -Token dev-token `
  -DeviceId windows `
  -DeviceAlias "윈도우"
```

이미 scheduled task가 있으면 위 설치 스크립트가 같은 이름의 task를 다시 등록하고
시작합니다. 수동으로 재시작하려면 Windows 작업 스케줄러에서 `Quipu Collector
Windows`를 실행하거나 PowerShell에서 `Start-ScheduledTask -TaskName "Quipu
Collector Windows"`를 사용합니다.

Windows scheduled task는 사용자 로그온 시 숨김 실행되고, 중복 실행을 방지하며,
offline buffer를 켠 채 기본 5분 간격(`QUIPU_COLLECTOR_INTERVAL`, 기본 300초)으로
전송합니다. 로그는 `apps\collector\logs\`에 남습니다.

Windows collector 배포 확인 기준:

- `Devices` 목록에 `윈도우 · <hostname>`처럼 별명이 보입니다.
- `last_seen_at`이 collector 실행 시각에 맞게 갱신됩니다.
- `latest_metrics`가 smoke metric 하나만이 아니라 Windows collector가 의도한 CPU,
  memory, disk, Wi-Fi, NVMe, battery 등 신호를 포함합니다.
- healthy 장비라도 클릭하면 상세 텔레메트리(Metric Ledger, Telemetry Matrix,
  Report)가 표시됩니다.

서버에서 Windows 장비 수신 상태를 확인하려면:

```bash
curl -s http://127.0.0.1:8000/api/fleet/overview | python3 -c '
import json, sys
payload = json.load(sys.stdin)
for snap in payload["devices"]:
    device = snap["device"]
    if device.get("display_name") == "윈도우" or device["device_id"] == "windows":
        print(device["device_id"], device.get("display_name"), device["hostname"],
              snap["risk_level"], len(snap["latest_metrics"]), len(snap["recent_events"]))
        print(sorted(snap["latest_metrics"].keys()))
'
```

Windows에서 Linux 전용 metric이 비어 있는 것은 오류가 아닐 수 있습니다. 예를 들어
Linux load average는 Windows에 같은 개념이 없으므로 비어 있을 수 있습니다. 다만
CPU core/thread, memory, battery, Wi-Fi, NVMe capacity까지 비어 있다면 Windows
장비가 아직 이전 collector를 실행 중이거나 scheduled task가 새 가상환경을 사용하지
않는지 먼저 확인합니다. UI에 표시되는 세부 범위는 collector가 보낸 metric/event
이름에 따라 결정됩니다.

현재 Windows collector는 Windows가 CIM, `netsh`, `Get-NetAdapter`,
`Get-StorageReliabilityCounter`, Event Log, `smartctl --json`,
LibreHardwareMonitor WMI 또는 공식 library로 노출하는 범위에서 다음
metric/event를 best-effort로 보냅니다.

- `cpu.physical_cores`, `cpu.logical_threads`
- `memory.used_percent`
- `disk.root_used_percent`
- `battery.capacity_percent`, `battery.ac_online`
- `wifi.signal_dbm`, `wifi.rx_bitrate_mbps`, `wifi.tx_bitrate_mbps`,
  `wifi.link_bitrate_mbps`
- `nvme.capacity_bytes`, `nvme.<device>.capacity_bytes`
- `nvme.temp_c`, `nvme.<device>.temp_c`
- `nvme.smart_passed`, `nvme.critical_warning`, `nvme.available_spare_percent`,
  `nvme.percentage_used_percent`, `nvme.media_errors`
- `nvme.power_on_hours`, `nvme.unsafe_shutdowns`, `nvme.error_log_entries`와
  각각의 `nvme.<device>.*` 장치별 metric
- `nvme.read_bytes_per_sec`, `nvme.write_bytes_per_sec`
- `nvme.<device>.read_bytes_per_sec`, `nvme.<device>.write_bytes_per_sec`
- `thermal.windows_zone_<n>.temp_c`
- `cpu.package_temp_c`, `cpu.core_<n>.temp_c`
- `cpu.p_core_<n>.temp_c`, `cpu.e_core_<n>.temp_c`,
  `cpu.lp_e_core_<n>.temp_c`
- `cpu.load_percent`, `cpu.p_core_<n>.load_percent`,
  `cpu.e_core_<n>.load_percent`, `cpu.lp_e_core_<n>.load_percent`
- `fan.rpm`, `fan.<sensor>.rpm`
- Windows Event Log 기반 `storage`, `network`, `graphics`, `thermal`, `memory`,
  `power`, `reboot`, `update` 이벤트

Windows에서 보낸 metric 이름이 위 목록과 일치하면 기존 UI의 CPU Profile,
Memory Used, Disk Health, Battery Power, Wi-Fi Link, NVMe Capacity,
Fan RPM, Telemetry Matrix에 바로 표시됩니다. Windows CPU core 온도와 core load는
LibreHardwareMonitor/OpenHardwareMonitor가 실제 sensor를 노출할 때 `CPU Cores`,
`CPU Core Load`로 표시됩니다. Windows Event Log 설명이 깨진 문자로 들어오면 UI는
원문 대신 category/source 중심의 짧은 설명을 보여줍니다.

### Windows CPU load와 core 온도 구분

Windows의 CPU load와 CPU 온도는 같은 sensor provider에서 오더라도 서로 다른
sensor type입니다.

- `cpu.load_percent`, `cpu.core_<n>.load_percent`: CPU total/core별 사용률입니다.
  Linux load average와 다른 percent 값입니다.
- `cpu.package_temp_c`, `cpu.core_<n>.temp_c`,
  `cpu.p_core_<n>.temp_c`, `cpu.e_core_<n>.temp_c`: CPU package/core 온도입니다.
- `thermal.windows_zone_<name>.temp_c`: Windows ACPI thermal zone입니다. 시스템
  thermal zone 값일 수 있지만 CPU core 온도로 간주하지 않습니다.

따라서 `CPU Core Load`가 보이는데 `CPU Cores` 온도가 보이지 않는 상태가 가능합니다.
이 경우 화면 문제가 아니라 Windows collector가 `Load` sensor는 받았지만
`Temperature` sensor를 받지 못한 것입니다. 관리자 PowerShell에서 다음을 확인합니다.

```powershell
Get-CimInstance -Namespace root/LibreHardwareMonitor -ClassName Sensor -ErrorAction SilentlyContinue |
  Where-Object SensorType -eq Load |
  Select-Object Name,Parent,Value

Get-CimInstance -Namespace root/LibreHardwareMonitor -ClassName Sensor -ErrorAction SilentlyContinue |
  Where-Object SensorType -eq Temperature |
  Select-Object Name,Parent,Value
```

collector가 실제로 보낼 JSON을 확인하려면:

```powershell
cd C:\path\to\Quipu\apps\collector
.\.venv\Scripts\quipu-collector.exe --dry-run | Select-String "cpu\.|thermal\.|load_percent|temp_c"
```

`load_percent`만 있고 `cpu.*.temp_c`가 없으면 UI가 숨기는 것이 아니라 collector가
CPU 온도 metric을 받지 못한 상태입니다. scheduled task가 관리자 권한인지도 확인합니다.

```powershell
(Get-ScheduledTask -TaskName "Quipu Collector Windows").Principal.RunLevel
```

`Highest`가 아니면 관리자 PowerShell에서 설치 스크립트를 `-Highest`로 다시 실행합니다.
LibreHardwareMonitor가 portable 위치에 있고 DLL을 자동 탐지하지 못하면
`apps\collector\ops\windows\collector.env.ps1`에 다음 값을 지정합니다.

```powershell
$env:QUIPU_LIBRE_HARDWARE_MONITOR_DLL = "C:\path\to\LibreHardwareMonitorLib.dll"
```

장치별 token을 만들려면 서버에서 다음을 실행합니다.

```bash
curl -sS -X POST http://127.0.0.1:8000/api/enrollment/tokens \
  -H "Content-Type: application/json" \
  -H "X-Quipu-Agent-Token: dev-token" \
  -d '{"device_id":"office-gram","label":"Office Gram collector"}'
```

응답의 `token`을 해당 노트북 collector의 `--token`에 넣습니다.

## 6. Collector 명령

로컬 JSON만 보고 싶을 때:

```bash
quipu-collector --dry-run
```

서버로 한 번 전송:

```bash
quipu-collector --server-url http://127.0.0.1:8000 --token dev-token --device-alias "내 노트북"
```

60초 간격으로 세 번 dry-run:

```bash
quipu-collector --dry-run --interval 60 --iterations 3
```

서버 장애나 네트워크 장애 때 로컬 spool에 보관:

```bash
quipu-collector \
  --server-url http://127.0.0.1:8000 \
  --token "$QUIPU_AGENT_TOKEN" \
  --offline-buffer \
  --spool-dir ~/.local/state/quipu/collector-spool \
  --state-dir ~/.local/state/quipu/collector-state
```

동작 규칙:

- `--offline-buffer`는 전송 실패한 batch를 spool 디렉터리에 JSON 파일로
  보관하고, 다음 성공 시 오래된 것부터 flush합니다. 보존 개수는
  `--spool-max-batches`(기본 288, 5분 간격 기준 약 하루)로 제한합니다.
- `--state-dir`는 NVMe 읽기/쓰기 처리량을 계산하기 위한 이전 sector counter를
  저장합니다. 첫 샘플에는 비교 기준이 없어서 NVMe R/W 속도가 비어 있을 수 있고,
  같은 장비의 다음 샘플부터 초당 처리량이 계산됩니다.
- `--once`는 `--interval`/`--iterations`와 함께 쓸 수 없고, `--iterations`는
  `--interval`이 필요합니다.

## 7. systemd timer로 5분마다 수집

collector 실행 파일을 먼저 준비합니다.

```bash
cd /home/chquan/Quipu/apps/collector
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

설치 미리보기:

```bash
cd /home/chquan/Quipu
scripts/install-collector-systemd.sh --dry-run
```

설치:

```bash
sudo scripts/install-collector-systemd.sh --no-enable
```

환경 파일:

```bash
sudo tee /etc/quipu/collector.env >/dev/null <<EOF
QUIPU_SERVER_URL=http://127.0.0.1:8000
QUIPU_AGENT_TOKEN=dev-token
QUIPU_COLLECTOR_ROOT=/
QUIPU_COLLECTOR_DEVICE_ID=local-computer
QUIPU_COLLECTOR_DEVICE_ALIAS=내 노트북
QUIPU_COLLECTOR_BIN=/home/chquan/Quipu/apps/collector/.venv/bin/quipu-collector
QUIPU_SPOOL_DIR=/var/lib/quipu/collector-spool
QUIPU_SPOOL_MAX_BATCHES=288
QUIPU_STATE_DIR=/var/lib/quipu/collector-state
EOF
sudo chmod 600 /etc/quipu/collector.env
```

수동 실행 확인:

```bash
sudo systemctl start quipu-collector.service
systemctl status quipu-collector.service --no-pager
journalctl -u quipu-collector.service -n 80 --no-pager
```

timer 활성화:

```bash
sudo systemctl enable --now quipu-collector.timer
systemctl list-timers quipu-collector.timer
```

비활성화:

```bash
sudo systemctl disable --now quipu-collector.timer
```

제거:

```bash
sudo scripts/uninstall-collector-systemd.sh
```

## 8. 화면 읽는 법

화면은 상단 장비 목록(Devices), 왼쪽 작업 영역(탭 2개), 오른쪽 탐색 영역
(탭 4개)으로 구성됩니다.

### Devices (상단)

연결된 장비 목록입니다. 각 장비는 별명/hostname, hardware label,
metric/event 수, 마지막 수집 시각, 상태 전이(예: `이전 ➔ 현재`)와 핵심
지표 요약(예: `발열(정상); 메모리(위험 ➔ 정상)`)을 표시합니다.

- 장비명은 별명이 있으면 `별명 · hostname`으로 표시됩니다.
- 연결이 `Stale`이면 지표 요약 대신 `Telemetry Offline` 메시지가 표시됩니다.
- healthy 장비도 클릭할 수 있습니다. 활성 이슈가 없어도 상세 텔레메트리를
  볼 수 있습니다.
- 상단 `Project info` chip에 Made by, About, Version 정보가 들어 있습니다.

장비를 선택하면 해당 장비의 첫 번째 활성 이슈가 자동으로 선택됩니다.

### 왼쪽: 🚨 예방 가이드 (Smart Advisor)

- **Device Issues**: 선택한 장비에만 해당하는 활성 조사 이슈입니다. 비어
  있으면 `No active investigations for this device.`로 표시됩니다.
- **Smart Advisor 알림**: 실시간 텔레메트리에서 생성한 카드(메모리, 발열,
  그래픽, 정상)입니다. 카드마다 확인 체크리스트가 있고, 체크 상태는 브라우저
  안에서만 유지됩니다.

### 왼쪽: 🛠️ 조치 및 협업 (Actions)

- **Intervention Guide**: 조치 기록 방법 안내.
- **Action plan**: 조치 이름과 설명을 기록하는 폼입니다. 기록하면 서버가
  조치 전후 telemetry 창(약 5분)을 비교해 `helped / worse / unclear /
insufficient_data` 판정을 돌려줍니다.
- **Recorded interventions**: 기록된 조치 목록.
- **Team Handoff**: 팀 인계 메모 작성/조회.

### 오른쪽: 실시간 지표 (Vitals)

- **Metric Ledger**: 핵심 지표의 상세 행입니다.
  - **CPU Package**: CPU package 온도와 core별 온도.
  - **Load Average**: Linux 1분, 5분, 15분 load average.
  - **NVMe SSD**: 대표 NVMe 온도와 장치별 온도, namespace 용량, 샘플 간
    읽기/쓰기 처리량.
  - **Wi-Fi Signal**: 대표 Wi-Fi 신호와 인터페이스별 신호, Rx/Tx 링크 bitrate.
  - 각 행의 `?` 버튼은 정의, 시간창, 해석 기준, 다음 확인 항목을 설명합니다.
  - Windows 장비는 Windows collector가 실제 보낸 metric(`CPU Core Load`,
    `CPU Cores` 등)을 우선 표시하고, 없는 Linux 전용 행을 억지로 채우지
    않습니다.
- **Telemetry Matrix**: CPU profile, memory, disk, NVMe health/capacity/I/O,
  fan, thermal, battery, Wi-Fi link, network, kernel, agent freshness 등
  범주별 관측 상태입니다. `N/전체 observed`는 위험 점수가 아니라 전체 범주 중
  관측값이 들어온 범주 수입니다.

### 오른쪽: 진단 및 가설 (Diagnosis)

- **Top hypotheses**: 규칙 기반 원인 후보.
- **Verification**: intervention 전후 비교 결과.
- **Report**: 인계용 결론 초안과 권장 다음 행동.

### 오른쪽: 이벤트 로그 (Timeline)

수집된 이벤트의 증거 타임라인입니다. 이벤트 출처(kern.log, journalctl,
Windows Event Log 등)와 분류(thermal, storage, power, graphics, memory,
network, reboot, update)를 함께 표시합니다.

### 오른쪽: 수집기 상태 (Operations)

- **Operations Rail**: stale 장비 등 수집 운영 카드.
- **Pattern Explorer**: category, component, model, kernel 기준 반복 신호.

### 조사 워크플로

각 이슈는 DTIHAVR 단계로 진행됩니다.

```text
Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report
```

### CPU core 표시

Quipu는 Linux hwmon/coretemp가 노출한 core id만 표시합니다. 없는 번호를
임의로 채우지 않습니다.

Intel Core Ultra 5 125H처럼 토폴로지가 확인되는 경우:

- `P`: Performance core
- `E`: Efficient core
- `LP-E`: Low Power Efficient core

공식 Intel Core Ultra 5 125H 스펙은 14 cores / 18 threads, 4 P-cores,
8 E-cores, 2 LP E-cores입니다. Quipu는 이 머신에서 확인된 sensor id 패턴일
때만 그룹을 붙입니다. 다른 CPU에서는 그룹을 추정하지 않습니다.

Windows에서도 hardware monitor가 core를 `Core #1`처럼 일반 이름으로만 보내면
`cpu.core_1.*`로 표시하고, `P-Core #1`/`E-Core #2`처럼 구분해 보내는 경우에만
`P`/`E` 그룹으로 묶습니다.

터미널에서 원본 센서 값을 보려면:

```bash
sensors | grep -E 'Package|Core'
```

### Load average

Load는 CPU 사용률 퍼센트가 아닙니다. 실행 중이거나 실행 대기 중인 작업 수의
평균입니다.

원본:

```bash
cat /proc/loadavg
uptime
```

앞 세 값이 각각 1분, 5분, 15분 load average입니다.

### CPU/Wi-Fi/NVMe 상세 정보

- **CPU Profile**: CPU 모델명, core/thread 수, 확인 가능한 경우 P/E/LP-E
  토폴로지를 표시합니다. Intel Core Ultra 5 125H는 4 P-cores, 8 E-cores,
  2 LP E-cores, 18 threads로 표시합니다.
- **Wi-Fi Link**: `iw dev <interface> link`의 Rx/Tx bitrate입니다. `iw`가
  없으면 `iwconfig`의 단일 Bit Rate를 fallback으로 표시합니다. 인터넷 다운로드
  속도 측정값이 아니라 AP와의 무선 링크 속도입니다.
- **NVMe Capacity**: `/sys/class/block/nvme*n*/size`에서 읽은 namespace
  용량입니다.
- **NVMe I/O**: 같은 장비의 이전 collector 샘플과 현재 샘플의 sector counter
  차이로 계산한 읽기/쓰기 bytes/sec입니다. 첫 샘플에는 `Needs 2 samples`처럼
  보일 수 있습니다.

## 9. 장치별 token

개발용 `dev-token` 대신 장치별 token을 만들 수 있습니다. 서버의 개발 token은
`QUIPU_DEV_AGENT_TOKEN` 환경 변수로 바꿀 수 있습니다.

```bash
curl -sS -X POST http://127.0.0.1:8000/api/enrollment/tokens \
  -H "Content-Type: application/json" \
  -H "X-Quipu-Agent-Token: dev-token" \
  -d '{"device_id":"local-computer","label":"Local notebook collector"}'
```

반환된 `token`을 collector의 `--token` 또는 `/etc/quipu/collector.env`에 넣습니다.
token은 서버에 SHA-256 hash로만 저장되고, `GET /api/enrollment/tokens`로 목록을,
`POST /api/enrollment/tokens/{id}/rotate`와 `.../revoke`로 회전/폐기를 할 수
있습니다 (모두 dev token 필요).

## 10. 자주 보는 문제

### 화면이 비어 있음

API 서버가 떠 있는지 확인합니다.

```bash
curl http://127.0.0.1:8000/api/health
```

서버가 떠 있고 장비 목록이 비어 있다면 아직 collector가 batch를 보내지
않았거나 시딩을 하지 않은 상태입니다 (3장 참고).

웹 UI가 API를 찾는 기본 주소는 `http://127.0.0.1:8000`입니다. 다른 노트북에서 UI를
열려면 Vite 또는 배포된 웹 서버도 `0.0.0.0`에 바인딩하고, 웹 빌드가 접근 가능한
API 주소를 보도록 설정해야 합니다. 개발 서버에서는 예를 들어 다음처럼 실행합니다.

```bash
cd /home/chquan/Quipu/apps/web
VITE_API_BASE_URL=http://<server-ip>:8000 npm run dev -- --host 0.0.0.0 --port 5174
```

서버는 `http://<server-ip>:5173` 또는 `http://<server-ip>:5174` 같은 private LAN
UI origin을 허용합니다.

### 샘플 장비가 계속 보임

시딩한 샘플 DB가 남아 있습니다.

```bash
rm -f data/quipu.sqlite3 data/quipu.sqlite3-wal data/quipu.sqlite3-shm
```

그 뒤 API 서버를 다시 시작하고 collector를 한 번 전송합니다.

### 다른 노트북이 안 보임

다른 노트북에서 서버에 접근 가능한지 먼저 확인합니다.

```bash
curl http://<server-ip>:8000/api/health
```

접근이 안 되면 서버가 `0.0.0.0`에 바인딩되어 있는지, 방화벽이 TCP `8000`을
허용하는지 확인합니다. 접근은 되는데 화면에 안 보이면 collector의
`--device-id`, `--token`, `--server-url`을 확인합니다.

Windows 장비가 보이지만 metric이 거의 없으면 Windows collector가 아직 이전 버전의
최소 smoke metric만 보내고 있을 수 있습니다. `/api/fleet/overview`의
`latest_metrics` 키 목록을 확인해 collector 배포가 의도한 신호를 모두 보내는지
점검합니다.

`v0.13.1` 이상 collector는 Windows에서 다음 호환성 보강을 포함합니다.

- PowerShell/CIM 명령을 더 오래 기다려 cold start timeout으로 metric이 빠지는
  일을 줄입니다.
- 한국어 Windows의 `netsh wlan show interfaces` 출력처럼 key 이름이 현지화된
  경우에도 signal `%`와 `(Mbps)` rate 값을 읽습니다.
- `Win32_DiskDrive`가 NVMe를 `SCSI`처럼 보고해도 `Get-PhysicalDisk`의
  `BusType = NVMe`를 fallback으로 사용합니다.
- `v0.13.2` 이상은 Intel Core i5-1340P를 `P 4 / E 8 / 16 threads` topology로
  표시하고, Wi-Fi signal은 `netsh` 직접 실행, full path, PowerShell 경유,
  WMI RSSI fallback을 차례대로 시도합니다.
- Windows 온도는 ACPI thermal zone 외에 LibreHardwareMonitor 또는
  OpenHardwareMonitor가 WMI sensor를 노출하면 CPU package/core와 NVMe/SSD 온도를
  읽습니다.
- `v0.13.3` 이상은 NVMe 온도에 `Get-StorageReliabilityCounter` fallback을 추가하고,
  LibreHardwareMonitor/OpenHardwareMonitor fan sensor가 있으면 팬 RPM을 읽으며,
  Windows Event Log의 최근 System/Application 이벤트를 조사 이벤트로 분류합니다.
- `v0.13.4` 이상은 Windows performance counter와 `Get-PhysicalDisk`를 매핑해
  NVMe R/W bytes/sec를 읽고, native WMI의 `Win32_TemperatureProbe`,
  `Win32_Fan`, `Win32_Tachometer`도 추가 fallback으로 시도합니다.
- `v0.14.0` 이상은 Windows/Linux 공통 `smartctl --json` fallback으로 NVMe
  SMART pass/fail, spare, 수명, media error, 가동시간과 비정상 종료를 장치별로
  읽습니다. Windows에서는 공식 LibreHardwareMonitor library도 직접 읽으며,
  CPU/팬처럼 관리자 접근이 필요한 센서는 `-Highest` task에서만 값이 나올 수 있습니다.
- `v0.14.1` 이상은 Windows Thermal Zone performance counter를 추가로 읽어
  관리자 권한 없이도 firmware가 공개한 시스템 thermal zone 온도를 보냅니다.
- `v0.14.2` 이상은 LibreHardwareMonitor/OpenHardwareMonitor가 노출하는 Windows
  CPU P-core/E-core/LP-E core 온도와 core별 load percent를 읽고, UI에서 Linux
  load average와 구분해 표시합니다.
- `v0.14.3` 이상은 LibreHardwareMonitor GUI가 이미 실행 중이어도 direct DLL
  probe를 건너뛰지 않습니다. WMI provider가 꺼져 있어도 설치 폴더에서
  `LibreHardwareMonitorLib.dll`을 찾을 수 있으면 core 온도/load를 읽습니다.
- `v0.14.5` 이상 문서는 Windows CPU load와 core 온도를 분리해 설명합니다. 현재
  `cpu.core_<n>.load_percent`가 들어와도 `cpu.*.temp_c`가 없으면 core 온도는
  표시되지 않습니다.

그래도 Wi-Fi/NVMe/thermal 값이 비어 있으면 Windows 장비에서
`apps\collector\logs\quipu-collector.err.log`와
`apps\collector\logs\quipu-collector-startup.log`를 확인합니다. ACPI thermal zone은
Windows/firmware가 노출하지 않고 hardware monitor WMI provider도 없으면 비어 있을
수 있습니다. 팬 RPM도 Windows 기본 CIM만으로는 보통 나오지 않으며, 해당 hardware
monitor WMI provider가 센서를 노출해야 표시됩니다.

### 별명을 바꾸고 싶음

같은 `--device-id`로 collector를 다시 보내면서 `--device-alias`만 바꾸면 됩니다.
systemd timer를 쓰면 `/etc/quipu/collector.env`의
`QUIPU_COLLECTOR_DEVICE_ALIAS`를 바꾼 뒤 다음 실행을 기다리거나 service를 한 번
수동 실행합니다.

### core 번호가 띄엄띄엄임

정상일 수 있습니다. Linux가 노출한 sensor/core id가 연속 번호가 아닐 수
있습니다. Quipu는 없는 번호를 만들어 표시하지 않습니다.

Windows에서도 LibreHardwareMonitor가 `Core #1`처럼 일반 이름으로만 sensor를
보내면 `cpu.core_1.*` 형태로 표시합니다. `P-Core #1`, `E-Core #2`,
`LP E-Core #1`처럼 provider가 구분해 보내는 경우에만 UI가 `P`, `E`, `LP-E`
그룹으로 묶습니다.

### Windows core load는 보이는데 core 온도가 안 보임

서버에서 먼저 최신 metric key를 확인합니다.

```bash
curl -s http://127.0.0.1:8000/api/fleet/overview | python3 -c '
import json, sys
payload = json.load(sys.stdin)
for snap in payload["devices"]:
    if snap["device"]["device_id"] == "windows":
        keys = sorted(snap["latest_metrics"].keys())
        print("CPU keys:")
        print("\n".join(key for key in keys if key.startswith("cpu.")))
        print("Thermal keys:")
        print("\n".join(key for key in keys if key.startswith("thermal.")))
'
```

`cpu.core_<n>.load_percent`는 있는데 `cpu.*.temp_c`가 없고
`thermal.windows_zone_*`만 있으면 Windows가 CPU load는 노출했지만 CPU core 온도는
collector에 노출하지 않은 것입니다. 이때는 Windows 장비에서 관리자 PowerShell로
LibreHardwareMonitor `Temperature` sensor와 scheduled task `RunLevel`을 확인합니다
(5장의 진단 절차 참고).

### NVMe Health가 Unavailable

Linux에는 `smartmontools`를 설치하고 collector systemd service를 root로 실행합니다.
Windows에는 관리자 PowerShell에서 설치 스크립트를 `-InstallSensorTools -Highest`로
실행합니다. 그래도 값이 없으면 저장장치 또는 드라이버가 SMART log를 공개하지 않는
경우입니다.

### fan이 0 rpm 또는 N/A

노트북 firmware/EC나 hwmon 드라이버가 fan 값을 공개하지 않거나, 팬이 멈춰 있는
상태일 수 있습니다. Linux에서는 `sensors`, Windows에서는 관리자 권한의
LibreHardwareMonitor에서 RPM sensor가 실제로 보이는지 함께 확인합니다.

## 11. 안전 원칙

- collector는 시스템 신호를 읽기 전용으로 수집합니다. NVMe R/W 계산을 위해
  collector state directory에 이전 counter를 저장할 수 있습니다.
- 원격 명령 실행은 없습니다.
- 자동 수리는 없습니다.
- raw log 전체를 장기 저장하는 제품이 아닙니다.
- 운영 배포, package publishing, RBAC는 향후 hardening 항목입니다.
