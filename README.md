# Quipu

<p align="center">
  <img alt="CI" src="https://github.com/chquandogong/Quipu/actions/workflows/ci.yml/badge.svg">
  <img alt="Version" src="https://img.shields.io/badge/version-v0.14.4-2f6f7e">
  <img alt="Status" src="https://img.shields.io/badge/status-local--first%20workstation%20health-5b6b73">
  <img alt="License" src="https://img.shields.io/badge/license-not%20selected-lightgrey">
</p>

<p align="center">
  <strong>워크스테이션 건강 조사 도구</strong><br>
  Quipu는 지표 대시보드가 아니라, 여러 노트북/컴퓨터의 문제를 발견하고 근거로 조사하고 조치 결과를 남기는 로컬 우선 운영 도구입니다.
</p>

<p align="center">
  한국어 | <a href="README.en.md">English</a> | <a href="README.zh-CN.md">简体中文</a>
</p>

---

## 무엇인가

Quipu는 노트북과 개발 워크스테이션에서 발생하는 발열, 그래픽 오류,
Wi-Fi 불안정, 저장장치 경고, 전원 문제, 재부팅 흔적을 한 화면에 모읍니다.
저장소에 포함된 collector는 읽기 전용 collector입니다. Linux에서는 sysfs와
procfs를 읽고, Windows에서는 PowerShell/CIM/netsh/Get-NetAdapter가 노출하는
신호를 best-effort로 읽습니다. 다른 운영체제 collector도 같은 ingest API 계약으로
관측값을 보내면 같은 화면에 표시됩니다.
첫 질문은 “CPU가 몇 도인가?”가 아니라 “지금 무엇을 조사해야 하며, 근거는
무엇인가?”입니다.

기본 조사 흐름은 다음 순서입니다.

```text
Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report
```

## v0.14.4 핵심

- 문서를 현재 구현 기준으로 다시 정리했습니다. README, 사용자 매뉴얼, ship
  checklist, dashboard, roadmap은 Windows collector가 실제로 보내는 값과
  표시되지 않는 값의 이유를 같은 용어로 설명합니다.
- Windows `윈도우 · DOGU_CHQUAN` 검증에서 CPU load는
  `cpu.load_percent`, `cpu.core_<n>.load_percent`로 들어오는 것을 확인했습니다.
  화면에서는 `CPU Core Load`로 표시됩니다.
- 같은 장비에서 LibreHardwareMonitor `Temperature` sensor가 노출된 뒤
  `cpu.package_temp_c`, `cpu.p_core_1..4.temp_c`, `cpu.e_core_1..8.temp_c`도
  수신되는 것을 확인했습니다.
- Windows CPU core 온도는 collector가 `cpu.*.temp_c` metric을 받은 경우에만
  보입니다. `thermal.windows_zone_*.temp_c`는 ACPI thermal zone이며 CPU core
  온도로 변환하지 않습니다.
- Windows에서 core load는 보이지만 core 온도가 안 보이면 UI 문제가 아니라
  LibreHardwareMonitor/OpenHardwareMonitor `Temperature` sensor가 scheduled task
  권한에서 노출되지 않은 상태일 수 있습니다. 관리자 PowerShell에서
  `Get-CimInstance -Namespace root/LibreHardwareMonitor -ClassName Sensor`와
  collector `--dry-run`으로 먼저 확인합니다.
- Windows에서 LibreHardwareMonitor GUI가 이미 실행 중이어도 collector가 direct
  DLL probe를 건너뛰지 않고, 실행 중인 프로세스/Program Files/WinGet 경로에서
  `LibreHardwareMonitorLib.dll`을 찾아 CPU core 온도와 load를 읽습니다.
- Windows LibreHardwareMonitor/OpenHardwareMonitor가 노출하는 CPU
  P-core/E-core/LP-E core 온도와 core별 load percent를 수집하고, 화면에서는
  `CPU Cores`와 `CPU Core Load`로 Windows 방식에 맞게 표시합니다.
- Windows 화면은 실제로 들어온 Windows metric을 우선 표시합니다. Linux 전용
  load average나 CPU package 값이 없을 때 억지로 표시하지 않습니다.
