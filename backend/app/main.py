from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import models  # noqa: F401 -- populate complete SQLAlchemy metadata
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.routers import (
    admin,
    ai_coach,
    auth,
    commerce,
    communication,
    competitive,
    identity,
    map_guides,
    organization,
    organizers,
    rankings,
    tournaments,
    transfers,
    websocket,
)
from app.services.regions import seed_regions


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.is_production:
        insecure = {
            "JWT_SECRET_KEY": settings.jwt_secret_key == "CHANGE_ME_IN_PRODUCTION",
            "ANTI_ABUSE_SECRET": settings.anti_abuse_secret == "CHANGE_ME_ANTI_ABUSE",
        }
        missing = [name for name, invalid in insecure.items() if invalid]
        if missing:
            raise RuntimeError(f"Production secrets are not configured: {', '.join(missing)}")
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            seed_regions(db)
    yield


app = FastAPI(
    title=settings.app_name,
    description="Competitive infrastructure for the African Call of Duty: Mobile community.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Device-Fingerprint", "X-Request-ID", "X-Paystack-Signature"],
)

api = settings.api_prefix
app.include_router(auth.router, prefix=api)
app.include_router(identity.router, prefix=api)
app.include_router(organization.router, prefix=api)
app.include_router(organization.teams_router, prefix=api)
app.include_router(organizers.router, prefix=api)
app.include_router(tournaments.router, prefix=api)
app.include_router(tournaments.governance_router, prefix=api)
app.include_router(map_guides.router, prefix=api)
app.include_router(rankings.router, prefix=api)
app.include_router(ai_coach.router, prefix=api)
app.include_router(competitive.router, prefix=api)
app.include_router(commerce.router, prefix=api)
app.include_router(commerce.payments_router, prefix=api)
app.include_router(transfers.router, prefix=api)
app.include_router(communication.notifications_router, prefix=api)
app.include_router(communication.chat_router, prefix=api)
app.include_router(admin.moderation_router, prefix=api)
app.include_router(admin.admin_router, prefix=api)
app.include_router(websocket.router, prefix=api)


@app.get("/health", tags=["operations"])
def health_check():
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok", "service": "codm-squad-hub", "version": app.version}


@app.get(f"{api}/health", include_in_schema=False)
def api_health_check():
    return health_check()
