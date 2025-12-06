from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.firebase_client import db
from app.services.openai_client import analyze_image_openai
from app.services.cloudinary_client import cloudinary
from app.models.photos import FoodPhotoCreate, FoodPhotoPublic
from datetime import datetime
import cloudinary.uploader

router = APIRouter(tags=["Photos"])

# Endpoint para interpretar la imagen sin subirla
@router.post("/interpret", response_model=dict)
async def interpret_photo(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        interpretation = analyze_image_openai(file.filename, image_bytes)
        return {"filename": file.filename, "interpretation": interpretation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interpretando imagen: {str(e)}")

# Endpoint para subir la imagen y guardar metadatos, usando la interpretación ya generada
@router.post("/upload", response_model=FoodPhotoPublic)
async def upload_photo(
    username: str = Form(...),
    meal_type: str = Form(...),
    interpretation: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        image_bytes = await file.read()
        # Subir imagen a Cloudinary
        upload_result = cloudinary.uploader.upload(
            image_bytes,
            folder=f"smartfitness/{username}",
            public_id=file.filename.split('.')[0],
            overwrite=True
        )
        image_url = upload_result.get("secure_url")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo imagen a Cloudinary: {str(e)}")

    # Guardar metadatos en Firestore
    doc_ref = db.collection("photos").document()
    photo_data = FoodPhotoCreate(
        username=username,
        meal_type=meal_type,
        timestamp=datetime.utcnow(),
        interpretation=interpretation
    ).dict()
    photo_data["image_url"] = image_url
    doc_ref.set(photo_data)

    return FoodPhotoPublic(**photo_data)

# Endpoint para obtener las fotos de un usuario
@router.get("/{username}", response_model=list[FoodPhotoPublic])
def get_photos(username: str):
    photos_ref = db.collection("photos").where("username", "==", username).stream()
    photo_list = []

    for doc in photos_ref:
        data = doc.to_dict()
        photo_list.append(FoodPhotoPublic(**data))

    return photo_list