- 깨진 문자로 들어오는 Windows Event Log 설명은 UI에서 숨기고, category/source
  중심의 읽을 수 있는 문구로 대체합니다.
- Windows와 Linux에서 `smartctl --json`을 자동 탐지해 NVMe별 온도, SMART
  통과 여부, critical warning, available spare, 수명 사용률, media error,
  power-on hours, unsafe shutdown, error-log count를 수집합니다.
- Windows Thermal Zone performance counter를 읽어 관리자 권한 없이도 firmware가
  공개한 시스템 thermal zone 온도를 수집합니다.
- Windows에서는 공식 LibreHardwareMonitor 라이브러리를 직접 읽어 CPU
  package/core, SSD/NVMe 온도와 노출 가능한 팬 RPM을 수집합니다.
- Linux hwmon 팬은 첫 번째 팬뿐 아니라 읽을 수 있는 모든 팬을
  `fan.<sensor>.rpm`으로 보냅니다.
- Windows 설치 스크립트의 `-InstallSensorTools`와 `-Highest` 옵션으로 공식
  sensor 도구 설치와 관리자 sensor 접근을 구성할 수 있습니다.

- Windows NVMe R/W 속도는 `Win32_PerfFormattedData_PerfDisk_PhysicalDisk`와
  `Get-PhysicalDisk`를 매핑해 `nvme.read_bytes_per_sec`,
  `nvme.write_bytes_per_sec`, 장치별 R/W metric으로 보냅니다.
- Windows native WMI fallback으로 `Win32_TemperatureProbe`,
  `Win32_Fan`, `Win32_Tachometer`를 추가로 읽습니다.
- Windows NVMe 온도는 `Get-PhysicalDisk | Get-StorageReliabilityCounter`
  경로를 추가로 사용해 `nvme.temp_c`와 `nvme.<device>.temp_c`로 보냅니다.
- Windows 팬 RPM은 LibreHardwareMonitor/OpenHardwareMonitor WMI fan sensor가
  노출되면 `fan.rpm`과 `fan.<sensor>.rpm`으로 보냅니다.
- Windows Event Log의 최근 System/Application 이벤트를 읽어 storage, network,
  graphics, thermal, memory, power, reboot, update 조사 이벤트로 분류합니다.
- Windows의 Intel Core i5-1340P를 `P 4 / E 8 / 16 threads` topology로 표시합니다.
- Windows Wi-Fi는 `netsh` 직접 실행, system path, PowerShell 경유, WMI RSSI
  fallback을 순서대로 시도해 signal/link 정보를 더 많이 수집합니다.
- Windows 온도는 ACPI thermal zone 외에 LibreHardwareMonitor/OpenHardwareMonitor
  WMI sensor가 있으면 CPU package/core, NVMe/SSD 온도를 같은 metric 이름으로
  보냅니다.
- Windows collector가 PowerShell/CIM 호출을 더 오래 기다리고, 한국어 `netsh`
  출력과 `Get-PhysicalDisk` NVMe 판별을 처리해 Wi-Fi/NVMe/장비 model 누락을
  줄였습니다.
- 좌측 화면을 `Devices` 중심으로 재구성했습니다. healthy 장비도 선택하면 상세
  Telemetry Matrix, Metric Ledger, Report가 표시됩니다.
- 선택한 장비의 활성 이슈만 `Device Issues`에 표시합니다. 이슈가 없으면
  `No active investigations for this device.`로 표시합니다.
- Fleet Brief의 `Queue cases` 표현을 `Open issues`로 바꿔 장비 수와 조사 이슈
  수를 분리했습니다.
- 같은 `device-id`의 다음 batch가 `display_name`이나 `cpu_model`을 생략해도
  기존 별명과 CPU 모델을 보존합니다.
- Windows scheduled-task collector packaging과 best-effort telemetry 수집을
  연결했습니다. Windows에서도 환경 파일, 숨김 실행 wrapper, 중복 실행 방지,
  offline buffer, 5분 반복 수집 흐름을 사용할 수 있습니다.
- Windows collector가 CIM/netsh/Get-NetAdapter에서 가능한 경우 CPU core/thread,
  memory, battery, Wi-Fi, NVMe capacity, thermal zone 정보를 같은 metric 이름으로
  보냅니다. 현재 Windows 장비에 값이 비어 있으면 먼저 최신 collector가 배포되어
  실행 중인지 확인합니다.
