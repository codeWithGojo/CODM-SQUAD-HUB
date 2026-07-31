from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app import models  # noqa: F401 — populates Base.metadata
from app.routers import auth, organization

app = FastAPI(
    title="CoDM Squad Hub API",
    description="Backend for the African CoDM competitive platform.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before real launch
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Dev convenience only — use Alembic migrations for real deploys,
    # this is just so the app boots against a fresh empty database.
    Base.metadata.create_all(bind=engine)


app.include_router(auth.router)
app.include_router(organization.router)
app.include_router(organization.teams_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
