from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.firebase_client import db
from app.services.openai_client import analyze_image_openai
from app.services.cloudinary_client import cloudinary
from app.models.photos import FoodPhotoCreate, FoodPhotoPublic
from datetime import datetime, timedelta
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

# Endpoint para subir la imagen y guardar metadatos
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

    try:
        # Obtener la hora local para timestamp correcto
        timestamp_local = datetime.now()  
        # Guardar metadatos en Firestore
        doc_ref = db.collection("photos").document()
        photo_data = FoodPhotoCreate(
            username=username,
            meal_type=meal_type,
            timestamp=timestamp_local,
            interpretation=interpretation
        ).dict()
        photo_data["image_url"] = image_url
        doc_ref.set(photo_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando metadatos en Firestore: {str(e)}")

    return FoodPhotoPublic(**photo_data)


# Endpoint para obtener las fotos de un usuario
@router.get("/{username}", response_model=list[FoodPhotoPublic])
def get_photos(username: str):
    photos_ref = db.collection("photos").where("username", "==", username).stream()
    photo_list = []

    for doc in photos_ref:
        data = doc.to_dict()
        photo_list.append(FoodPhotoPublic(**data))

    # Ordenar las fotos de forma descendente
    photo_list.sort(key=lambda x: x.timestamp)

    return photo_list

# Endpoint para eliminar fotos
@router.delete("/delete-by-date/{username}")
async def delete_by_date(username: str, date: str):
    try:

        target_date_str = date  
        
        deleted_photos = 0
        deleted_recommendations = 0
        
        # Borrar fotos de Firestore y Cloudinary 
        photos_ref = db.collection("photos") \
                      .where("username", "==", username)
        
        photos = photos_ref.stream()
        for doc in photos:
            photo_data = doc.to_dict()
            photo_time = photo_data.get("timestamp")
            
            if photo_time:
                photo_date_str = photo_time.strftime("%Y-%m-%d")
                
                if photo_date_str == target_date_str:
                    if "image_url" in photo_data:
                        try:
                            url_parts = photo_data["image_url"].split("/")
                            public_id = url_parts[-1].split(".")[0]
                            folder = f"smartfitness/{username}"
                            full_public_id = f"{folder}/{public_id}"
                            cloudinary.uploader.destroy(full_public_id)
                        except Exception as e:
                            print(f"Error borrando de Cloudinary: {e}")
                    
                    doc.reference.delete()
                    deleted_photos += 1
        
        recs_ref = db.collection("recommendations") \
                    .where("username", "==", username)
        
        recs = recs_ref.stream()
        for doc in recs:
            rec_data = doc.to_dict()
            rec_time = rec_data.get("timestamp")
            
            if rec_time:
                rec_date_str = rec_time.strftime("%Y-%m-%d")
                if rec_date_str == target_date_str:
                    doc.reference.delete()
                    deleted_recommendations += 1
        
        return {
            "success": True,
            "deleted_photos": deleted_photos,
            "deleted_recommendations": deleted_recommendations,
            "message": f"Borrados {deleted_photos} fotos y {deleted_recommendations} recomendaciones del {date}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error borrando datos: {str(e)}")