
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from backend.app.core.security import get_current_user, get_db
from backend.app.models import Appointment, Slot, User
from backend.app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
)

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"],
)


# ==========================================
# HELPER FUNCTION
# ==========================================

# Load appointment along with patient, slot, and doctor details
def get_appointment_with_details(
    db: Session,
    appointment_id: int,
):
    return (
        db.query(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.slot).joinedload(Slot.doctor),
        )
        .filter(Appointment.id == appointment_id)
        .first()
    )


# ==========================================
# 1. BOOK AN APPOINTMENT
# ==========================================

@router.post(
    "/",
    response_model=AppointmentResponse,
    status_code=201,
)
def book_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.role != "patient":
        raise HTTPException(
            status_code=403,
            detail="Only patients can book appointments",
        )

    # Lock the slot while processing the booking
    slot = (
        db.query(Slot)
        .filter(Slot.id == appointment_data.slot_id)
        .with_for_update()
        .first()
    )

    if slot is None:
        raise HTTPException(
            status_code=404,
            detail="Slot not found",
        )

    # Check whether the slot is in the future
    if slot.start_time <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="Cannot book a past or ongoing slot",
        )

    # Check whether the slot is already booked
    existing_appointment = (
        db.query(Appointment)
        .filter(
            Appointment.slot_id == slot.id,
            Appointment.status == "booked",
        )
        .first()
    )

    if existing_appointment:
        raise HTTPException(
            status_code=409,
            detail="This slot is already booked",
        )

    new_appointment = Appointment(
        patient_id=current_user.id,
        slot_id=slot.id,
        status="booked",
    )

    try:
        db.add(new_appointment)
        db.commit()
        db.refresh(new_appointment)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This slot is already booked",
        )

    return get_appointment_with_details(
        db,
        new_appointment.id,
    )


# ==========================================
# 2. GET PATIENT APPOINTMENTS
# ==========================================

@router.get(
    "/my-appointments",
    response_model=list[AppointmentResponse],
)
def get_my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.role != "patient":
        raise HTTPException(
            status_code=403,
            detail="Only patients can view their appointments",
        )

    appointments = (
        db.query(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.slot).joinedload(Slot.doctor),
        )
        .filter(
            Appointment.patient_id == current_user.id
        )
        .order_by(Appointment.created_at.desc())
        .all()
    )

    return appointments


# ==========================================
# 3. CANCEL AN APPOINTMENT
# ==========================================

@router.patch(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse,
)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.role != "patient":
        raise HTTPException(
            status_code=403,
            detail="Only patients can cancel appointments",
        )

    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.patient_id == current_user.id,
        )
        .with_for_update()
        .first()
    )

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found",
        )

    if appointment.status == "cancelled":
        raise HTTPException(
            status_code=400,
            detail="Appointment is already cancelled",
        )

    if appointment.status != "booked":
        raise HTTPException(
            status_code=400,
            detail="Only booked appointments can be cancelled",
        )

    appointment.status = "cancelled"

    try:
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise

    return get_appointment_with_details(
        db,
        appointment.id,
    )


# ==========================================
# 4. RESCHEDULE AN APPOINTMENT
# ==========================================

@router.patch(
    "/{appointment_id}/reschedule",
    response_model=AppointmentResponse,
)
def reschedule_appointment(
    appointment_id: int,
    new_slot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.role != "patient":
        raise HTTPException(
            status_code=403,
            detail="Only patients can reschedule appointments",
        )

    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.patient_id == current_user.id,
        )
        .with_for_update()
        .first()
    )

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found",
        )

    if appointment.status != "booked":
        raise HTTPException(
            status_code=400,
            detail="Only booked appointments can be rescheduled",
        )

    if appointment.slot_id == new_slot_id:
        raise HTTPException(
            status_code=400,
            detail="You are already booked for this slot",
        )

    new_slot = (
        db.query(Slot)
        .filter(Slot.id == new_slot_id)
        .with_for_update()
        .first()
    )

    if new_slot is None:
        raise HTTPException(
            status_code=404,
            detail="New slot not found",
        )

    if new_slot.start_time <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="Cannot reschedule to a past or ongoing slot",
        )

    existing_appointment = (
        db.query(Appointment)
        .filter(
            Appointment.slot_id == new_slot_id,
            Appointment.status == "booked",
        )
        .first()
    )

    if existing_appointment:
        raise HTTPException(
            status_code=409,
            detail="The new slot is already booked",
        )

    appointment.slot_id = new_slot_id

    try:
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to reschedule. The new slot may already be booked.",
        )

    return get_appointment_with_details(
        db,
        appointment.id,
    )


# ==========================================
# 5. GET DOCTOR APPOINTMENTS
# ==========================================

@router.get(
    "/doctor-appointments",
    response_model=list[AppointmentResponse],
)
def get_doctor_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.role != "doctor":
        raise HTTPException(
            status_code=403,
            detail="Only doctors can view their appointments",
        )

    appointments = (
        db.query(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.slot).joinedload(Slot.doctor),
        )
        .join(
            Slot,
            Appointment.slot_id == Slot.id,
        )
        .filter(
            Slot.doctor_id == current_user.id
        )
        .order_by(Appointment.created_at.desc())
        .all()
    )

    return appointments


# ==========================================
# 6. COMPLETE AN APPOINTMENT
# ==========================================

@router.patch(
    "/{appointment_id}/complete",
    response_model=AppointmentResponse,
)
def complete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # Only doctors can complete appointments
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=403,
            detail="Only doctors can complete appointments",
        )

    # Find appointment belonging to this doctor
    appointment = (
        db.query(Appointment)
        .join(
            Slot,
            Appointment.slot_id == Slot.id,
        )
        .filter(
            Appointment.id == appointment_id,
            Slot.doctor_id == current_user.id,
        )
        .with_for_update()
        .first()
    )

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found",
        )

    # Only booked appointments can be completed
    if appointment.status != "booked":
        raise HTTPException(
            status_code=400,
            detail="Only booked appointments can be completed",
        )

    # Appointment must have ended
    current_time = datetime.now(timezone.utc)

    if appointment.slot.end_time > current_time:
        raise HTTPException(
            status_code=400,
            detail="Appointment cannot be completed before its scheduled end time",
        )

    # Update appointment status
    appointment.status = "completed"

    try:
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise

    return get_appointment_with_details(
        db,
        appointment.id,
    )

