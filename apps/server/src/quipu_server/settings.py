from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path(os.environ.get("QUIPU_DATABASE_PATH", "data/quipu.sqlite3"))
    dev_agent_token: str = os.environ.get("QUIPU_DEV_AGENT_TOKEN", "dev-token")
