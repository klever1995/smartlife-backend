from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

# Datos para crear una recomendación
class RecommendationCreate(BaseModel):
    username: str
    photo_ids: Optional[List[str]] = None
    interpretations: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Datos para mostrar una recomendación
class RecommendationPublic(BaseModel):
    username: str
    photo_ids: Optional[List[str]] = None
    interpretations: Optional[List[str]] = None
    recommendations: List[str]
    final_recommendation: str
    timestamp: datetime