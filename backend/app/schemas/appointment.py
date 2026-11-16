
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AppointmentCreate(BaseModel):
    slot_id: int


class UserSummary(BaseModel):
    id: int
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class SlotSummary(BaseModel):
    id: int
    doctor_id: int
    start_time: datetime
    end_time: datetime

    doctor: UserSummary

    model_config = ConfigDict(from_attributes=True)


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    slot_id: int
    status: str

    patient: UserSummary
    slot: SlotSummary

    model_config = ConfigDict(from_attributes=True)
