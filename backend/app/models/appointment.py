
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    __table_args__ = (
        Index(
            "uq_appointments_active_slot",
            "slot_id",
            unique=True,
            postgresql_where=text("status = 'booked'"),
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    slot_id: Mapped[int] = mapped_column(
        ForeignKey("slots.id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="booked",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Connect appointment to its patient
    patient = relationship(
        "User",
        back_populates="appointments",
    )

    # Connect appointment to its slot
    slot = relationship(
        "Slot",
        back_populates="appointments",
    )
