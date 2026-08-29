from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class AdminUserCreateRequest(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=30)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="CLIENT", min_length=1, max_length=32)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise ValueError("El teléfono no tiene un formato válido")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        requirements = (
            any(char.isupper() for char in value),
            any(char.islower() for char in value),
            any(char.isdigit() for char in value),
            any(not char.isalnum() for char in value),
        )
        if not all(requirements):
            raise ValueError("La contraseña debe incluir mayúsculas, minúsculas, números y un carácter especial")
        return value


class UserUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=2, max_length=100)
    last_name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=7, max_length=30)
    role: str | None = Field(default=None, min_length=1, max_length=32)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise ValueError("El teléfono no tiene un formato válido")
        return normalized


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    role: str
    is_active: bool


class UserPage(BaseModel):
    items: list[UserResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