- Windows install/uninstall PowerShell 스크립트를 추가했습니다.
- 다른 노트북/컴퓨터를 같은 서버에 연결하는 collector 절차를 문서화했습니다.
- collector `--device-alias`와 systemd `QUIPU_COLLECTOR_DEVICE_ALIAS`로 장비별
  별명을 보낼 수 있습니다.
- 화면은 별명이 있으면 `별명 · hostname`으로 표시하고, 없으면 기존 hostname만
  표시합니다.
- `Made by`, `About`, `Version`은 상단 `Project info` hover/focus chip 하나로
  통합했습니다.
- status, metric, coverage, operations, telemetry 설명을 같은 hover/focus
  popover 패턴으로 정리했습니다.
- collector가 CPU 모델/코어 수/스레드 수, Intel Core Ultra 5 125H의
  `P/E/LP-E` 토폴로지, Wi-Fi 링크 속도, NVMe 용량, NVMe 읽기/쓰기 처리량을
  수집합니다.
- Telemetry Matrix와 Metric Ledger가 NVMe/Wi-Fi 상세값을 장치/인터페이스별로
  같은 chip 패턴으로 표시합니다.
- LAN에서 `http://<server-ip>:5173` 또는 `:5174`로 연 UI가 API를 읽을 수 있도록
  private-address CORS 설정을 추가했습니다.
- v0.10.0의 Metric Ledger 개선도 유지합니다. Load average는 `1m / 5m / 15m`
  창으로 표시하고, CPU core/NVMe/Wi-Fi는 실제 관측된 개별 값만 보여줍니다.

## v0.10.0에서 유지되는 핵심

- 기본 문서를 처음부터 정리하고 [사용자 매뉴얼](USER_MANUAL.md)을 추가했습니다.
- Metric Ledger가 Load average를 `1m / 5m / 15m` 창으로 명확히 표시합니다.
- CPU package 행은 core 센서 값을 숫자 chip으로 표시합니다. 없는 core 번호를
  임의로 채우지 않습니다.
- Intel Core Ultra 5 125H처럼 확인 가능한 토폴로지에서는 core chip을
  `P`, `E`, `LP-E` 그룹으로 묶어 표시합니다.
- NVMe와 Wi-Fi는 장치나 인터페이스가 하나뿐이어도 개별 chip으로 표시하고,
  여러 개면 각각의 값을 나열합니다.
- 로컬 DB를 비우고 현재 노트북 collector 데이터만 넣는 운영 절차를 문서화했습니다.

## 화면 구성

- **Command Center**: 선택된 조사 항목, 위험도, 우선순위, 다음 행동.
- **Problem Guide**: 무엇이 문제인지, 먼저 볼 근거, 다음에 할 일.
- **Telemetry Brief**: CPU, Load, NVMe, Wi-Fi 대표값.
- **Metric Ledger**: 핵심 지표의 상세값과 설명 tooltip.
- **Telemetry Matrix**: CPU Profile, Memory, Fan, NVMe Health/Capacity/I/O,
  Disk, Battery, Wi-Fi Link, Network, Thermal, Kernel, Agent freshness 범주별
  관측 상태.
- **Devices**: 연결된 장비 목록. 별명, hostname, hardware label, metric/event 수,
  마지막 수집 시각, 활성 이슈 요약, risk를 함께 표시합니다.
- **Device Issues**: 선택한 장비에만 해당하는 활성 조사 이슈입니다. healthy 장비는
  이 영역이 비어 있어도 상세 텔레메트리를 볼 수 있습니다.
- **Evidence / Hypotheses / Action / Verification / Report**: 근거, 가설,
  조치, 전후 검증, 인계용 결론.
- **Pattern Explorer**: category, component, model, kernel 기준 반복 신호.

## 빠른 시작: 샘플 데이터

샘플 fleet로 서버를 실행합니다.

```bash
scripts/dev-server.sh
```

다른 터미널에서 웹 UI를 실행합니다.

```bash
cd apps/web
npm install
npm run dev
```

브라우저에서 엽니다.

```text
http://127.0.0.1:5173
```

## 빠른 시작: 이 노트북만 보기

