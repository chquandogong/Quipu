# Quipu

<p align="center">
  <img alt="CI" src="https://github.com/chquandogong/Quipu/actions/workflows/ci.yml/badge.svg">
  <img alt="Version" src="https://img.shields.io/badge/version-v0.11.0-2f6f7e">
  <img alt="Status" src="https://img.shields.io/badge/status-local--first%20workstation%20health-5b6b73">
  <img alt="License" src="https://img.shields.io/badge/license-not%20selected-lightgrey">
</p>

<p align="center">
  <strong>Linux 워크스테이션 건강 조사 도구</strong><br>
  Quipu는 지표 대시보드가 아니라, 문제를 발견하고 근거로 조사하고 조치 결과를 남기는 로컬 우선 운영 도구입니다.
</p>

<p align="center">
  한국어 | <a href="README.en.md">English</a> | <a href="README.zh-CN.md">简体中文</a>
</p>

---

## 무엇인가

Quipu는 Linux 노트북과 개발 워크스테이션에서 발생하는 발열, 그래픽 오류,
Wi-Fi 불안정, 저장장치 경고, 전원 문제, 재부팅 흔적을 한 화면에 모읍니다.
첫 질문은 “CPU가 몇 도인가?”가 아니라 “지금 무엇을 조사해야 하며, 근거는
무엇인가?”입니다.

기본 조사 흐름은 다음 순서입니다.

```text
Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report
```

## v0.11.0 핵심

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
- **Investigation Queue**: 지금 확인해야 할 장비/사건 목록.
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

여러 대를 연결할 때는 `--device-id`를 장비마다 다르게 유지합니다. 운영 반복
수집에서는 `dev-token` 대신 장치별 enrollment token을 쓰는 것을 권장합니다.

## Collector가 읽는 신호

collector는 시스템 신호를 읽기 전용으로 수집합니다. 원격 명령 실행이나 자동
수리는 하지 않습니다. NVMe R/W 처리량 계산을 위해 collector state directory에
이전 sector counter를 저장할 수 있습니다.

- `cpu.load_1m`, `cpu.load_5m`, `cpu.load_15m`: `/proc/loadavg`의 1/5/15분 load average.
- `cpu.physical_cores`, `cpu.logical_threads`, `cpu.performance_cores`,
  `cpu.efficient_cores`, `cpu.low_power_efficient_cores`: CPU 모델과
  `/proc/cpuinfo`에서 확인한 코어/스레드 정보. Intel Core Ultra 5 125H는
  4P/8E/2LP-E/18 threads로 표시합니다.
- `cpu.package_temp_c`, `cpu.core_<n>.temp_c`: hwmon/coretemp 기반 CPU 온도.
- `thermal.*.temp_c`: sysfs thermal zone 온도.
- `nvme.temp_c`, `nvme.<device>.temp_c`: NVMe 대표/장치별 온도.
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
Linux collector
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
  collector/     Read-only Linux collector
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
