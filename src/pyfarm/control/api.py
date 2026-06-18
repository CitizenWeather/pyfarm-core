"""FastAPI endpoints for a running ControlRunner."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from pyfarm.control.engine.context import ControlContext


def _elapsed_days(ctx: ControlContext) -> float:
    return (datetime.now(timezone.utc) - ctx.stage_entered_at).total_seconds() / 86400.0


def _is_stale(ts: datetime, threshold_seconds: float = 60.0) -> bool:
    ts_aware = ts if ts.tzinfo is not None else ts.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - ts_aware).total_seconds() > threshold_seconds


def make_app(ctx: ControlContext) -> FastAPI:
    app = FastAPI(title="pyfarm-control", docs_url=None, redoc_url=None)

    @app.get("/status")
    async def status() -> JSONResponse:
        return JSONResponse(_build_status(ctx))

    @app.get("/events")
    async def events(
        since: str | None = Query(default=None)
    ) -> JSONResponse:
        all_events = list(ctx.events)
        if since is not None:
            try:
                cutoff = datetime.fromisoformat(since)
                if cutoff.tzinfo is None:
                    cutoff = cutoff.replace(tzinfo=timezone.utc)
                all_events = [e for e in all_events if e.timestamp > cutoff]
            except ValueError:
                pass
        return JSONResponse([
            {"kind": e.kind, "message": e.message, "timestamp": e.timestamp.isoformat(), **e.data}
            for e in all_events
        ])

    @app.get("/actuators")
    async def actuators() -> JSONResponse:
        return JSONResponse({
            name: {
                "on": state.on,
                "command": state.command if isinstance(state.command, (bool, int, float)) else str(state.command),
                "last_changed": state.last_changed.isoformat(),
                "seconds_in_state": round(state.seconds_in_state(), 1),
            }
            for name, state in ctx.actuator_states.items()
        })

    return app


def _build_status(ctx: ControlContext) -> dict[str, Any]:
    return {
        "run_id": ctx.run_id,
        "spec_name": ctx.spec.metadata.name,
        "current_stage": ctx.current_stage.name,
        "elapsed_days": round(_elapsed_days(ctx), 4),
        "readings": {
            metric: {"value": r.value, "unit": r.unit, "stale": _is_stale(r.timestamp)}
            for metric, r in ctx.readings.items()
        },
        "derived": dict(ctx.derived),
        "recent_events": [
            {"kind": e.kind, "message": e.message, "timestamp": e.timestamp.isoformat()}
            for e in list(ctx.events)[-20:]
        ],
    }
