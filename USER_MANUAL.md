# Quipu User Manual

이 문서는 Quipu를 로컬에서 실행하고, Linux 노트북 데이터를 수집하고, 화면의
조사 정보를 해석하는 운영자용 매뉴얼입니다.

## 1. 대상 사용자

Quipu는 다음 사용자를 기준으로 설계했습니다.

- Linux 노트북이나 개발 워크스테이션을 직접 운영하는 개발자.
- 팀 장비의 발열, 그래픽 오류, Wi-Fi, 저장장치, 재부팅 문제를 조사하는 운영자.
- 조치 전후 결과와 팀 인계 메모를 남겨야 하는 기술 리더.

Quipu는 원격 수리 도구가 아닙니다. collector는 읽기 전용이고, 서버는 받은
관측값을 저장한 뒤 규칙 기반으로 조사 항목을 만듭니다.

## 2. 준비

필요한 도구:

- Python 3.11 이상
- Node.js 20 이상
- npm
- Linux 환경

저장소 루트는 이 문서에서 `/home/chquan/Quipu`로 가정합니다. 다른 경로를 쓰면
명령의 경로만 바꾸면 됩니다.

## 3. 샘플 데이터로 실행

처음 UI를 확인할 때는 샘플 서버가 가장 빠릅니다.

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

`scripts/dev-server.sh`는 샘플 fixture를 DB에 넣습니다. 실제 이 노트북만 보고
싶다면 다음 장의 절차로 DB를 비우고 collector를 실행합니다.

## 4. 샘플 DB를 지우고 이 노트북만 표시

기존 API 서버를 멈춘 뒤 DB 파일을 지웁니다.

```bash
cd /home/chquan/Quipu
rm -f data/quipu.sqlite3 data/quipu.sqlite3-wal data/quipu.sqlite3-shm
```

빈 DB로 API 서버를 실행합니다.

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
quipu-collector --server-url http://127.0.0.1:8000 --token dev-token --device-id local-computer
```

웹 UI를 새로고침하면 현재 노트북 하나만 표시됩니다.

## 5. Collector 명령

로컬 JSON만 보고 싶을 때:

```bash
quipu-collector --dry-run
```

서버로 한 번 전송:

```bash
quipu-collector --server-url http://127.0.0.1:8000 --token dev-token
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
  --spool-dir ~/.local/state/quipu/collector-spool
```

## 6. systemd timer로 5분마다 수집

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
QUIPU_COLLECTOR_BIN=/home/chquan/Quipu/apps/collector/.venv/bin/quipu-collector
QUIPU_SPOOL_DIR=/var/lib/quipu/collector-spool
QUIPU_SPOOL_MAX_BATCHES=288
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

## 7. 화면 읽는 법

### Command Center

첫 화면은 선택된 조사 항목을 보여줍니다.

- `Medium`: queue 우선순위입니다.
- `Warning`: 위험도입니다.
- `Triage`: 현재 DTIHAVR 단계입니다.
- `Problem Guide`: 문제, 먼저 볼 근거, 다음 행동입니다.

### Telemetry Brief

CPU, Load, NVMe, Wi-Fi 대표값입니다. 이 줄은 결론이 아니라 조사 보조 신호입니다.

### Metric Ledger

핵심 지표의 상세 행입니다.

- **CPU Package**: CPU package 온도와 core별 온도.
- **Load Average**: Linux 1분, 5분, 15분 load average.
- **NVMe SSD**: 대표 NVMe 온도와 장치별 온도.
- **Wi-Fi Signal**: 대표 Wi-Fi 신호와 인터페이스별 신호.

각 행의 `?` 버튼은 정의, 시간창, 해석 기준, 다음 확인 항목을 설명합니다.

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

### Telemetry Matrix

10개 범주의 관측 상태를 보여줍니다. `9/10 observed`는 위험 점수가 아니라
10개 범주 중 9개가 들어왔다는 뜻입니다.

### Investigation Queue

가장 먼저 볼 조사 항목입니다. 항목을 선택하면 오른쪽 상세 영역이 바뀝니다.

### Evidence, Hypotheses, Action, Verification

- Evidence: 수집된 이벤트와 출처.
- Hypotheses: 규칙 기반 원인 후보.
- Action: 사람이 할 다음 조치.
- Verification: intervention 전후 비교 결과.
- Team Handoff: 팀 인계 메모.

## 8. 장치별 token

개발용 `dev-token` 대신 장치별 token을 만들 수 있습니다.

```bash
curl -sS -X POST http://127.0.0.1:8000/api/enrollment/tokens \
  -H "Content-Type: application/json" \
  -H "X-Quipu-Agent-Token: dev-token" \
  -d '{"device_id":"local-computer","label":"Local notebook collector"}'
```

반환된 `token`을 collector의 `--token` 또는 `/etc/quipu/collector.env`에 넣습니다.

## 9. 자주 보는 문제

### 화면이 비어 있음

API 서버가 떠 있는지 확인합니다.

```bash
curl http://127.0.0.1:8000/api/health
```

웹 UI가 API를 찾는 기본 주소는 `http://127.0.0.1:8000`입니다.

### 샘플 장비가 계속 보임

샘플 DB가 남아 있습니다.

```bash
rm -f data/quipu.sqlite3 data/quipu.sqlite3-wal data/quipu.sqlite3-shm
```

그 뒤 API 서버를 다시 시작하고 collector를 한 번 전송합니다.

### core 번호가 띄엄띄엄임

정상일 수 있습니다. Linux가 노출한 sensor/core id가 연속 번호가 아닐 수
있습니다. Quipu는 없는 번호를 만들어 표시하지 않습니다.

### NVMe Health가 Unavailable

일부 장비는 root 없이 NVMe SMART-lite 값을 노출하지 않습니다. 온도만 보이는
것은 정상일 수 있습니다.

### fan이 0 rpm 또는 N/A

노트북 firmware나 hwmon 드라이버가 fan 값을 노출하지 않거나, 팬이 멈춰 있는
상태일 수 있습니다. `sensors` 출력과 함께 확인합니다.

## 10. 안전 원칙

- collector는 읽기 전용입니다.
- 원격 명령 실행은 없습니다.
- 자동 수리는 없습니다.
- raw log 전체를 장기 저장하는 제품이 아닙니다.
- 운영 배포, package publishing, RBAC는 향후 hardening 항목입니다.
