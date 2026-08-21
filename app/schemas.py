from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MedallioRefreshEvent(BaseModel):
    event_id: str = Field(min_length=8, max_length=200)
    event_type: Literal["medallio.table.refreshed.v1"] = "medallio.table.refreshed.v1"
    run_id: str
    source_table: str = "raw_cygnus.clientes_proyectos"
    status: Literal["SUCCESS"] = "SUCCESS"
    rows_loaded: int = Field(default=0, ge=0)
    watermark: datetime | None = None


class DirectLeadEvent(BaseModel):
    event_id: str
    source_lead_id: str
    person_name: str | None = None
    phone_e164: str | None = None
    project: str | None = None
    opted_in: bool = False
