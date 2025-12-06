from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importar routers de cada módulo
from app.routes import user_routes
from app.routes import photos_routes      
from app.routes import recommendations_routes  

# Configurar aplicación FastAPI
app = FastAPI(
    title="SmartFitness API",
    description="Backend de SmartFitness - recibe imágenes, analiza con IA y guarda datos",
    version="1.0.0"
)

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas con sus prefijos
app.include_router(user_routes.router, prefix="/users", tags=["users"])
app.include_router(photos_routes.router, prefix="/photos", tags=["photos"])  
app.include_router(recommendations_routes.router, prefix="/recommendations", tags=["recommendations"])  

@app.get("/")
async def root():
    return {"message": "SmartFitness backend activo"}
