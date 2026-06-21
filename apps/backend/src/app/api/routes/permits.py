"""Permit layer API — runs all 12 German permit checks for a residential address.

POST /api/v1/advisor/permits  → full PermitMatrix JSON (batch)
GET  /api/v1/advisor/permits/stream → SSE stream, one event per check as it resolves
"""
from __future__ import annotations

import json
import queue
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Any, Iterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.config import get_settings
from app.domain.savings.permit_layer.checks import (
    PermitCheck,
    check_battery_install,
    check_battery_mastr,
    check_denkmal_heatpump,
    check_denkmal_solar,
    check_ev_parking,
    check_ev_weg,
    check_hp_geg,
    check_hp_noise,
    check_mastr,
    check_bplan,
    check_solar_lbo,
    plz_to_bundesland,
)
from app.domain.savings.permit_layer.engine import run_permit_checks

router = APIRouter(prefix="/api/v1/advisor", tags=["permits"])


class PermitIntake(BaseModel):
    building_year: int = 1985
    fuel_type: str = "GAS"
    has_private_parking: bool = False


class PermitRequest(BaseModel):
    address: str
    plz: str
    lat: float          # passed from solar layer — no second geocoding call
    lng: float
    intake: PermitIntake = PermitIntake()


@router.post("/permits")
def run_permits(body: PermitRequest) -> dict[str, Any]:
    """Batch: all 12 permit checks → PermitMatrix JSON.

    lat/lng come from the solar layer (already geocoded) — no extra API call.
    """
    settings = get_settings()
    matrix = run_permit_checks(
        body.address,
        body.plz,
        body.lat,
        body.lng,
        body.intake.model_dump(),
        tavily_api_key=settings.tavily_api_key,
        anthropic_api_key=settings.anthropic_api_key,
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_role_key,
    )
    return asdict(matrix)


@router.get("/permits/stream")
def stream_permits(
    address: str,
    plz: str,
    lat: float,
    lng: float,
    building_year: int = 1985,
    fuel_type: str = "GAS",
    has_private_parking: bool = False,
) -> StreamingResponse:
    """SSE: each of the 12 permit checks streams back as it resolves.

    lat/lng come from the solar layer — pass them as query params.
    Frontend receives one `data: {...}` event per check, in completion order.
    Final event: `data: {"event": "done"}`.
    """
    settings = get_settings()
    bundesland = plz_to_bundesland(plz)
    city = address.split(",")[-1].strip().split()[-1] if "," in address else plz
    q: queue.Queue[PermitCheck | BaseException] = queue.Queue()

    total_checks = 12  # solar_lbo + 2×denkmal + 2×bplan + mastr + ev_parking + ev_weg + hp_geg + hp_noise + 2×battery

    def _submit(pool: ThreadPoolExecutor, fn: Any, *args: Any, **kwargs: Any) -> None:
        def _run() -> None:
            try:
                result = fn(*args, **kwargs)
                if isinstance(result, list):
                    for r in result:
                        q.put(r)
                else:
                    q.put(result)
            except Exception as exc:
                q.put(exc)
        pool.submit(_run)

    def generate() -> Iterator[str]:
        with ThreadPoolExecutor(max_workers=8) as pool:
            _submit(pool, check_solar_lbo, bundesland)
            _submit(pool, check_denkmal_solar, lat, lng, bundesland)
            _submit(pool, check_denkmal_heatpump, lat, lng, bundesland)
            _submit(pool, check_bplan, plz, city, settings.tavily_api_key, settings.anthropic_api_key)
            _submit(pool, check_mastr, plz, settings.supabase_url, settings.supabase_service_role_key, settings.tavily_api_key)
            _submit(pool, check_ev_parking, lat, lng, has_private_parking)
            _submit(pool, check_ev_weg, lat, lng)
            _submit(pool, check_hp_geg, building_year, fuel_type)
            _submit(pool, check_hp_noise, lat, lng)
            _submit(pool, check_battery_install)
            _submit(pool, check_battery_mastr)

            received = 0
            while received < total_checks:
                item = q.get()
                received += 1
                if isinstance(item, BaseException):
                    yield f"data: {json.dumps({'error': str(item)})}\n\n"
                else:
                    yield f"data: {json.dumps(asdict(item))}\n\n"

        yield 'data: {"event": "done"}\n\n'

    return StreamingResponse(generate(), media_type="text/event-stream")
