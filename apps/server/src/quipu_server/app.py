from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3
from threading import Lock

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware

from quipu_server.analysis import build_fleet_overview, build_investigation_detail, build_investigation_queue
from quipu_server.contracts import InterventionIn, ObservationBatchIn
from quipu_server.db import connect, initialize
from quipu_server.repository import (
    ingest_batch,
    list_device_snapshots,
    list_interventions_for_item,
    list_observations_for_intervention,
    record_intervention,
)
from quipu_server.settings import Settings


def create_app(
    *,
    database_path: Path | None = None,
    dev_agent_token: str | None = None,
) -> FastAPI:
    settings = Settings()
    db_path = database_path or settings.database_path
    token = dev_agent_token or settings.dev_agent_token
    conn = initialize(connect(db_path))
    db_lock = Lock()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            app.state.conn.close()

    app = FastAPI(title="Quipu Server", version="0.5.0", lifespan=lifespan)
    app.state.conn = conn
    app.state.db_lock = db_lock
    app.state.dev_agent_token = token

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Quipu-Agent-Token"],
    )

    def get_conn() -> Iterator[sqlite3.Connection]:
        with app.state.db_lock:
            yield app.state.conn

    def require_agent_token(x_quipu_agent_token: str | None = Header(default=None)) -> None:
        if x_quipu_agent_token != app.state.dev_agent_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid agent token")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/ingest/batches", status_code=status.HTTP_201_CREATED)
    def ingest_observation_batch(
        batch: ObservationBatchIn,
        response: Response,
        _: None = Depends(require_agent_token),
        db: sqlite3.Connection = Depends(get_conn),
    ) -> dict[str, int | bool]:
        result = ingest_batch(db, batch)
        if not result.inserted:
            response.status_code = status.HTTP_200_OK
        return {
            "inserted": result.inserted,
            "metrics_inserted": result.metrics_inserted,
            "events_inserted": result.events_inserted,
        }

    @app.get("/api/fleet/overview")
    def fleet_overview(db: sqlite3.Connection = Depends(get_conn)) -> dict:
        snapshots = list_device_snapshots(db)
        return build_fleet_overview(snapshots)

    @app.get("/api/investigations/queue")
    def investigation_queue(db: sqlite3.Connection = Depends(get_conn)) -> dict:
        snapshots = list_device_snapshots(db)
        return {"items": build_investigation_queue(snapshots)}

    @app.get("/api/investigations/{item_id}")
    def investigation_detail(item_id: str, db: sqlite3.Connection = Depends(get_conn)) -> dict:
        snapshots = list_device_snapshots(db)
        interventions = list_interventions_for_item(db, item_id)
        intervention_windows = {
            intervention["id"]: list_observations_for_intervention(db, intervention) for intervention in interventions
        }
        detail = build_investigation_detail(
            snapshots,
            item_id,
            interventions=interventions,
            intervention_windows=intervention_windows,
        )
        if detail is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="investigation not found")
        return detail

    @app.post("/api/investigations/{item_id}/interventions", status_code=status.HTTP_201_CREATED)
    def create_intervention(
        item_id: str,
        intervention: InterventionIn,
        db: sqlite3.Connection = Depends(get_conn),
    ) -> dict:
        snapshots = list_device_snapshots(db)
        detail = build_investigation_detail(snapshots, item_id)
        if detail is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="investigation not found")
        item = detail["item"]
        return record_intervention(
            db,
            investigation_id=item_id,
            device_id=item["device_id"],
            category=item["category"],
            intervention=intervention,
        )

    return app


app = create_app()