샘플 DB를 지우고 빈 DB로 API를 실행합니다.

```bash
rm -f data/quipu.sqlite3 data/quipu.sqlite3-wal data/quipu.sqlite3-shm
cd apps/server
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
QUIPU_DATABASE_PATH=../../data/quipu.sqlite3 uvicorn quipu_server.app:app --host 127.0.0.1 --port 8000 --reload
```

다른 터미널에서 collector를 한 번 실행합니다.

```bash
sudo apt-get install smartmontools
cd apps/collector
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
quipu-collector \
  --server-url http://127.0.0.1:8000 \
  --token dev-token \
  --device-id local-computer \
  --device-alias "내 노트북"
```

웹 UI를 새로고침하면 현재 노트북만 표시됩니다.

## 다른 노트북/컴퓨터 연결

Quipu 서버가 떠 있는 컴퓨터에서 LAN 주소로 API를 엽니다.

```bash
cd apps/server
. .venv/bin/activate
QUIPU_DATABASE_PATH=../../data/quipu.sqlite3 uvicorn quipu_server.app:app --host 0.0.0.0 --port 8000
```

다른 Linux 노트북에서 포함된 collector를 설치하고 같은 서버로 전송합니다.

```bash
cd apps/collector
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
quipu-collector \
  --server-url http://<server-ip>:8000 \
  --token dev-token \
  --device-id office-gram \
  --device-alias "사무실 그램"
```

여러 대를 연결할 때는 `--device-id`를 장비마다 다르게 유지합니다. 운영 반복
수집에서는 `dev-token` 대신 장치별 enrollment token을 쓰는 것을 권장합니다.

Windows에서는 같은 collector 패키지를 PowerShell scheduled-task wrapper로
실행할 수 있습니다. 처음 설치하거나 최신 릴리스로 갱신한 뒤에는 Windows 장비에서
가상환경을 다시 설치하고 scheduled task를 재등록하거나 재시작합니다.

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

같은 ingest API로 `device_id`, `display_name` 또는 별명, `hostname`, `metrics`,
`events`를 보내는 외부 collector도 UI의 `Devices` 목록에 함께 표시됩니다.
Windows 장비에서 Linux load average가 없거나 NVMe/Wi-Fi 세부값이 일부만 보이는
것은 collector가 아직 해당 metric을 보내지 않았다는 뜻일 수 있습니다.
마찬가지로 `CPU Core Load`가 보이더라도 `CPU Cores` 온도가 안 보이면 Windows
collector가 load sensor는 읽었지만 temperature sensor는 받지 못한 상태입니다.

## Collector가 읽는 신호

저장소의 Linux collector는 시스템 신호를 읽기 전용으로 수집합니다. 원격 명령
실행이나 자동 수리는 하지 않습니다. NVMe R/W 처리량 계산을 위해 collector state
directory에 이전 sector counter를 저장할 수 있습니다. Windows collector도 같은
원칙으로 읽기 전용 관측값만 보내는 구현을 권장합니다.

- `cpu.load_1m`, `cpu.load_5m`, `cpu.load_15m`: `/proc/loadavg`의 1/5/15분 load average.
- `cpu.physical_cores`, `cpu.logical_threads`, `cpu.performance_cores`,
  `cpu.efficient_cores`, `cpu.low_power_efficient_cores`: CPU 모델과
  `/proc/cpuinfo`에서 확인한 코어/스레드 정보. Intel Core Ultra 5 125H는
  4P/8E/2LP-E/18 threads로 표시합니다.
- `cpu.package_temp_c`, `cpu.core_<n>.temp_c`: hwmon/coretemp 기반 CPU 온도.
- `cpu.load_percent`, `cpu.core_<n>.load_percent`,
  `cpu.p_core_<n>.load_percent`, `cpu.e_core_<n>.load_percent`: Windows
  hardware monitor가 노출한 CPU 사용률 percent. Linux load average와 다른 값입니다.
- `thermal.*.temp_c`: sysfs thermal zone 온도.
- `nvme.temp_c`, `nvme.<device>.temp_c`: NVMe 대표/장치별 온도.
- `nvme.smart_passed`, `nvme.critical_warning`,
  `nvme.available_spare_percent`, `nvme.percentage_used_percent`,
  `nvme.media_errors`: `smartctl --json` 또는 OS reliability counter 기반
  NVMe SMART health. 같은 값은 `nvme.<device>.*` 장치별 metric으로도 보냅니다.
