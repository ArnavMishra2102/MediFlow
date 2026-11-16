
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import exists
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_user, get_db
from backend.app.models import Appointment, Slot, User
from backend.app.schemas.slot import SlotCreate, SlotResponse

router = APIRouter(
    prefix="/slots",
    tags=["Slots"],
)


# CREATE A SLOT
@router.post("/", response_model=SlotResponse, status_code=201)
def create_slot(
    slot_data: SlotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=403,
            detail="Only doctors can create slots",
        )

    if slot_data.end_time <= slot_data.start_time:
        raise HTTPException(
            status_code=400,
            detail="End time must be after start time",
        )

    if slot_data.start_time <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="Slot must be scheduled in the future",
        )

    new_slot = Slot(
        doctor_id=current_user.id,
        start_time=slot_data.start_time,
        end_time=slot_data.end_time,
    )

    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)

    return new_slot


# GET ALL AVAILABLE SLOTS (FOR PATIENTS)
@router.get("/", response_model=list[SlotResponse])
def get_available_slots(
    db: Session = Depends(get_db),
):
    current_time = datetime.now(timezone.utc)

    available_slots = (
        db.query(Slot)
        .filter(
            Slot.start_time > current_time,
            ~exists().where(
                (Appointment.slot_id == Slot.id)
                & (Appointment.status == "booked")
            ),
        )
        .order_by(Slot.start_time)
        .all()
    )

    return available_slots


# GET ALL SLOTS CREATED BY THE LOGGED-IN DOCTOR
@router.get("/my-slots", response_model=list[SlotResponse])
def get_my_slots(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=403,
            detail="Only doctors can view their slots",
        )

    my_slots = (
        db.query(Slot)
        .filter(Slot.doctor_id == current_user.id)
        .order_by(Slot.start_time.desc())
        .all()
    )

    return my_slots


# DELETE A SLOT
@router.delete("/{slot_id}")
def delete_slot(
    slot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=403,
            detail="Only doctors can delete slots",
        )

    slot = (
        db.query(Slot)
        .filter(
            Slot.id == slot_id,
            Slot.doctor_id == current_user.id,
        )
        .first()
    )

    if not slot:
        raise HTTPException(
            status_code=404,
            detail="Slot not found",
        )

    existing_appointment = (
        db.query(Appointment)
        .filter(Appointment.slot_id == slot_id)
        .first()
    )

    if existing_appointment:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a slot with appointment history",
        )

    db.delete(slot)
    db.commit()

    return {
        "message": "Slot deleted successfully",
        "slot_id": slot_id,
    }
