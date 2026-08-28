# Data Models

The canonical model inventory, relationships, migration revisions, and integrity decisions are documented in [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).

The generated OpenAPI schema at `/openapi.json` is authoritative for request and response objects. SQLAlchemy models live under `backend/app/models`, while Pydantic input/output contracts live under `backend/app/schemas`.
