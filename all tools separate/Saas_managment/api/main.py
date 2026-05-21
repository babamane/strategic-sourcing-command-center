"""FastAPI entrypoint for the SaaS spend processing layer."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.routers import forecast, ghost, health, mail, reclamation, renewal, triggers, trueup, utilization
from api.routers import pipeline as pipeline_router
from processing.context_builder import build_context

from db.connection import initialize_database
initialize_database()

app = FastAPI(title="SaaS Spend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def context_middleware(request: Request, call_next):
    # Skip context building for pipeline management routes
    if request.url.path.startswith("/v1/pipeline") or request.url.path.startswith("/api/v1/pipeline"):
        return await call_next(request)

    raw = request.query_params.get("vendor")
    vendor = raw.strip() if raw else None
    if vendor == "":
        vendor = None
    request.state.ctx = build_context(vendor=vendor, version=None)
    response = await call_next(request)
    return response


app.include_router(health.router, tags=["health"])
app.include_router(trueup.router, tags=["trueup"])
app.include_router(ghost.router, tags=["ghost"])
app.include_router(reclamation.router, tags=["reclamation"])
app.include_router(utilization.router, tags=["utilization"])
app.include_router(renewal.router, tags=["renewal"])
app.include_router(forecast.router, tags=["forecast"])
app.include_router(triggers.router)
app.include_router(mail.router)
app.include_router(pipeline_router.router, prefix="/v1")
