# Quipu

<p align="center">
  <img alt="CI" src="https://github.com/chquandogong/Quipu/actions/workflows/ci.yml/badge.svg">
  <img alt="Release" src="https://img.shields.io/github/v/release/chquandogong/Quipu?color=2f6f7e&label=release">
  <img alt="Status" src="https://img.shields.io/badge/status-local--first%20workstation%20health-5b6b73">
  <img alt="License" src="https://img.shields.io/github/license/chquandogong/Quipu?color=blue">
</p>

<p align="center">
  <strong>워크스테이션 건강 조사 도구</strong><br>
  Quipu는 지표 대시보드가 아니라, 여러 노트북/컴퓨터의 문제를 발견하고 근거로 조사하고 조치 결과를 남기는 로컬 우선 운영 도구입니다.
</p>

<p align="center">
  한국어 | <a href="README.en.md">English</a> | <a href="README.zh-CN.md">简体中文</a>
</p>

---

<p align="center">
  <img alt="Quipu 조사 대시보드 — 장비 목록, Smart Advisor, 실시간 지표" src="docs/images/dashboard.png" width="920">
</p>

## 무엇인가

Quipu는 노트북과 개발 워크스테이션에서 발생하는 발열, 그래픽 오류,
Wi-Fi 불안정, 저장장치 경고, 전원 문제, 재부팅 흔적을 한 화면에 모읍니다.
저장소에 포함된 collector는 읽기 전용입니다. Linux에서는 sysfs와 procfs를
읽고, Windows에서는 PowerShell/CIM/netsh/LibreHardwareMonitor가 노출하는
신호를 best-effort로 읽습니다. 다른 운영체제 collector도 같은 ingest API
계약으로 관측값을 보내면 같은 화면에 표시됩니다.

첫 질문은 "CPU가 몇 도인가?"가 아니라 "지금 무엇을 조사해야 하며, 근거는
무엇인가?"입니다. 기본 조사 흐름은 다음 순서입니다.

```text
Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report
```

구성 요소는 세 개입니다.

- `apps/server`: FastAPI ingest/조회 API + SQLite(WAL) 저장 + 규칙 기반 분석.
- `apps/collector`: 읽기 전용 신호 수집 CLI(`quipu-collector`). Linux/Windows 지원.
- `apps/web`: Vite + React 조사 UI.

최근 변경 내역은 [CHANGELOG](CHANGELOG.md)를 보세요.

## 화면 구성

상단에는 연결된 장비 목록(**Devices**)이 있습니다. 각 장비는 별명/hostname,
hardware label, metric/event 수, 마지막 수집 시각, 상태 전이(예: `이전 ➔ 현재`)를
표시합니다. healthy 장비도 선택하면 상세 텔레메트리를 볼 수 있습니다.

왼쪽 작업 영역은 두 개의 탭입니다.

- **🚨 예방 가이드 (Smart Advisor)**: 선택한 장비의 활성 조사 이슈(Device
  Issues)와, 실시간 텔레메트리에서 생성한 Smart Advisor 알림 카드(메모리,
  발열, 그래픽 등)와 체크리스트.
- **🛠️ 조치 및 협업 (Actions)**: Intervention Guide, 조치 기록 폼(Action plan),
  기록된 intervention 목록, 팀 인계 메모(Team Handoff).

오른쪽 탐색 영역은 네 개의 탭입니다.

- **실시간 지표 (Vitals)**: 핵심 지표 상세(**Metric Ledger**: CPU, Load, NVMe,
  Wi-Fi)와 범주별 관측 상태(**Telemetry Matrix**: CPU profile, memory, disk,
  NVMe health/capacity/I/O, fan, thermal, battery, Wi-Fi link, network, kernel,
  agent freshness 등).
- **진단 및 가설 (Diagnosis)**: 규칙 기반 원인 후보(Top hypotheses), 조치 전후
  검증(Verification), 인계용 결론(Report).
- **이벤트 로그 (Timeline)**: 수집된 이벤트의 증거 타임라인.
- **수집기 상태 (Operations)**: stale 장비/운영 카드(Operations Rail)와
  category/component/model/kernel 기준 반복 신호(**Pattern Explorer**).

조치를 기록하면 서버가 조치 전후 telemetry 창을 비교해 `helped / worse /
unclear / insufficient_data` 판정을 돌려줍니다.

## 빠른 시작

API 서버를 실행합니다. 스크립트가 가상환경 생성과 설치까지 처리하고,
`0.0.0.0:8000`에 바인딩해 다른 장비의 collector도 접근할 수 있습니다.
DB는 `data/quipu.sqlite3`입니다.

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

서버는 시작할 때 데이터를 자동으로 만들지 않습니다. 처음 실행하면 장비가
없는 빈 화면이 정상입니다. 아래 방법 중 하나로 데이터를 넣습니다.

