from __future__ import annotations

import uuid

from pydantic import BaseModel


class RegionOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    zone: str

    model_config = {"from_attributes": True}
