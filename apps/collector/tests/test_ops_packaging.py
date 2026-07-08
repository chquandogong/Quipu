from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[3]
OPS = ROOT / "apps" / "collector" / "ops"
WINDOWS_OPS = OPS / "windows"
SCRIPTS = ROOT / "scripts"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_systemd_service_runs_read_only_collector_wrapper() -> None:
    service = _read(OPS / "systemd" / "quipu-collector.service")

    assert "[Unit]" in service
    assert "Description=Quipu read-only workstation collector" in service
    assert "After=network-online.target" in service
    assert "[Service]" in service
    assert "Type=oneshot" in service
    assert "EnvironmentFile=/etc/quipu/collector.env" in service
    assert "ExecStart=/usr/local/lib/quipu/quipu-collector-run" in service
    assert "NoNewPrivileges=true" in service
    assert "PrivateTmp=true" in service
    assert "ProtectSystem=full" in service
    assert "WantedBy=multi-user.target" in service


def test_systemd_timer_schedules_collector_every_five_minutes() -> None:
    timer = _read(OPS / "systemd" / "quipu-collector.timer")

    assert "[Timer]" in timer
    assert "OnBootSec=2min" in timer
    assert "OnUnitActiveSec=5min" in timer
    assert "AccuracySec=30s" in timer
    assert "Persistent=true" in timer
    assert "Unit=quipu-collector.service" in timer
    assert "WantedBy=timers.target" in timer


def test_env_example_documents_required_and_optional_settings() -> None:
    env_example = _read(OPS / "collector.env.example")

    assert "QUIPU_SERVER_URL=http://127.0.0.1:8000" in env_example
    assert "QUIPU_AGENT_TOKEN=replace-with-enrollment-token" in env_example
    assert "QUIPU_COLLECTOR_ROOT=/" in env_example
    assert "QUIPU_COLLECTOR_DEVICE_ID=" in env_example
    assert "QUIPU_COLLECTOR_DEVICE_ALIAS=" in env_example
    assert "QUIPU_SPOOL_DIR=/var/lib/quipu/collector-spool" in env_example
    assert "QUIPU_SPOOL_MAX_BATCHES=288" in env_example
    assert "QUIPU_STATE_DIR=/var/lib/quipu/collector-state" in env_example
    assert "dev-token" not in env_example


def test_windows_scheduled_task_packaging_matches_systemd_flow() -> None:
    env_example = _read(WINDOWS_OPS / "collector.env.example.ps1")
    starter = _read(WINDOWS_OPS / "start-quipu-collector.ps1")
    installer = _read(SCRIPTS / "install-collector-scheduled-task.ps1")
    uninstaller = _read(SCRIPTS / "uninstall-collector-scheduled-task.ps1")

    assert "$env:QUIPU_SERVER_URL = \"http://127.0.0.1:8000\"" in env_example
    assert "$env:QUIPU_AGENT_TOKEN = \"replace-with-enrollment-token\"" in env_example
    assert "$env:QUIPU_COLLECTOR_DEVICE_ID = \"\"" in env_example
    assert "$env:QUIPU_COLLECTOR_DEVICE_ALIAS = \"\"" in env_example
    assert "$env:QUIPU_COLLECTOR_INTERVAL = \"300\"" in env_example
    assert "dev-token" not in env_example

    assert "QUIPU_SERVER_URL is required" in starter
    assert "QUIPU_AGENT_TOKEN is required" in starter
    assert "\"--offline-buffer\"" in starter
    assert "\"--interval\"" in starter
    assert "\"--spool-max-batches\"" in starter
    assert "collector already running" in starter
    assert "Start-Process" in starter
    assert "-WindowStyle Hidden" in starter

    assert "Register-ScheduledTask" in installer
    assert "New-ScheduledTaskTrigger -AtLogOn" in installer
    assert "New-ScheduledTaskPrincipal" in installer
    assert "MultipleInstances IgnoreNew" in installer
    assert "Start-ScheduledTask" in installer

    assert "Unregister-ScheduledTask" in uninstaller
    assert "Stop-Process" in uninstaller
    assert "PurgeConfig" in uninstaller


def test_wrapper_validates_required_config_and_builds_safe_args(tmp_path: Path) -> None:
    if shutil.which("bash") is None:
        pytest.skip("bash is required to execute the systemd collector wrapper")

    wrapper = OPS / "bin" / "quipu-collector-run"

    missing = subprocess.run(
        ["bash", str(wrapper)],
        cwd=ROOT,
        env={},
        text=True,
        capture_output=True,
        check=False,
    )
    assert missing.returncode != 0
    assert "QUIPU_SERVER_URL is required" in missing.stderr

    fake_collector = tmp_path / "quipu-collector"
    fake_collector.write_text("#!/usr/bin/env bash\nprintf '<%s>\\n' \"$@\"\n", encoding="utf-8")
    fake_collector.chmod(0o755)

    env = {
        **os.environ,
        "QUIPU_SERVER_URL": "http://127.0.0.1:8000",
        "QUIPU_AGENT_TOKEN": "token-123",
        "QUIPU_COLLECTOR_BIN": str(fake_collector),
        "QUIPU_COLLECTOR_ROOT": "/tmp/quipu-root",
        "QUIPU_COLLECTOR_DEVICE_ID": "device-1",
        "QUIPU_COLLECTOR_DEVICE_ALIAS": "Build laptop",
    }
    result = subprocess.run(
        ["bash", str(wrapper)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "<--root>",
        "</tmp/quipu-root>",
        "<--server-url>",
        "<http://127.0.0.1:8000>",
        "<--token>",
        "<token-123>",
        "<--once>",
        "<--offline-buffer>",
        "<--spool-dir>",
        "</var/lib/quipu/collector-spool>",
        "<--spool-max-batches>",
        "<288>",
        "<--state-dir>",
        "</var/lib/quipu/collector-state>",
        "<--device-id>",
        "<device-1>",
        "<--device-alias>",
        "<Build laptop>",
    ]


def test_ops_scripts_are_syntax_valid_and_support_dry_run() -> None:
    if shutil.which("bash") is None:
        pytest.skip("bash is required to validate the systemd collector scripts")

    scripts = [
        OPS / "bin" / "quipu-collector-run",
        SCRIPTS / "install-collector-systemd.sh",
        SCRIPTS / "uninstall-collector-systemd.sh",
    ]
    for script in scripts:
        syntax = subprocess.run(["bash", "-n", str(script)], text=True, capture_output=True, check=False)
        assert syntax.returncode == 0, syntax.stderr

    install = subprocess.run(
        ["bash", str(SCRIPTS / "install-collector-systemd.sh"), "--dry-run"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert install.returncode == 0
    assert "DRY RUN" in install.stdout
    assert "quipu-collector.service" in install.stdout
    assert "quipu-collector.timer" in install.stdout

    uninstall = subprocess.run(
        ["bash", str(SCRIPTS / "uninstall-collector-systemd.sh"), "--dry-run", "--purge-config"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert uninstall.returncode == 0
    assert "DRY RUN" in uninstall.stdout
    assert "collector.env" in uninstall.stdout
