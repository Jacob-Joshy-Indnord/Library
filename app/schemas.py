from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models import ReservationStatus


class ReservationCreate(BaseModel):
    member_id: int
    tool_id: int
    pickup_day: date


class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    tool_id: int
    pickup_day: date
    status: ReservationStatus
    created_at: datetime


class WaitlistJoin(BaseModel):
    member_id: int


class WaitlistEntryOut(BaseModel):
    id: int
    tool_id: int
    member_id: int
    position: int
    created_at: datetime
