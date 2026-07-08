# Quipu

<p align="center">
  <img alt="CI" src="https://github.com/chquandogong/Quipu/actions/workflows/ci.yml/badge.svg">
  <img alt="Version" src="https://img.shields.io/badge/version-v0.10.0-2f6f7e">
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

## v0.10.0 핵심

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
- **Telemetry Matrix**: Memory, Fan, NVMe Health, Disk, Battery, Network,
  Thermal, Kernel, Agent freshness 범주별 관측 상태.
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
  --device-id local-computer
```

웹 UI를 새로고침하면 현재 노트북만 표시됩니다.

## Collector가 읽는 신호

collector는 읽기 전용입니다. 원격 명령 실행이나 자동 수리는 하지 않습니다.

- `cpu.load_1m`, `cpu.load_5m`, `cpu.load_15m`: `/proc/loadavg`의 1/5/15분 load average.
- `cpu.package_temp_c`, `cpu.core_<n>.temp_c`: hwmon/coretemp 기반 CPU 온도.
- `thermal.*.temp_c`: sysfs thermal zone 온도.
- `nvme.temp_c`, `nvme.<device>.temp_c`: NVMe 대표/장치별 온도.
- `wifi.signal_dbm`, `wifi.<interface>.signal_dbm`: `/proc/net/wireless` 신호 세기.
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
