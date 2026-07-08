from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
import re
from typing import Any


SendFn = Callable[..., dict[str, Any]]


def _safe_file_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    return cleaned.strip("-") or "batch"


class SpoolStore:
    def __init__(self, directory: Path | str, *, max_batches: int) -> None:
        self.directory = Path(directory).expanduser()
        self.max_batches = max_batches

    def _paths(self) -> list[Path]:
        if not self.directory.exists():
            return []
        return sorted(self.directory.glob("*.json"))

    def depth(self) -> int:
        return len(self._paths())

    def enqueue(self, batch: dict[str, Any]) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        observed = _safe_file_part(str(batch.get("observed_at", "unknown-time")))
        batch_id = _safe_file_part(str(batch["batch_id"]))
        target = self.directory / f"{observed}-{batch_id}.json"
        temp = target.with_suffix(".json.tmp")
        temp.write_text(json.dumps(batch, separators=(",", ":")), encoding="utf-8")
        temp.replace(target)
        self._prune()
        return target

    def list_batches(self) -> list[dict[str, Any]]:
        batches: list[dict[str, Any]] = []
        for path in self._paths():
            batches.append(json.loads(path.read_text(encoding="utf-8")))
        return batches

    def _prune(self) -> None:
        paths = self._paths()
        overflow = len(paths) - self.max_batches
        if overflow <= 0:
            return
        for path in paths[:overflow]:
            path.unlink(missing_ok=True)

    def flush(
        self,
        *,
        send: SendFn,
        server_url: str,
        token: str,
        limit: int | None = None,
    ) -> dict[str, int | bool]:
        attempted = 0
        sent = 0
        failed = False
        for path in self._paths():
            if limit is not None and attempted >= limit:
                break
            batch = json.loads(path.read_text(encoding="utf-8"))
            attempted += 1
            try:
                send(batch, server_url=server_url, token=token)
            except Exception:
                failed = True
                break
            path.unlink(missing_ok=True)
            sent += 1
        return {
            "attempted": attempted,
            "sent": sent,
            "remaining": self.depth(),
            "failed": failed,
        }
