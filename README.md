# Quipu

<p align="center">
  <img alt="CI" src="https://github.com/chquandogong/Quipu/actions/workflows/ci.yml/badge.svg">
  <img alt="Version" src="https://img.shields.io/badge/version-v0.3.1-2f6f7e">
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

Quipu의 화면은 모든 로그와 지표를 한 번에 펼치지 않습니다. 여러 대안을
비교한 결과, 단순 카드형 대시보드나 장식적인 mission-control 화면보다
`Investigation Lens` 방식을 채택했습니다. 먼저 한 사건을 중심에 두고
세 가지 질문만 보이게 합니다.

- 무엇을 먼저 봐야 하는가?
- 지금 어떤 행동을 기록해야 하는가?
- 그 행동이 실제로 효과가 있었는가?

상세 근거는 요약 상태로 접혀 있다가 마우스 접근, 키보드 포커스, 버튼
클릭 흐름에서 확장됩니다. 핵심 CTA는 `Review evidence`, `Record action`,
`Verify result`로 고정해 사용자가 다음 행동을 놓치지 않게 합니다.

CPU package, Load Average, NVMe 같은 핵심 지표는 숫자만 보여주지 않습니다.
각 metric 카드의 정보 버튼에 마우스가 닿거나 키보드 포커스가 가면
`Definition`, `Window`, `How to read`, `Next check`가 열립니다. 예를 들어
Load 값은 순간 CPU 사용률이 아니라 Linux 1분 load average임을 명시합니다.

Dogu Robotics, Dogu X, Physical AI 공개 레퍼런스와 제작자 정보는 접힌
보조 영역으로 내려, 제품의 맥락은 남기되 조사 업무 표면은 방해하지
않도록 설계했습니다.

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
- 읽기 전용 one-shot Linux collector
- 조사 항목별 intervention 기록
- intervention 전후 검증 결과
- Vite React 조사 중심 UI
- Investigation Lens형 focus board와 hover/focus 확장 패널
- 핵심 metric별 정의, 시간창, 해석, 다음 확인 항목 tooltip
- 접힌 제작자/Physical AI 레퍼런스 영역
- 서버, 컬렉터, 웹 테스트 및 빌드용 GitHub Actions CI

다음 방향:

- supervised local agent 형태의 collector
- 모델, 커널, 드라이버, 저장장치, Wi-Fi, 워크로드, 물리적 환경별 팀 패턴 탐색
- 역할 기반 팀 워크플로, redaction, retention policy

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

collector는 root 권한 없이 Linux 신호를 한 번 읽어 Quipu observation
batch로 출력합니다. 수리 명령을 실행하지 않고, raw log 전체를 업로드하지
않습니다.

로컬 출력:

```bash
cd apps/collector
python -m venv .venv
. .venv/bin/activate
pip install -e .
quipu-collector
```

로컬 Quipu 서버로 전송:

```bash
quipu-collector --server-url http://127.0.0.1:8000 --token dev-local-token
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
  collector/     읽기 전용 one-shot Linux observation collector
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
