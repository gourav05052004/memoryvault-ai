from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError

from ..auth.jwt import create_access_token
from ..db.mongo import get_users_collection
from ..dependencies.auth import get_current_user


router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SignUpRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class MessageResponse(BaseModel):
    message: str


class UserProfileResponse(BaseModel):
    id: str
    name: str
    email: str


def _normalize_email(email: str) -> str:
    return email.strip().lower()


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignUpRequest) -> AuthResponse:
    name = payload.name.strip()
    email = _normalize_email(payload.email)
    password = payload.password

    if len(name) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name is too short")
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email")
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    users_collection = get_users_collection()
    users_collection.create_index("email", unique=True)

    password_hash = pwd_context.hash(password)
    now = datetime.now(timezone.utc)

    document = {
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "createdAt": now,
    }

    try:
        insert_result = users_collection.insert_one(document)
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from exc

    token = create_access_token(user_id=str(insert_result.inserted_id), email=email)
    return AuthResponse(access_token=token)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    email = _normalize_email(payload.email)
    password = payload.password

    users_collection = get_users_collection()
    user = users_collection.find_one({"email": email})

    if user is None or not pwd_context.verify(password, str(user.get("password_hash", ""))):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user_id=str(user["_id"]), email=email)
    return AuthResponse(access_token=token)


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
) -> MessageResponse:
    current_password = payload.current_password
    new_password = payload.new_password

    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters",
        )

    if not pwd_context.verify(current_password, str(current_user.get("password_hash", ""))):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if current_password == new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    users_collection = get_users_collection()
    users_collection.update_one(
        {"_id": current_user["_id"]},
        {
            "$set": {
                "password_hash": pwd_context.hash(new_password),
                "updatedAt": datetime.now(timezone.utc),
            }
        },
    )

    return MessageResponse(message="Password changed successfully")


@router.get("/me", response_model=UserProfileResponse)
def get_profile(current_user: dict = Depends(get_current_user)) -> UserProfileResponse:
    return UserProfileResponse(
        id=str(current_user["_id"]),
        name=str(current_user.get("name", "User")),
        email=str(current_user.get("email", "")),
    )
