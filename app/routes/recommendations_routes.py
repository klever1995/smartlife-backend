from fastapi import APIRouter, HTTPException
from app.services.firebase_client import db
from app.services.openai_client import generate_daily_recommendation_openai
from app.models.recommendations import RecommendationCreate, RecommendationPublic
from datetime import datetime
from typing import Optional

router = APIRouter(tags=["Recommendations"])

# Endpoint para generar una recomendación sin guardar
@router.get("/recommend/{username}", response_model=RecommendationPublic)
def generate_recommendation(username: str):
    interpretations_today = []
    photo_ids_today = []

    try:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        photos_ref = db.collection("photos") \
                       .where("username", "==", username) \
                       .where("timestamp", ">=", today_start).stream()

        for doc in photos_ref:
            photo_data = doc.to_dict()
            if "interpretation" in photo_data and photo_data["interpretation"]:
                interpretations_today.append(photo_data["interpretation"])
                photo_ids_today.append(doc.id)

    except Exception as e:
        print(f"Error buscando fotos del día: {e}")
        raise HTTPException(status_code=500, detail="Error al buscar fotos del usuario")

    if not interpretations_today:
        raise HTTPException(status_code=400, detail="No hay fotos interpretadas hoy para generar recomendación")

    # Cargar datos del usuario
    user_context = None
    try:
        user_doc = db.collection("users").document(username).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            user_context = {
                "peso_kg": user_data.get("peso_kg"),
                "estatura_cm": user_data.get("estatura_cm"),
                "edad": user_data.get("edad"),
                "sexo": user_data.get("sexo")
            }
    except Exception as e:
        print(f"Error cargando datos del usuario: {e}")

    final_text = generate_daily_recommendation_openai(
        username=username,
        interpretations=interpretations_today,
        user_context=user_context
    )

    lines = [line.strip() for line in (final_text or "").splitlines() if line.strip()]
    rec_list = lines if lines else [final_text]

    # Retornamos la recomendación sin guardarla
    return RecommendationPublic(
        username=username,
        photo_ids=photo_ids_today,
        interpretations=interpretations_today,
        recommendations=rec_list,
        final_recommendation=final_text or "",
        timestamp=datetime.utcnow()
    )


# Endpoint para guardar una recomendación generada
@router.post("/save", response_model=RecommendationPublic)
def save_recommendation(rec: RecommendationCreate, final_recommendation: Optional[str] = None):
    if not rec.interpretations or not rec.recommendations:
        raise HTTPException(status_code=400, detail="Se requiere la recomendación generada para guardar")

    final_text = final_recommendation or rec.recommendations[-1]

    doc_ref = db.collection("recommendations").document()
    data = {
        "username": rec.username,
        "photo_ids": rec.photo_ids or [],
        "interpretations": rec.interpretations,
        "recommendations": rec.recommendations,
        "final_recommendation": final_text,
        "timestamp": datetime.utcnow(),
        "created_at": datetime.utcnow(),
    }
    doc_ref.set(data)

    return RecommendationPublic(**data)

# Endpoint para obtener todas las recomendaciones de un usuario
@router.get("/{username}", response_model=list[RecommendationPublic])
def get_recommendations(username: str):
    recs_ref = db.collection("recommendations").where("username", "==", username).stream()
    rec_list = []
    for doc in recs_ref:
        data = doc.to_dict()
        rec_list.append(RecommendationPublic(**data))
    return rec_list

# Endpoint para obtener una recomendación específica por su ID
@router.get("/id/{doc_id}", response_model=RecommendationPublic)
def get_recommendation_by_id(doc_id: str):
    doc = db.collection("recommendations").document(doc_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")
    data = doc.to_dict()
    return RecommendationPublic(**data)