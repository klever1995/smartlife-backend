from fastapi import APIRouter, HTTPException
from app.services.firebase_client import db
from app.models.users import UserCreate, AdminCreate, UserPublic, UserType

router = APIRouter(tags=["Users"])

# Endpoint para registrar un nuevo usuario
@router.post("/register", response_model=UserPublic)
def create_user(user: UserCreate):

    doc_ref = db.collection("users").document(user.username)
    if doc_ref.get().exists:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    data = user.dict()
    doc_ref.set(data)

    data.pop("password")
    return UserPublic(**data)

# Endpoint para registrar un nuevo administrador
@router.post("/admin/create", response_model=UserPublic)
def create_admin(admin: AdminCreate):

    doc_ref = db.collection("users").document(admin.username)
    if doc_ref.get().exists:
        raise HTTPException(status_code=400, detail="El admin ya existe")

    data = admin.dict()
    doc_ref.set(data)

    data.pop("password")
    return UserPublic(**data)

# Endpoint para validar credenciales de acceso
@router.post("/login")
def login(username: str, password: str):

    doc = db.collection("users").document(username).get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user = doc.to_dict()

    if user["password"] != password:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    user.pop("password")
    return user

# Endpoint para obtener un usuario
@router.get("/{username}", response_model=UserPublic)
def get_user(username: str):

    doc = db.collection("users").document(username).get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    data = doc.to_dict()
    data.pop("password")
    return UserPublic(**data)

# Endpoint para obtener todos los usuarios
@router.get("/", response_model=list[UserPublic])
def list_users():

    users_ref = db.collection("users").stream()
    user_list = []

    for doc in users_ref:
        user = doc.to_dict()
        user.pop("password", None)
        user_list.append(UserPublic(**user))

    return user_list