### 방법 1: 샘플 fleet 시딩

UI를 먼저 구경하고 싶다면 결정적 샘플 fixture(3개 장비: `thinkpad-p1`,
`xps-13`, `framework-13`)를 수동으로 시딩합니다.

```bash
cd apps/server
. .venv/bin/activate
python -m quipu_server.seed ../../fixtures/ingest/team-sample.json \
  --database ../../data/quipu.sqlite3
```

샘플 장비를 지우려면 서버를 멈추고 DB 파일을 삭제한 뒤 다시 시작합니다.

```bash
rm -f data/quipu.sqlite3 data/quipu.sqlite3-wal data/quipu.sqlite3-shm
```

### 방법 2: 이 노트북 연결

다른 터미널에서 collector를 한 번 실행합니다.

```bash
sudo apt-get install smartmontools   # NVMe SMART 수집(선택)
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

웹 UI를 새로고침하면 현재 노트북이 표시됩니다.

## 다른 노트북/컴퓨터 연결

`scripts/dev-server.sh`는 이미 `0.0.0.0`에 바인딩하므로 같은 LAN의 다른
장비에서 `http://<server-ip>:8000`으로 접근할 수 있습니다. 방화벽이 있다면
TCP `8000`을 허용합니다.

다른 Linux 노트북에서 collector를 설치하고 같은 서버로 전송합니다.

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

- `--device-id`는 장비마다 다르게, 그리고 바꾸지 않고 유지합니다.
- `--device-alias`는 화면에 보일 별명입니다. 별명이 있으면 UI는
  `별명 · hostname`으로 표시합니다.
