# Quipu

<p align="center">
  <img alt="CI" src="https://github.com/chquandogong/Quipu/actions/workflows/ci.yml/badge.svg">
  <img alt="Version" src="https://img.shields.io/badge/version-v0.3.2-2f6f7e">
  <img alt="Status" src="https://img.shields.io/badge/status-local--first%20prototype-5b6b73">
  <img alt="License" src="https://img.shields.io/badge/license-not%20selected-lightgrey">
</p>

<p align="center">
  <strong>面向团队的 Linux 工作站健康调查平台。</strong><br>
  Quipu 不是指标看板，而是把问题排查流程产品化的本地优先工具。
</p>

<p align="center">
  <a href="README.md">한국어</a> | <a href="README.en.md">English</a> | 简体中文
</p>

---

## 快速了解

Quipu 帮助团队调查多台 Linux 笔记本和开发工作站上的散热压力、重启、
图形/会话错误、存储告警、Wi-Fi 不稳定以及物理摆放变化。

它的目标不是展示更多图表，而是更快回答这些排查问题：

- 团队应该先检查哪台机器？
- 它现在为什么有风险？
- 最可能的原因假设是什么？
- 哪些证据支持或削弱这些假设？
- 人下一步应该检查或调整什么？
- 干预之后，健康状态是否真的改善？
- 同样的模式是否在其他机器上重复出现？

```text
Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report
```

## UI/UX 原则

Quipu 不会一次性展开所有日志和指标。比较当前 dashboard、design system 和
progressive disclosure 模式之后，Quipu 采用 `Command Center` 方式：始终
围绕一个事件展开，并优先回答四个问题：

- 现在应该检查什么？
- 为什么重要？
- 下一步应该做什么？
- 需要什么证据才能确认问题已改善？

详细证据默认保持紧凑，在鼠标靠近、键盘焦点或按钮导航时展开。核心
CTA 固定为 `Review evidence`、`Record action` 和 `Verify result`，让下一步
操作保持清晰。

CPU package、Load Average、NVMe 等核心指标不会只显示孤立数字。每个
metric 卡片会用韩文解释并保留英文技术术语，同时说明时间窗口、解读方式
和下一步检查。例如 Load 会明确说明它是 Linux 1 分钟 load average，而不是
瞬时 CPU 使用率。

创作者和版本信息只保留在顶部小型 metadata chip 中。大型 creator/reference
图片区域因为不能直接帮助调查判断，已从工作界面移除。

## 为什么需要 Quipu

开发机器的问题很少只来自单个指标。CPU 温度、内核日志、GPU 驱动告警、
SSD 状态、Wi-Fi 质量、系统更新、启动历史、工作负载和桌面物理环境都
可能相互叠加。

Quipu 将传感器值、系统事件和人工干预组织成调查记录：

- 当前状态
- 事件时间线
- 原因假设
- 支持证据与反证
- 下一步检查项
- 已采取的操作
- 干预前后验证
- 适合团队阅读的报告

## 差异化

1. **调查优先，指标其次**
   Quipu 从机器、事件或团队问题出发，只展示解释问题所需的指标。

2. **结论必须连接证据**
   每个发现都应该包含支持证据、反证、置信度和原始来源引用。

3. **团队级模式记忆**
   Quipu 面向模型、内核、GPU 驱动、SSD、Wi-Fi 设备、工作负载和物理摆放
   等维度寻找重复问题。

4. **干预验证**
   Quipu 记录抬高笔记本、修改电源配置、更新驱动等操作，并比较干预前后
   的健康窗口。

5. **只读、本地优先的信任边界**
   第一版必须能安全运行在团队设备上：只读 agent、自托管存储、最小日志
   摘录，并且没有远程修复命令。

## 当前状态

Quipu 仍是早期本地优先原型。

已实现：

- FastAPI ingest API
- SQLite WAL 持久化
- 基于规则的 fleet overview
- 确定性的示例设备数据
- Investigation queue/detail API
- 只读 one-shot Linux collector
- 调查项 intervention 记录
- intervention 前后验证结果
- Vite React 调查优先 UI
- Command Center 首屏与 hover/focus 展开面板
- 每个核心 metric 的韩文说明、英文技术术语、时间窗口、解读方式和下一步检查 tooltip
- 小型 Made by、About、Version metadata chip
- 覆盖 server、collector、web 的 GitHub Actions CI

下一步方向：

- supervised local agent 形式的 collector
- 按型号、内核、驱动、存储、Wi-Fi、工作负载和物理环境探索团队模式
- 角色感知的团队流程、redaction 控制和 retention policy

## 快速开始

运行带示例数据的本地 API 服务：

```bash
scripts/dev-server.sh
```

另开一个终端运行 Web UI：

```bash
cd apps/web
npm install
npm run dev
```

打开：

```text
http://127.0.0.1:5173
```

## Collector

collector 是一次性 Linux 信号读取器。它不需要 root 权限，不执行修复命令，
也不会上传完整 raw log。

输出本地 observation batch：

```bash
cd apps/collector
python -m venv .venv
. .venv/bin/activate
pip install -e .
quipu-collector
```

发送一个 batch 到本地 Quipu server：

```bash
quipu-collector --server-url http://127.0.0.1:8000 --token dev-local-token
```

## 架构

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

MVP 边界：

- 默认自托管
- 只读采集
- 不执行远程命令
- 不自动修复
- 不依赖云服务
- 不作为完整 raw-log 仓库

## 验证

Server:

```bash
cd apps/server
. .venv/bin/activate
pytest -v
```

Collector:

```bash
cd apps/collector
python -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
pytest -v
```

Web:

```bash
cd apps/web
npm test
npm run build
```

## 仓库结构

```text
apps/
  collector/     只读 one-shot Linux observation collector
  server/        FastAPI API、SQLite persistence、rule-based analysis
  web/           Vite React UI
docs/
  superpowers/   产品决策、设计、计划和 dashboard
fixtures/
  ingest/        确定性的示例 health batch
scripts/
  dev-server.sh  本地 seeded API server
```

## 关键文档

- [Project dashboard](docs/superpowers/DASHBOARD.md)
- [Decision log](docs/superpowers/DECISION_LOG.md)
- [Roadmap](docs/superpowers/ROADMAP.md)
- [Ship checklist](docs/superpowers/SHIP_CHECKLIST.md)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## 安全边界

当前和近期默认值：

- 只读数据采集
- 自托管存储
- 最小日志摘录
- 不执行远程命令
- 不自动修复
- 没有证据链接时，AI 结论不具备权威性

## 许可证

尚未选择许可证。在明确添加许可证之前，不要假定拥有再分发权利。
