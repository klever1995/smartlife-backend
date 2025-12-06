import os
import firebase_admin
from firebase_admin import credentials, firestore

# Configura la ruta del archivo de credenciales de Firebase
cred_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'lifestyle.json')

# Inicializa Firebase solo si no está inicializada
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("Conexión a Firebase exitosa.")
    except Exception as e:
        print("Error al conectar con Firebase:", e)
        raise e

# Cliente de Firestore
db = firestore.client()
