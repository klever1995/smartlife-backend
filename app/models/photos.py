from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

# Tipos de comida permitidos
class MealType(str, Enum):
    desayuno = "desayuno"
    almuerzo = "almuerzo"
    cena = "cena"
    snack = "snack"               
    comida_extra = "comida_extra"   
    postre = "postre"

# Datos para crear foto
class FoodPhotoCreate(BaseModel):
    username: str
    meal_type: MealType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    interpretation: str | None = None

# Datos para mostrar foto
class FoodPhotoPublic(BaseModel):
    username: str
    meal_type: MealType
    timestamp: datetime
    image_url: str | None = None      
    interpretation: str | None = None  