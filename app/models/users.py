from pydantic import BaseModel, EmailStr, Field
from enum import Enum


# Tipo de roles
class UserType(str, Enum):
    admin = "admin"
    user = "user"

# Datos para registrar un administrador
class AdminCreate(BaseModel):
    username: str
    password: str
    type: UserType = UserType.admin

# Datos para registrar un usuario
class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr
    peso_kg: float = Field(..., gt=0)
    estatura_cm: float = Field(..., gt=0)
    edad: int = Field(..., gt=0)
    sexo: str = Field(..., pattern="^(M|F)$")
    type: UserType = UserType.user

# Datos para mostrar un usuario
class UserPublic(BaseModel):
    username: str
    email: str | None = None
    type: UserType
    peso_kg: float | None = None
    estatura_cm: float | None = None
    edad: int | None = None
    sexo: str | None = None
