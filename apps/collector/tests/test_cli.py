import json
from pathlib import Path

import pytest

from quipu_collector.__main__ import main


def _batch(batch_id: str = "batch-1") -> dict:
    return {
        "batch_id": batch_id,
        "observed_at": "2026-07-08T00:00:00+00:00",
        "device": {
            "device_id": "device-1",
            "hostname": "test-host",
            "model": None,
            "os_name": "Ubuntu",
            "kernel_version": "6.14.0",
        },
        "metrics": [],
        "events": [],
    }


def test_main_prints_one_shot_batch_by_default(capsys) -> None:
    calls: list[dict] = []

    def fake_collect(**kwargs):
        calls.append(kwargs)
        return _batch()

    exit_code = main(["--root", "/tmp/quipu-test", "--device-id", "device-1"], collect=fake_collect)

    assert exit_code == 0
    assert calls == [{"root": Path("/tmp/quipu-test"), "observed_at": None, "device_id": "device-1"}]
    assert json.loads(capsys.readouterr().out)["batch_id"] == "batch-1"


def test_main_posts_batch_when_server_url_and_token_are_present(capsys) -> None:
    sent: list[dict] = []

    def fake_collect(**kwargs):
        return _batch()

    def fake_send(batch, *, server_url, token):
        sent.append({"batch": batch, "server_url": server_url, "token": token})
        return {"inserted": True, "metrics_inserted": 0, "events_inserted": 0}

    exit_code = main(
        ["--server-url", "http://127.0.0.1:8000", "--token", "dev-token"],
        collect=fake_collect,
        send=fake_send,
    )

    assert exit_code == 0
    assert sent == [
        {
            "batch": _batch(),
            "server_url": "http://127.0.0.1:8000",
            "token": "dev-token",
        }
    ]
    assert json.loads(capsys.readouterr().out)["inserted"] is True


def test_dry_run_prints_batch_and_skips_post_even_with_server_url(capsys) -> None:
    send_calls: list[dict] = []

    def fake_collect(**kwargs):
        return _batch("dry-run-batch")

    def fake_send(batch, *, server_url, token):
        send_calls.append({"batch": batch, "server_url": server_url, "token": token})
        return {"inserted": True}

    exit_code = main(
        ["--server-url", "http://127.0.0.1:8000", "--dry-run"],
        collect=fake_collect,
        send=fake_send,
    )

    assert exit_code == 0
    assert send_calls == []
    assert json.loads(capsys.readouterr().out)["batch_id"] == "dry-run-batch"


def test_interval_mode_runs_multiple_iterations_and_sleeps_between_them(capsys) -> None:
    collect_calls: list[int] = []
    sleep_calls: list[float] = []

    def fake_collect(**kwargs):
        collect_calls.append(len(collect_calls) + 1)
        return _batch(f"batch-{len(collect_calls)}")

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    exit_code = main(
        ["--interval", "30", "--iterations", "2", "--dry-run"],
        collect=fake_collect,
        sleep=fake_sleep,
    )

    assert exit_code == 0
    assert collect_calls == [1, 2]
    assert sleep_calls == [30.0]
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [line["batch_id"] for line in lines] == ["batch-1", "batch-2"]


def test_main_returns_error_json_when_collection_fails(capsys) -> None:
    def fake_collect(**kwargs):
        raise RuntimeError("no readable Linux signals found")

    exit_code = main(["--dry-run"], collect=fake_collect)

    assert exit_code == 1
    error = json.loads(capsys.readouterr().err)
    assert error == {
        "error": "collection_failed",
        "message": "no readable Linux signals found",
    }


def test_offline_buffer_spools_batch_when_send_fails(tmp_path: Path, capsys) -> None:
    def fake_collect(**kwargs):
        return _batch("offline-batch")

    def fake_send(batch, *, server_url, token):
        raise RuntimeError("server unavailable")

    exit_code = main(
        [
            "--server-url",
            "http://127.0.0.1:8000",
            "--token",
            "dev-token",
            "--offline-buffer",
            "--spool-dir",
            str(tmp_path),
        ],
        collect=fake_collect,
        send=fake_send,
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["buffered"] is True
    assert payload["spool_depth"] == 1
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_offline_buffer_flushes_spool_before_current_send(tmp_path: Path, capsys) -> None:
    from quipu_collector.spool import SpoolStore

    SpoolStore(tmp_path, max_batches=10).enqueue(_batch("spooled-batch"))
    sent: list[str] = []

    def fake_collect(**kwargs):
        return _batch("current-batch")

    def fake_send(batch, *, server_url, token):
        sent.append(batch["batch_id"])
        return {"inserted": True}

    exit_code = main(
        [
            "--server-url",
            "http://127.0.0.1:8000",
            "--token",
            "dev-token",
            "--offline-buffer",
            "--spool-dir",
            str(tmp_path),
        ],
        collect=fake_collect,
        send=fake_send,
    )

    assert exit_code == 0
    assert sent == ["spooled-batch", "current-batch"]
    payload = json.loads(capsys.readouterr().out)
    assert payload["inserted"] is True
    assert payload["spool"]["sent"] == 1
    assert payload["spool"]["remaining"] == 0


def test_iterations_require_interval() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--iterations", "2", "--dry-run"], collect=lambda **kwargs: _batch())

    assert exc_info.value.code == 2
