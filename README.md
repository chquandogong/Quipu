# Quipu

<p align="center">
  <img alt="CI" src="https://github.com/chquandogong/Quipu/actions/workflows/ci.yml/badge.svg">
  <img alt="Version" src="https://img.shields.io/badge/version-v0.9.0-2f6f7e">
  <img alt="Status" src="https://img.shields.io/badge/status-local--first%20prototype-5b6b73">
  <img alt="License" src="https://img.shields.io/badge/license-not%20selected-lightgrey">
</p>

<p align="center">
  <strong>팀용 Linux 워크스테이션 건강 조사 플랫폼</strong><br>
  시스템 모니터가 아니라, 문제 해결 과정을 제품화한 로컬 우선 조사 도구입니다.
</p>

<p align="center">
  한국어 | <a href="README.en.md">English</a> | <a href="README.zh-CN.md">简体中文</a>
</p>

---

## 한눈에

Quipu는 여러 대의 Linux 노트북과 개발 워크스테이션에서 발생하는
발열, 재부팅, 그래픽 세션 오류, 저장장치 경고, Wi-Fi 불안정, 물리적
환경 변화를 한곳에 모아 팀이 함께 조사하도록 돕습니다.

핵심은 차트를 많이 보여주는 것이 아니라, 다음 질문에 빨리 답하는
것입니다.

- 지금 어떤 장비를 먼저 봐야 하는가?
- 왜 위험한가?
- 어떤 원인이 가장 그럴듯한가?
- 근거와 반대 근거는 무엇인가?
- 사람이 다음에 무엇을 확인하거나 조치해야 하는가?
- 조치 후 실제로 상태가 좋아졌는가?
- 같은 문제가 다른 장비에서도 반복되는가?

```text
Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report
```

## UI/UX 원칙

Quipu의 화면은 모든 로그와 지표를 한 번에 펼치지 않습니다. 최신 dashboard,
design system, progressive disclosure 사례를 비교한 결과, 단순 카드형
대시보드보다 어두운 `Command Center` 방식을 채택했습니다. 첫 화면은 한
사건에 대해 네 가지 답과 핵심 signal console을 강하게 보여줍니다.

- 무엇을 지금 확인해야 하는가?
- 왜 중요한가?
- 다음 행동은 무엇인가?
- 어떤 증거가 있어야 해결됐다고 말할 수 있는가?

상세 근거는 요약 상태로 접혀 있다가 마우스 접근, 키보드 포커스, 버튼
클릭 흐름에서 확장됩니다. 핵심 CTA는 `Review evidence`, `Record action`,
`Verify result`로 고정합니다.

`Medium`, `Warning`, `Triage` 같은 짧은 상태 단어는 화면에 계속 설명문을
늘어놓지 않고 status chip으로 유지합니다. 대신 마우스 hover와 키보드
focus에서 의미를 보여줘, 처음 보는 사람도 우선순위, 위험도, DTIHAVR
진행 단계를 같은 기준으로 해석할 수 있게 합니다.

CPU package, Load Average, NVMe 같은 핵심 지표는 숫자만 보여주지 않습니다.
각 metric 카드의 정보 버튼은 한국어 설명과 영어 기술 용어를 함께 보여줍니다.
예를 들어 Load 값은 순간 CPU 사용률이 아니라 Linux 1분 load average임을
명시합니다.

CPU, Load, NVMe만으로는 단일 thermal triage에는 도움이 되지만 팀용 원인
분석에는 충분하지 않습니다. 그래서 현재 UI는 Wi-Fi signal을 핵심 signal로
승격하고, `Telemetry Matrix`에서 Memory, Fan RPM, NVMe Health, Disk Health,
Battery Power, Network Events, Reconnect History, Thermal Throttling,
Kernel Warnings, Agent Freshness를 함께 보여줍니다. 이후 더 깊은 SMART/NVMe
health와 fan-control이 아닌 fan-context 분석을 같은 구조로 확장합니다.

v0.9.0 UI는 여기에 `Operations Rail`, `Team Handoff`, `Pattern Explorer`를
덧붙였습니다. 운영 레일은 agent freshness, offline buffer, enrollment guard,
pattern radar를 한 줄로 보여주고, 팀 인계는 조사 항목별 메모를 남기며,
패턴 탐색은 category/model/kernel 기준 반복 신호를 묶어 보여줍니다.

제작자와 버전 정보는 헤더의 작은 metadata chip으로만 유지합니다. 큰
creator/reference 이미지 영역은 조사 판단에 직접 도움이 되지 않아 제거했습니다.

## 왜 Quipu인가

개발 장비의 장애는 단일 지표로 설명하기 어렵습니다. CPU 온도, 커널
로그, GPU 드라이버 경고, SSD 상태, Wi-Fi 품질, 업데이트, 부팅 이력,
책상 위 물리적 배치가 동시에 영향을 줄 수 있습니다.

Quipu는 센서 값과 시스템 이벤트, 사람이 시도한 개입을 조사 기록으로
묶습니다.

