
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from backend.app.database import SessionLocal
from backend.app.models import User
from backend.app.schemas.user import UserCreate, UserResponse
from backend.app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

password_hash = PasswordHash.recommended()


# Provide a database session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Register a new user
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    # Check whether this email is already registered
    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    # Hash the password before storing it
    hashed_password = password_hash.hash(user_data.password)

    new_user = User(
        full_name=user_data.full_name,
        email=str(user_data.email),
        password_hash=hashed_password,
        role="patient",
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# Log in and generate an access token
@router.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # Swagger sends the email in the "username" field
    user = (
        db.query(User)
        .filter(User.email == form_data.username)
        .first()
    )

    if not user or not password_hash.verify(
        form_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