- `nvme.capacity_bytes`, `nvme.<device>.capacity_bytes`: NVMe namespace 용량.
- `nvme.read_bytes_per_sec`, `nvme.write_bytes_per_sec`,
  `nvme.<device>.read_bytes_per_sec`, `nvme.<device>.write_bytes_per_sec`:
  collector 샘플 간 sector counter 차이로 계산한 현재 읽기/쓰기 처리량.
  첫 샘플에는 비교 기준이 없어 표시되지 않을 수 있습니다.
- `wifi.signal_dbm`, `wifi.<interface>.signal_dbm`: `/proc/net/wireless` 신호 세기.
- `wifi.rx_bitrate_mbps`, `wifi.tx_bitrate_mbps`,
  `wifi.<interface>.rx_bitrate_mbps`, `wifi.<interface>.tx_bitrate_mbps`:
  `iw dev <interface> link`의 무선 링크 속도. 인터넷 속도 측정값이 아니라
  AP와의 link bitrate입니다.
- `wifi.link_bitrate_mbps`, `wifi.<interface>.link_bitrate_mbps`: `iw`가 없을
  때 `iwconfig`의 단일 Bit Rate를 fallback으로 저장합니다.
- `memory.used_percent`, `disk.root_used_percent`, `battery.capacity_percent`,
  `battery.ac_online`, `fan.rpm`.
- kernel thermal/storage/power/graphics/memory warning, update marker, reboot marker,
  NetworkManager reconnect summary.

CPU core 번호는 Linux가 노출한 sensor/core id를 그대로 따릅니다. 예를 들어
Intel Core Ultra 5 125H에서는 `0-7`, `8`, `12`, `16`, `20`, `32`, `33`처럼
띄엄띄엄 보일 수 있습니다. Quipu는 없는 번호를 만들어 표시하지 않습니다.
Windows에서도 hardware monitor가 core를 `Core #1`처럼 일반 이름으로만 보내면
`cpu.core_1.*`로 표시하고, `P-Core #1`/`E-Core #2`처럼 구분해 보내는 경우에만
`P`/`E` 그룹으로 묶습니다.

## 운영 설치

collector는 한 번 실행하거나 systemd timer로 5분마다 실행할 수 있습니다.
자세한 절차는 [사용자 매뉴얼](USER_MANUAL.md)을 보세요.

주요 명령:

```bash
cd apps/collector
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
quipu-collector --dry-run
```

systemd 설치 미리보기:

```bash
scripts/install-collector-systemd.sh --dry-run
```

## 아키텍처

```text
Linux collector / compatible Windows collector
      |
      v
FastAPI ingest API
      |
      v
SQLite WAL store
      |
      v
Rule-based analysis engine
      |
      v
React investigation UI
```

## 검증

서버:

```bash
cd apps/server
. .venv/bin/activate
pytest -v
```

컬렉터:

```bash
cd apps/collector
. .venv/bin/activate
pytest -v
```

웹:

```bash
cd apps/web
npm test
npm run build
```

## 저장소 구조

```text
apps/
  collector/     Read-only Linux collector; compatible external collectors can use the same ingest API
  server/        FastAPI API, SQLite persistence, rule-based analysis
  web/           Vite React UI
docs/
  superpowers/   Product decisions, plans, release notes, roadmap
fixtures/
  ingest/        Deterministic sample batches
scripts/
  dev-server.sh  Seeded local API server
```

## 문서

- [사용자 매뉴얼](USER_MANUAL.md)
- [Changelog](CHANGELOG.md)
- [Project dashboard](docs/superpowers/DASHBOARD.md)
- [Ship checklist](docs/superpowers/SHIP_CHECKLIST.md)
- [Roadmap](docs/superpowers/ROADMAP.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## 안전 경계

현재 릴리스에 포함하지 않습니다.

- 원격 수리 명령 실행
- production deployment
- package publishing
- AI 단독 결론
- raw log warehouse

Quipu의 기본값은 로컬 우선, 읽기 전용, 근거 기반입니다.
