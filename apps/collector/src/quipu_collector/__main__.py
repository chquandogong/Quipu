from __future__ import annotations

import argparse
from collections.abc import Callable
from datetime import datetime
import json
from pathlib import Path
import sys
import time
from typing import Any

from quipu_collector.collect import collect_observation, send_observation

CollectFn = Callable[..., dict[str, Any]]
SendFn = Callable[..., dict[str, Any]]
SleepFn = Callable[[float], None]


def _positive_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return parsed


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return parsed


def _write_json(payload: dict[str, Any], *, pretty: bool, stream: Any | None = None) -> None:
    output = stream or sys.stdout
    if pretty:
        json.dump(payload, output, indent=2)
    else:
        json.dump(payload, output, separators=(",", ":"))
    output.write("\n")


def _write_error(error: str, message: str) -> None:
    _write_json({"error": error, "message": message}, pretty=False, stream=sys.stderr)


def main(
    argv: list[str] | None = None,
    *,
    collect: CollectFn = collect_observation,
    send: SendFn = send_observation,
    sleep: SleepFn = time.sleep,
) -> int:
    parser = argparse.ArgumentParser(description="Collect read-only Quipu observation batches")
    parser.add_argument("--root", default="/", help="filesystem root to read, mainly for tests")
    parser.add_argument("--device-id", help="override generated device ID")
    parser.add_argument("--observed-at", help="ISO datetime override")
    parser.add_argument("--server-url", help="Quipu server base URL; prints JSON when omitted")
    parser.add_argument("--token", help="agent token required when --server-url is set")
    parser.add_argument("--once", action="store_true", help="collect exactly once; default without --interval")
    parser.add_argument("--interval", type=_positive_float, help="seconds to sleep between collection runs")
    parser.add_argument("--iterations", type=_positive_int, help="number of collection runs before exiting")
    parser.add_argument("--dry-run", action="store_true", help="print observation batches and skip posting")
    args = parser.parse_args(argv)

    if args.once and args.interval:
        parser.error("--once cannot be combined with --interval")
    if args.once and args.iterations:
        parser.error("--once cannot be combined with --iterations")
    if args.iterations and not args.interval:
        parser.error("--iterations requires --interval")
    if args.server_url and not args.token and not args.dry_run:
        parser.error("--token is required when --server-url is set")

    try:
        observed_at = datetime.fromisoformat(args.observed_at) if args.observed_at else None
    except ValueError:
        parser.error("--observed-at must be an ISO datetime")

    max_iterations = args.iterations or (None if args.interval else 1)
    pretty_output = max_iterations == 1 and not args.interval
    iteration = 0

    try:
        while max_iterations is None or iteration < max_iterations:
            try:
                batch = collect(root=Path(args.root), observed_at=observed_at, device_id=args.device_id)
            except Exception as exc:
                _write_error("collection_failed", str(exc))
                return 1

            if args.server_url and not args.dry_run:
                try:
                    payload = send(batch, server_url=args.server_url, token=args.token)
                except Exception as exc:
                    _write_error("send_failed", str(exc))
                    return 1
            else:
                payload = batch

            _write_json(payload, pretty=pretty_output)
            iteration += 1

            if max_iterations is not None and iteration >= max_iterations:
                break
            if args.interval:
                sleep(args.interval)
            else:
                break
    except KeyboardInterrupt:
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