- 현재 상태
- 사건 타임라인
- 원인 가설
- 지지 근거와 반대 근거
- 다음 확인 항목
- 사람이 수행한 조치
- 전후 비교
- 팀 공유용 보고서

## 차별성

1. **조사 우선, 지표는 그다음**
   Quipu는 기계, 사건, 팀 문제에서 출발한 뒤 설명에 필요한 지표만
   꺼냅니다.

2. **근거가 연결된 결론**
   모든 판단은 지지 근거, 반대 근거, 신뢰도, 원본 출처를 함께 보여줘야
   합니다.

3. **팀 단위 패턴 기억**
   모델, 커널, GPU 드라이버, SSD, Wi-Fi 장치, 워크로드, 물리적 배치별
   반복 문제를 찾는 방향으로 설계합니다.

4. **개입 검증**
   노트북을 살짝 들어 올리기, 전원 프로파일 변경, 드라이버 업데이트 같은
   조치를 기록하고 전후 건강 상태를 비교합니다.

5. **읽기 전용, 로컬 우선 신뢰성**
   첫 제품은 팀 장비에서 안전하게 돌 수 있어야 합니다. 에이전트는 읽기
   전용이고, 저장소는 자체 호스팅이며, 원격 수리 명령은 없습니다.

## 현재 상태

Quipu는 초기 로컬 우선 프로토타입입니다.

구현됨:

- FastAPI ingest API
- SQLite WAL 기반 저장소
- 규칙 기반 fleet overview
- 결정적 샘플 장비 데이터
- Investigation queue/detail API
- 읽기 전용 Linux collector
- collector의 best-effort kernel thermal throttling 및 NetworkManager reconnect event 요약 수집
- collector의 root filesystem 사용률, 배터리 잔량, AC 연결 상태 수집
- collector의 best-effort kernel storage 및 power warning event 요약 수집
- collector의 hwmon 기반 Fan RPM 및 sysfs 기반 NVMe SMART-lite health 수집
- collector의 dry-run, interval, iterations 기반 경량 운용 루프
- collector의 offline local ring buffer, flush limit, retry backoff
- collector systemd service/timer, 환경 파일 예시, wrapper, dry-run 설치/제거 스크립트
- collector의 graphics, memory, update, reboot marker 요약 수집
- device enrollment, per-device token ingest, token rotation/revocation API
- schema version endpoint와 조사 항목별 team handoff note API
- category/model/kernel 기준 Pattern Explorer API
- 조사 항목별 intervention 기록
- intervention 전후 검증 결과
- Vite React 조사 중심 UI
- 고대비 dark Command Center 첫 화면, 핵심 signal console, hover/focus 확장 패널
- CPU, Load, NVMe, Wi-Fi 핵심 metric별 한국어 설명, 영어 기술 용어, 시간창, 해석, 다음 확인 tooltip
- Memory, Fan RPM, NVMe Health, Disk Health, Battery Power, Network Events, Reconnect History, Thermal Throttling, Kernel Warnings, Agent Freshness를 묶는 Telemetry Matrix
- Operations Rail, Team Handoff, Pattern Explorer UI
- 작고 항상 보이는 Made by, About, Version metadata chip
- 서버, 컬렉터, 웹 테스트 및 빌드용 GitHub Actions CI

다음 방향:

- 역할 기반 팀 워크플로, redaction, retention policy
- Postgres adapter, backup/restore, longer-term baseline analytics
- package publishing과 production deployment 준비

## 빠른 시작

샘플 데이터가 포함된 API 서버를 실행합니다.

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

## Collector

collector는 root 권한 없이 Linux 신호를 읽어 Quipu observation batch로
출력합니다. 기본값은 one-shot 실행이고, `--interval`을 주면 가벼운 반복
수집 루프로 운용할 수 있습니다. 수리 명령을 실행하지 않고, raw log 전체를
업로드하지 않습니다.

현재 수집하는 주요 신호:

- `cpu.load_1m`: Linux 1분 load average
- `memory.used_percent`: `/proc/meminfo` 기반 메모리 사용률
- `disk.root_used_percent`: root filesystem 사용률
- `cpu.package_temp_c`, `thermal.*.temp_c`: sysfs thermal zone 온도
- `nvme.temp_c`: hwmon에 노출된 NVMe 온도
- `fan.rpm`: hwmon에 노출된 첫 번째 fan 회전수
- `nvme.critical_warning`, `nvme.available_spare_percent`, `nvme.percentage_used_percent`, `nvme.media_errors`: sysfs에 노출된 NVMe SMART-lite health
- `wifi.signal_dbm`: `/proc/net/wireless` 기반 Wi-Fi 신호
- `battery.capacity_percent`, `battery.ac_online`: `/sys/class/power_supply` 기반 배터리/AC 상태
- kernel thermal, storage, power, graphics, memory warning 요약, update/reboot marker, NetworkManager reconnect 요약

