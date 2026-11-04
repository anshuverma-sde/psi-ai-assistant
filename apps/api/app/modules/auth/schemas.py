import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.modules.organization.schemas import OrganizationOut


class RegisterIn(BaseModel):
    organization_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("organization_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("Organization name must be at least 2 characters")
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserOut(BaseModel):
    id: uuid.UUID
    email: str


class SessionOut(BaseModel):
    user: UserOut
    organization: OrganizationOut