- 빠른 테스트는 `dev-token`으로 가능하지만, 반복 운용은 장치별
  enrollment token을 권장합니다(아래 [토큰과 인증](#토큰과-인증)).

### Windows 워크스테이션 연결

Windows에서는 같은 collector 패키지를 PowerShell scheduled-task wrapper로
실행합니다. 처음 설치하거나 최신 릴리스로 갱신한 뒤에는 가상환경을 다시
설치하고 scheduled task를 재등록합니다.

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

- `-InstallSensorTools`: 공식 sensor 도구(LibreHardwareMonitor 등) 설치.
- `-Highest`: 관리자 sensor 접근이 필요한 CPU core 온도/팬 RPM 수집용.

Windows scheduled task는 사용자 로그온 시 숨김 실행되고, 중복 실행을
방지하며, offline buffer를 켠 채 기본 5분 간격으로 전송합니다. Windows
metric이 일부 비어 있을 때의 진단 절차는
[사용자 매뉴얼](USER_MANUAL.md)의 Windows 절을 보세요.

## Collector가 읽는 신호

collector는 시스템 신호를 읽기 전용으로 수집합니다. 원격 명령 실행이나
자동 수리는 하지 않습니다. NVMe R/W 처리량 계산을 위해 state directory에
이전 sector counter만 저장합니다.

| 범주               | 대표 metric                                                                                                                                                                                                                                           | 출처 (Linux / Windows)                                         |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| CPU load           | `cpu.load_1m/5m/15m` (Linux), `cpu.load_percent`, `cpu.core_<n>.load_percent` (Windows)                                                                                                                                                               | `/proc/loadavg` / hardware monitor `Load` sensor               |
| CPU 토폴로지       | `cpu.physical_cores`, `cpu.logical_threads`, `cpu.performance_cores`, `cpu.efficient_cores`, `cpu.low_power_efficient_cores`                                                                                                                          | `/proc/cpuinfo` / CIM                                          |
| CPU 온도           | `cpu.package_temp_c`, `cpu.core_<n>.temp_c`, `cpu.p_core_<n>.temp_c`, `cpu.e_core_<n>.temp_c`                                                                                                                                                         | hwmon coretemp / LibreHardwareMonitor·OpenHardwareMonitor      |
| Thermal zone       | `thermal.<sensor>.temp_c`, `thermal.windows_zone_<n>.temp_c`                                                                                                                                                                                          | sysfs thermal / ACPI·performance counter                       |
| NVMe 온도·SMART    | `nvme.temp_c`, `nvme.smart_passed`, `nvme.critical_warning`, `nvme.available_spare_percent`, `nvme.percentage_used_percent`, `nvme.media_errors`, `nvme.power_on_hours`, `nvme.unsafe_shutdowns`, `nvme.error_log_entries` + 장치별 `nvme.<device>.*` | hwmon·sysfs·`smartctl --json` / reliability counter·smartctl   |
| NVMe 용량·I/O      | `nvme.capacity_bytes`, `nvme.read_bytes_per_sec`, `nvme.write_bytes_per_sec` + 장치별                                                                                                                                                                 | sysfs block(샘플 간 delta) / performance counter               |
| Wi-Fi              | `wifi.signal_dbm`, `wifi.rx_bitrate_mbps`, `wifi.tx_bitrate_mbps`, `wifi.link_bitrate_mbps` + 인터페이스별                                                                                                                                            | `/proc/net/wireless`·`iw`·`iwconfig` / `netsh`·WMI             |
| 메모리·디스크·전원 | `memory.used_percent`, `disk.root_used_percent`, `battery.capacity_percent`, `battery.ac_online`                                                                                                                                                      | procfs·sysfs / CIM                                             |
| 팬                 | `fan.rpm`, `fan.<sensor>.rpm`                                                                                                                                                                                                                         | hwmon(읽을 수 있는 모든 팬) / hardware monitor sensor          |
| 이벤트             | thermal, storage, power, graphics, memory, network, reboot, update                                                                                                                                                                                    | kern.log·journalctl 등 / Windows Event Log(System·Application) |

CPU core 번호는 OS가 노출한 sensor/core id를 그대로 따릅니다. 없는 번호를
만들어 채우지 않습니다. Wi-Fi bitrate는 인터넷 속도 측정값이 아니라 AP와의
link bitrate입니다. NVMe R/W 속도는 두 샘플 사이 delta라서 첫 샘플에는
비어 있을 수 있습니다.

Windows에서 `cpu.core_<n>.load_percent`는 보이는데 `cpu.*.temp_c`가 없으면
UI 문제가 아니라 hardware monitor `Temperature` sensor가 collector에
노출되지 않은 상태입니다. 진단 절차는 [사용자 매뉴얼](USER_MANUAL.md)을
보세요.

## Collector 주요 옵션

```bash
quipu-collector --dry-run                          # 전송 없이 JSON 출력
quipu-collector --server-url URL --token TOKEN     # 한 번 수집·전송
quipu-collector --dry-run --interval 60 --iterations 3   # 60초 간격 3회
```

| 옵션                                | 기본값                                 | 설명                                                 |
| ----------------------------------- | -------------------------------------- | ---------------------------------------------------- |
| `--server-url`                      | (없음)                                 | 생략하면 stdout에 JSON만 출력                        |
| `--token`                           | (없음)                                 | `--server-url` 사용 시 필수(`--dry-run` 제외)        |
| `--device-id` / `--device-alias`    | 자동 생성 / (없음)                     | 장비 고유 ID / 화면 별명                             |
| `--interval` / `--iterations`       | (없음)                                 | 반복 수집 간격(초) / 횟수                            |
| `--offline-buffer`                  | off                                    | 전송 실패 시 로컬 spool에 보관 후 다음 성공 시 flush |
| `--spool-dir`                       | `~/.local/state/quipu/collector-spool` | spool 위치                                           |
| `--spool-max-batches`               | `288`                                  | spool 보존 개수(5분 간격 기준 약 하루)               |
| `--state-dir`                       | `~/.local/state/quipu/collector-state` | NVMe R/W delta 계산용 상태                           |
| `--flush-limit` / `--retry-backoff` | (없음) / `0`                           | flush 상한 / 실패 후 대기(초)                        |

## 서버 API 요약

모든 경로는 `/api` 아래에 있습니다. 인증 헤더는 `X-Quipu-Agent-Token`입니다.

| 경로                                                                              | 용도                                    | 인증         |
| --------------------------------------------------------------------------------- | --------------------------------------- | ------------ |
| `GET /api/health`                                                                 | liveness 확인                           | 없음         |
| `POST /api/ingest/batches`                                                        | 관측 batch 수신(중복은 200, 신규는 201) | ingest token |
| `GET /api/fleet/overview`                                                         | fleet 장비 요약                         | 없음         |
| `GET /api/investigations/queue`                                                   | 우선순위 조사 queue                     | 없음         |
| `GET /api/investigations/{id}`                                                    | 조사 상세(intervention 포함)            | 없음         |
| `GET·POST /api/investigations/{id}/notes`                                         | 인계 메모 조회/작성                     | 없음         |
| `POST /api/investigations/{id}/interventions`                                     | 조치 기록                               | 없음         |
| `GET /api/patterns/overview`                                                      | 반복 신호 패턴                          | 없음         |
| `POST·GET /api/enrollment/tokens`, `POST .../{id}/rotate`, `POST .../{id}/revoke` | 장치별 token 발급/조회/회전/폐기        | dev token    |
| `GET /api/admin/schema`                                                           | 스키마 버전·테이블 확인                 | dev token    |

## 토큰과 인증

- 개발 기본 토큰은 `dev-token`이며 `QUIPU_DEV_AGENT_TOKEN` 환경 변수로
  바꿀 수 있습니다.
- ingest는 dev token 또는 해당 `device_id`로 발급된 활성 enrollment token을
  받습니다. 장치별 token은 SHA-256 hash로만 저장됩니다.

```bash
curl -sS -X POST http://127.0.0.1:8000/api/enrollment/tokens \
  -H "Content-Type: application/json" \
  -H "X-Quipu-Agent-Token: dev-token" \
  -d '{"device_id":"office-gram","label":"Office Gram collector"}'
```

응답의 `token`을 해당 장비 collector의 `--token`에 넣습니다.

## 환경 변수

| 변수                                                                                                                                                                                                                 | 대상                   | 기본값                  | 설명                                        |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- | ----------------------- | ------------------------------------------- |
| `QUIPU_DATABASE_PATH`                                                                                                                                                                                                | server                 | `data/quipu.sqlite3`    | SQLite 경로                                 |
| `QUIPU_DEV_AGENT_TOKEN`                                                                                                                                                                                              | server                 | `dev-token`             | 개발/관리용 토큰                            |
| `QUIPU_SERVER_URL`, `QUIPU_AGENT_TOKEN`, `QUIPU_COLLECTOR_DEVICE_ID`, `QUIPU_COLLECTOR_DEVICE_ALIAS`, `QUIPU_SPOOL_DIR`, `QUIPU_SPOOL_MAX_BATCHES`, `QUIPU_STATE_DIR`, `QUIPU_COLLECTOR_BIN`, `QUIPU_COLLECTOR_ROOT` | collector 운영 wrapper | —                       | systemd/Windows wrapper가 CLI 옵션으로 변환 |
| `QUIPU_COLLECTOR_INTERVAL`, `QUIPU_COLLECTOR_ENV`                                                                                                                                                                    | Windows wrapper        | `300` / —               | 수집 간격(초) / 환경 파일 경로              |
| `QUIPU_SMARTCTL_BIN`                                                                                                                                                                                                 | collector              | 자동 탐지               | smartctl 경로 지정                          |
| `QUIPU_LIBRE_HARDWARE_MONITOR_DLL`                                                                                                                                                                                   | collector(Windows)     | 자동 탐지               | LibreHardwareMonitorLib.dll 경로 지정       |
| `VITE_API_BASE_URL`                                                                                                                                                                                                  | web                    | `http://127.0.0.1:8000` | 웹 UI가 호출할 API 주소                     |

## 운영 설치

Linux에서는 systemd timer가 5분마다 collector를 한 번씩 실행합니다.

```bash
scripts/install-collector-systemd.sh --dry-run   # 미리보기
sudo scripts/install-collector-systemd.sh --no-enable
sudo systemctl enable --now quipu-collector.timer
```

설정은 `/etc/quipu/collector.env`에 둡니다. Windows scheduled task 설치,
환경 파일, 제거 절차를 포함한 전체 운영 절차는
[사용자 매뉴얼](USER_MANUAL.md)을 보세요.

## 아키텍처

```text
Linux collector / Windows collector / compatible external collector
      |
      v
FastAPI ingest API  (X-Quipu-Agent-Token)
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

CI는 Python 3.12와 Node 24에서 아래와 같은 검증을 실행합니다.

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
  collector/     읽기 전용 collector CLI (Linux/Windows) + systemd/scheduled-task 운영 스크립트
  server/        FastAPI API, SQLite 저장, 규칙 기반 분석, 수동 seed CLI
  web/           Vite React 조사 UI
data/            로컬 SQLite DB (dev-server.sh가 사용)
docs/
  superpowers/   제품 결정, 대시보드, 로드맵, ship checklist
fixtures/
  ingest/        결정적 샘플 batch (team-sample.json)
scripts/
  dev-server.sh                          로컬 API 서버 (0.0.0.0:8000)
  install-collector-systemd.sh           Linux collector 설치/제거
  install-collector-scheduled-task.ps1   Windows collector 설치/제거
```

## 문서

- [사용자 매뉴얼](USER_MANUAL.md) — 설치, 운영, 화면 해석, 문제 해결
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Project dashboard](docs/superpowers/DASHBOARD.md)
- [Roadmap](docs/superpowers/ROADMAP.md)
- [Ship checklist](docs/superpowers/SHIP_CHECKLIST.md)

## 안전 경계

현재 릴리스에 포함하지 않습니다.

- 원격 수리 명령 실행
- production deployment
- package publishing
- AI 단독 결론
- raw log warehouse

Quipu의 기본값은 로컬 우선, 읽기 전용, 근거 기반입니다.

## 라이선스

Quipu는 [Apache License 2.0](LICENSE)으로 배포됩니다. 상업적 이용, 수정,
재배포가 자유롭고 명시적인 특허 라이선스를 포함합니다. 자세한 내용은
[LICENSE](LICENSE)와 [NOTICE](NOTICE)를 보세요.
