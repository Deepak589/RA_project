from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserPreferencesBase(BaseModel):
    allergies_jsonb: list[str] = Field(default_factory=list)
    dietary_flags_jsonb: list[str] = Field(default_factory=list)
    disliked_foods_jsonb: list[str] = Field(default_factory=list)
    goal_flags_jsonb: list[str] = Field(default_factory=list)
    onboarding_completed: bool = False
    disclaimer_accepted: bool = False
    disclaimer_accepted_at: datetime | None = None


class UserPreferencesCreate(UserPreferencesBase):
    pass


class UserPreferencesResponse(UserPreferencesBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class UserMedicationBase(BaseModel):
    medication_name: str
    schedule_note: str | None = None
    is_active: bool = True


class UserMedicationCreate(UserMedicationBase):
    pass


class UserMedicationCreateRequest(BaseModel):
    medication_name: str = Field(min_length=1)
    dosage: str | None = None
    frequency: str | None = None


class UserMedicationResponse(UserMedicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class AuthenticationSessionBase(BaseModel):
    expires_at: datetime
    revoked_at: datetime | None = None
    last_used_at: datetime | None = None
    user_agent: str | None = None
    ip_address: str | None = None


class AuthenticationSessionCreate(AuthenticationSessionBase):
    refresh_token_hash: str


class AuthenticationSessionResponse(AuthenticationSessionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    refresh_token_hash: str
    issued_at: datetime
    created_at: datetime


class AccountDeletionRequestBase(BaseModel):
    reason: str | None = None
    scheduled_for: datetime


class AccountDeletionRequestCreate(AccountDeletionRequestBase):
    pass


class AccountDeletionRequestResponse(AccountDeletionRequestBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    status: str
    requested_at: datetime
    processed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(max_length=200)
    timezone: str = "UTC"
    role: str = "user"
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=8)
    preferences: UserPreferencesCreate | None = None
    medications: list[UserMedicationCreate] = Field(default_factory=list)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    name: str = Field(min_length=1, max_length=200)
    timezone: str = "UTC"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=72)


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    height: float | None = None
    weight: float | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(max_length=72)
    new_password: str = Field(min_length=8, max_length=72)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None
    preferences: UserPreferencesResponse | None = None
    medications: list[UserMedicationResponse] = Field(default_factory=list)


class UserPreferencesUpdate(BaseModel):
    dietary_flags: list[str] | None = None
    allergies: list[str] | None = None
    goals: list[str] | None = None
    cuisine_preferences: list[str] | None = None
    budget_friendly: bool | None = None


class UserProfileResponse(BaseModel):
    user: UserResponse
    preferences: UserPreferencesResponse
    medications: list[UserMedicationResponse]
