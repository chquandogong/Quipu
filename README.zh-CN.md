# Quipu

<p align="center">
  <img alt="CI" src="https://github.com/chquandogong/Quipu/actions/workflows/ci.yml/badge.svg">
  <img alt="Version" src="https://img.shields.io/badge/version-v0.10.0-2f6f7e">
  <img alt="Status" src="https://img.shields.io/badge/status-local--first%20workstation%20health-5b6b73">
  <img alt="License" src="https://img.shields.io/badge/license-not%20selected-lightgrey">
</p>

<p align="center">
  <strong>Linux 工作站健康调查工具</strong><br>
  Quipu 把只读 Linux 信号整理成证据、行动、验证和团队交接。
</p>

<p align="center">
  <a href="README.md">한국어</a> | <a href="README.en.md">English</a> | 简体中文
</p>

---

## 这是什么

Quipu 是本地优先的 Linux 笔记本和开发工作站健康调查工具。它收集温度、
load、NVMe、Wi-Fi、内存、磁盘、电池、风扇、kernel、图形、重启和更新信号，
并把它们放进一个调查流程：

```text
Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report
```

Quipu 不是远程修复工具。collector 是只读的，server 使用确定性的规则分析。

## v0.10.0 重点

- 文档从头重写。
- 新增 [用户手册](USER_MANUAL.md)。
- Load average 明确显示为 `1m / 5m / 15m`。
- CPU package 只显示 Linux 实际暴露的 core sensor。
- Intel Core Ultra 5 125H 的已确认 sensor 模式会按 `P`、`E`、`LP-E` 分组。
- NVMe 和 Wi-Fi 即使只有一个设备或接口，也使用独立 chip 显示。

## 使用样例数据运行

```bash
scripts/dev-server.sh
```

另开终端：

```bash
cd apps/web
npm install
npm run dev
```

打开：

```text
http://127.0.0.1:5173
```

## 只显示当前笔记本

停止 API server，删除样例 DB，然后启动空 DB：

```bash
rm -f data/quipu.sqlite3 data/quipu.sqlite3-wal data/quipu.sqlite3-shm
cd apps/server
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
QUIPU_DATABASE_PATH=../../data/quipu.sqlite3 uvicorn quipu_server.app:app --host 127.0.0.1 --port 8000 --reload
```

发送一次本机 collector batch：

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

刷新 Web UI。

## 主要界面

- Command Center：当前 case、优先级、风险、下一步。
- Problem Guide：问题、证据、下一步行动。
- Telemetry Brief：CPU、Load、NVMe、Wi-Fi 代表值。
- Metric Ledger：core、load、device、interface 的详细 chip 和 tooltip。
- Telemetry Matrix：memory、disk、fan、storage health、power、network、
  thermal、kernel、freshness 覆盖情况。
- Pattern Explorer：按 category、component、model、kernel 聚合重复信号。

## 验证

```bash
cd apps/server && . .venv/bin/activate && pytest -v
cd apps/collector && . .venv/bin/activate && pytest -v
cd apps/web && npm test && npm run build
```

## 文档

- [用户手册](USER_MANUAL.md)
- [Changelog](CHANGELOG.md)
- [Dashboard](docs/superpowers/DASHBOARD.md)
- [Ship Checklist](docs/superpowers/SHIP_CHECKLIST.md)
- [Roadmap](docs/superpowers/ROADMAP.md)
- [Security Policy](SECURITY.md)

## 边界

本版本不包含：

- 远程命令执行
- 自动修复
- 生产部署
- package publishing
- 仅靠 AI 的结论
- raw log warehouse
