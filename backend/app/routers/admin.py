from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_user, get_db
from backend.app.models import User, Slot


router = APIRouter(prefix="/admin", tags=["Admin"])
password_hash = PasswordHash.recommended()


class DoctorCreate(BaseModel):
    full_name: str
    email: str
    password: str


class AdminSlotCreate(BaseModel):
    start_time: datetime
    end_time: datetime


def require_admin(
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can access this resource.",
        )
    return current_user


@router.post("/doctors", status_code=status.HTTP_201_CREATED)
def create_doctor(
    data: DoctorCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if not data.full_name.strip() or not data.email.strip():
        raise HTTPException(400, "Name and email are required.")

    if len(data.password) < 8:
        raise HTTPException(400, "Password must contain at least 8 characters.")

    email = data.email.strip().lower()

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(409, "An account with this email already exists.")

    doctor = User(
        full_name=data.full_name.strip(),
        email=email,
        password_hash=password_hash.hash(data.password),
        role="doctor",
    )

    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    return {
        "id": doctor.id,
        "full_name": doctor.full_name,
        "email": doctor.email,
        "role": doctor.role,
    }


@router.get("/doctors")
def get_doctors(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    doctors = (
        db.query(User)
        .filter(User.role == "doctor")
        .order_by(User.id.desc())
        .all()
    )

    return [
        {
            "id": doctor.id,
            "full_name": doctor.full_name,
            "email": doctor.email,
            "role": doctor.role,
        }
        for doctor in doctors
    ]


@router.post(
    "/doctors/{doctor_id}/slots",
    status_code=status.HTTP_201_CREATED,
)
def assign_slot_to_doctor(
    doctor_id: int,
    data: AdminSlotCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    doctor = (
        db.query(User)
        .filter(User.id == doctor_id, User.role == "doctor")
        .first()
    )

    if not doctor:
        raise HTTPException(404, "Doctor not found.")

    if data.start_time.tzinfo is None or data.end_time.tzinfo is None:
        raise HTTPException(
            400,
            "Slot times must include a timezone.",
        )

    if data.end_time <= data.start_time:
        raise HTTPException(
            400,
            "End time must be later than start time.",
        )

    if data.start_time <= datetime.now(timezone.utc):
        raise HTTPException(
            400,
            "You can only assign future slots.",
        )

    slot = Slot(
        doctor_id=doctor.id,
        start_time=data.start_time,
        end_time=data.end_time,
    )

    db.add(slot)
    db.commit()
    db.refresh(slot)

    return {
        "message": "Slot assigned successfully.",
        "id": slot.id,
        "doctor_id": slot.doctor_id,
        "doctor_name": doctor.full_name,
        "start_time": slot.start_time,
        "end_time": slot.end_time,
    }