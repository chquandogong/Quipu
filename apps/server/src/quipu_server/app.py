from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3
from threading import Lock

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware

from quipu_server.analysis import (
    build_fleet_overview,
    build_investigation_detail,
    build_investigation_queue,
    build_pattern_overview,
)
from quipu_server.contracts import EnrollmentCreate, InterventionIn, InvestigationNoteIn, ObservationBatchIn
from quipu_server.db import connect, initialize
from quipu_server.repository import (
    create_agent_token,
    get_schema_info,
    ingest_batch,
    list_agent_tokens,
    list_device_snapshots,
    list_investigation_notes,
    list_interventions_for_item,
    list_observations_for_intervention,
    record_intervention,
    record_investigation_note,
    revoke_agent_token,
    rotate_agent_token,
    validate_agent_token,
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

    app = FastAPI(title="Quipu Server", version="0.14.3", lifespan=lifespan)
    app.state.conn = conn
    app.state.db_lock = db_lock
    app.state.dev_agent_token = token

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ],
        allow_origin_regex=r"^http://(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+):(5173|5174)$",
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Quipu-Agent-Token"],
    )

    def get_conn() -> Iterator[sqlite3.Connection]:
        with app.state.db_lock:
            yield app.state.conn

    def require_dev_token(x_quipu_agent_token: str | None = Header(default=None)) -> None:
        if x_quipu_agent_token != app.state.dev_agent_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid agent token")

    def require_ingest_token(
        db: sqlite3.Connection,
        batch: ObservationBatchIn,
        x_quipu_agent_token: str | None,
    ) -> None:
        if x_quipu_agent_token == app.state.dev_agent_token:
            return
        if x_quipu_agent_token and validate_agent_token(
            db,
            token=x_quipu_agent_token,
            device_id=batch.device.device_id,
        ):
            return
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid agent token")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/ingest/batches", status_code=status.HTTP_201_CREATED)
    def ingest_observation_batch(
        batch: ObservationBatchIn,
        response: Response,
        x_quipu_agent_token: str | None = Header(default=None),
        db: sqlite3.Connection = Depends(get_conn),
    ) -> dict[str, int | bool]:
        require_ingest_token(db, batch, x_quipu_agent_token)
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

    @app.get("/api/admin/schema")
    def schema_info(
        _: None = Depends(require_dev_token),
        db: sqlite3.Connection = Depends(get_conn),
    ) -> dict:
        return get_schema_info(db)

    @app.post("/api/enrollment/tokens", status_code=status.HTTP_201_CREATED)
    def create_enrollment_token(
        enrollment: EnrollmentCreate,
        _: None = Depends(require_dev_token),
        db: sqlite3.Connection = Depends(get_conn),
    ) -> dict:
        return create_agent_token(db, enrollment)

    @app.get("/api/enrollment/tokens")
    def enrollment_tokens(
        _: None = Depends(require_dev_token),
        db: sqlite3.Connection = Depends(get_conn),
    ) -> dict:
        return {"tokens": list_agent_tokens(db)}

    @app.post("/api/enrollment/tokens/{token_id}/rotate")
    def rotate_enrollment_token(
        token_id: int,
        _: None = Depends(require_dev_token),
        db: sqlite3.Connection = Depends(get_conn),
    ) -> dict:
        token = rotate_agent_token(db, token_id)
        if token is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="token not found")
        return token

    @app.post("/api/enrollment/tokens/{token_id}/revoke")
    def revoke_enrollment_token(
        token_id: int,
        _: None = Depends(require_dev_token),
        db: sqlite3.Connection = Depends(get_conn),
    ) -> dict:
        token = revoke_agent_token(db, token_id)
        if token is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="token not found")
        return token

    @app.get("/api/investigations/queue")
    def investigation_queue(db: sqlite3.Connection = Depends(get_conn)) -> dict:
        snapshots = list_device_snapshots(db)
        return {"items": build_investigation_queue(snapshots)}

    @app.get("/api/patterns/overview")
    def pattern_overview(db: sqlite3.Connection = Depends(get_conn)) -> dict:
        snapshots = list_device_snapshots(db)
        return build_pattern_overview(snapshots)

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

    @app.get("/api/investigations/{item_id}/notes")
    def investigation_notes(item_id: str, db: sqlite3.Connection = Depends(get_conn)) -> dict:
        return {"notes": list_investigation_notes(db, item_id)}

    @app.post("/api/investigations/{item_id}/notes", status_code=status.HTTP_201_CREATED)
    def create_investigation_note(
        item_id: str,
        note: InvestigationNoteIn,
        db: sqlite3.Connection = Depends(get_conn),
    ) -> dict:
        snapshots = list_device_snapshots(db)
        detail = build_investigation_detail(snapshots, item_id)
        if detail is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="investigation not found")
        return record_investigation_note(db, investigation_id=item_id, note=note)

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
