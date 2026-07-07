from pathlib import Path

from quipu_server.settings import Settings


def test_settings_uses_local_sqlite_default() -> None:
    settings = Settings()

    assert settings.database_path == Path("data/quipu.sqlite3")
    assert settings.dev_agent_token == "dev-token"
