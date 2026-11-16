
from fastapi import Depends, FastAPI

from backend.app.database import Base, engine
from backend.app.models import User, Slot, Appointment

from backend.app.routers.auth import router as auth_router
from backend.app.routers.appointments import router as appointments_router
from backend.app.routers.slots import router as slots_router
from backend.app.routers.admin import router as admin_router

from backend.app.core.security import get_current_user
from backend.app.schemas.user import UserResponse


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MediFlow",
    description="Healthcare Appointment Management System",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(appointments_router)
app.include_router(slots_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {"message": "Welcome to MediFlow API"}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "MediFlow API is running",
    }


@app.get("/auth/me", response_model=UserResponse)
def get_logged_in_user(
    current_user: User = Depends(get_current_user),
):
    return current_user
