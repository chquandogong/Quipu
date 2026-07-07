from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

from quipu_collector.collect import collect_observation, send_observation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect one read-only Quipu observation batch")
    parser.add_argument("--root", default="/", help="filesystem root to read, mainly for tests")
    parser.add_argument("--device-id", help="override generated device ID")
    parser.add_argument("--observed-at", help="ISO datetime override")
    parser.add_argument("--server-url", help="Quipu server base URL; prints JSON when omitted")
    parser.add_argument("--token", help="agent token required when --server-url is set")
    args = parser.parse_args(argv)

    observed_at = datetime.fromisoformat(args.observed_at) if args.observed_at else None
    batch = collect_observation(root=Path(args.root), observed_at=observed_at, device_id=args.device_id)

    if args.server_url:
        if not args.token:
            parser.error("--token is required when --server-url is set")
        result = send_observation(batch, server_url=args.server_url, token=args.token)
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    json.dump(batch, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