로컬 출력:

```bash
cd apps/collector
python -m venv .venv
. .venv/bin/activate
pip install -e .
quipu-collector --dry-run
```

로컬 Quipu 서버로 한 번 전송:

```bash
quipu-collector --server-url http://127.0.0.1:8000 --token dev-token
```

서버가 잠시 내려가거나 네트워크가 끊겨도 batch를 잃지 않도록 로컬 spool에
버퍼링할 수 있습니다.

```bash
quipu-collector \
  --server-url http://127.0.0.1:8000 \
  --token "$QUIPU_AGENT_TOKEN" \
  --offline-buffer \
  --spool-dir ~/.local/state/quipu/collector-spool
```

장치별 수집 토큰은 개발/admin 토큰으로 생성하고, 이후 해당 장비 ingest에만
사용합니다.

```bash
curl -sS -X POST http://127.0.0.1:8000/api/enrollment/tokens \
  -H "Content-Type: application/json" \
  -H "X-Quipu-Agent-Token: dev-token" \
  -d '{"device_id":"thinkpad-p1","label":"ThinkPad P1 collector"}'
```

반복 수집 smoke test:

```bash
quipu-collector --dry-run --interval 60 --iterations 3
```

간단한 supervised loop:

```bash
quipu-collector --server-url http://127.0.0.1:8000 --token dev-token --interval 300
```

이 컴퓨터에서 5분 자동 수집으로 고정하려면 systemd timer를 사용합니다. 아래
예시는 현재 개발 머신의 경로(`/home/chquan/Quipu`)와 로컬 API
(`http://127.0.0.1:8000`) 기준입니다. 다른 팀 장비에서는 repository 경로,
device id, token만 장비별로 바꾸면 됩니다.

collector 실행 파일 준비:

```bash
cd /home/chquan/Quipu/apps/collector
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

systemd timer 설치 미리보기:

```bash
cd /home/chquan/Quipu
scripts/install-collector-systemd.sh --dry-run
```

실제 설치:

```bash
sudo scripts/install-collector-systemd.sh --no-enable
```

collector 환경 파일 설정:

```bash
sudo tee /etc/quipu/collector.env >/dev/null <<EOF
QUIPU_SERVER_URL=http://127.0.0.1:8000
QUIPU_AGENT_TOKEN=dev-token
QUIPU_COLLECTOR_ROOT=/
QUIPU_COLLECTOR_DEVICE_ID=local-computer
QUIPU_COLLECTOR_BIN=/home/chquan/Quipu/apps/collector/.venv/bin/quipu-collector
QUIPU_SPOOL_DIR=/var/lib/quipu/collector-spool
QUIPU_SPOOL_MAX_BATCHES=288
EOF
sudo chmod 600 /etc/quipu/collector.env
```

수동으로 한 번 실행해서 권한/경로/서버 연결을 확인:

```bash
sudo systemctl start quipu-collector.service
systemctl status quipu-collector.service --no-pager
journalctl -u quipu-collector.service -n 80 --no-pager
```

5분 자동 수집 활성화:

```bash
sudo systemctl enable --now quipu-collector.timer
systemctl list-timers quipu-collector.timer
```

중지/비활성화:

```bash
sudo systemctl disable --now quipu-collector.timer
```

완전 제거:

```bash
sudo scripts/uninstall-collector-systemd.sh
```

설치 스크립트는 `quipu-collector` 실행 파일이 대상 장비에 이미 설치되어
있다고 가정합니다. 운영 환경에서는 `dev-token` 대신 장치별 enrollment token을
사용하고, 아직 package publishing과 production deployment는 포함하지 않습니다.

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

MVP 경계:

- 자체 호스팅 기본값
- 읽기 전용 수집
- 원격 명령 실행 없음
- 자동 수리 없음
- 클라우드 의존 없음
- full raw-log warehouse 지양

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
python -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
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
  collector/     읽기 전용 Linux observation collector
  server/        FastAPI API, SQLite persistence, rule-based analysis
  web/           Vite React UI
docs/
  superpowers/   제품 결정, 설계, 계획, 대시보드
fixtures/
  ingest/        결정적 샘플 health batch
scripts/
  dev-server.sh  로컬 seeded API server
```

## 주요 문서

- [Project dashboard](docs/superpowers/DASHBOARD.md)
- [Decision log](docs/superpowers/DECISION_LOG.md)
- [Roadmap](docs/superpowers/ROADMAP.md)
- [Ship checklist](docs/superpowers/SHIP_CHECKLIST.md)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## 안전 경계

현재와 가까운 미래의 기본값:

- 읽기 전용 데이터 수집
- 자체 호스팅 저장소
- 최소 로그 발췌
- 원격 명령 실행 없음
- 자동 수리 없음
- AI 결론은 근거 링크 없이는 권위가 없음

## 라이선스

아직 라이선스가 선택되지 않았습니다. 명시적 라이선스가 추가되기 전까지
재배포 권한을 가정하지 마세요.
