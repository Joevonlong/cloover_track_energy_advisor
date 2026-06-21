"""FastAPI application entrypoint.

Owner: Zhou (backend)
Feature ID: F01 (monorepo scaffold) / F17 (api endpoints)

Wires CORS + routers. MUST boot with no business logic present.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.routes import advisor, health, permits, subsidies
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Heimwende Advisor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(advisor.router)
app.include_router(permits.router)
app.include_router(subsidies.router)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """Redirect bare root to the interactive API docs."""
    return RedirectResponse(url="/docs")
