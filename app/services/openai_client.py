import os
import base64
from dotenv import load_dotenv
from openai import AzureOpenAI

# Carga de variables de entorno
load_dotenv()

# Cliente de Azure OpenAI
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("OPENAI_API_VERSION")
)

DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# Conviertir imagen a formato base64 para enviar a Openai
def _encode_image_to_data_url(filename: str, image_bytes: bytes) -> tuple[str, str]:
    mime = "image/jpeg" if filename.lower().endswith(("jpg", "jpeg")) else "image/png"
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime};base64,{b64}"
    return mime, data_url

# Analizar una imagen y devolver una descripción breve
def analyze_image_openai(filename: str, image_bytes: bytes) -> str:

    try:
        _, data_url = _encode_image_to_data_url(filename, image_bytes)

        response = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=[
                {
                    "role": "system",
                    "content": "Eres un analizador de imágenes conciso y preciso. Responde con 1-2 líneas, sin listas y sin explicaciones largas."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_url
                            }
                        },
                        {
                            "type": "text",
                            "text": (
                                f"Analiza brevemente la imagen '{filename}'. "
                                "Devuelve **una frase** clara que describa el plato y un **juicio corto** sobre su densidad calórica (ej: 'alta en calorías', 'ligera', 'balanceada'). "
                                "No uses viñetas ni listas. Máximo 1-2 líneas."
                            )
                        }
                    ]
                }
            ],
            max_tokens=120,
            temperature=0.2
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error analizando imagen: {str(e)}"

# Generar una recomendacion basada en las interpretaciones
def generate_daily_recommendation_openai(
    username: str,
    interpretations: list[str],
    user_context: dict | None = None
) -> str:

# Validar que hay interpretaciones
    try:

        if not interpretations:
            return "No hay interpretaciones para generar recomendación."

        interp_text = "\n".join(f"- {i}" for i in interpretations[:20])  

# Contexto a partir de los datos del usuario
        context_parts = []
        if user_context:
            if user_context.get("peso_kg"):
                context_parts.append(f"peso: {user_context['peso_kg']} kg")
            if user_context.get("estatura_cm"):
                context_parts.append(f"estatura: {user_context['estatura_cm']} cm")
            if user_context.get("edad"):
                context_parts.append(f"edad: {user_context['edad']} años")
            if user_context.get("sexo"):
                context_parts.append(f"sexo: {user_context['sexo']}")

        context_str = "; ".join(context_parts) if context_parts else "sin contexto de usuario"

        prompt_text = (
            f"Recomendación para el usuario: {username}\n"
            "Se te entregan las interpretaciones breves de las comidas de un usuario durante el día.\n\n"
            f"Contexto del usuario: {context_str}.\n\n"
            "Interpretaciones:\n"
            f"{interp_text}\n\n"
            "Tarea: Resumir en 3-6 líneas si la dieta del día fue equilibrada o no, dar 3 recomendaciones prácticas y concretas (cada una 1 frase) para mejorar el siguiente día, y una acción prioritaria recomendada ahora (1 frase). "
            "La respuesta debe ser concisa, en lenguaje claro y orientado a la acción. No expliques el razonamiento extenso."
        )

        response = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=[
                {"role": "system", "content": "Eres un nutricionista virtual que da recomendaciones breves y prácticas basadas en descripciones de comidas."},
                {"role": "user", "content": prompt_text}
            ],
            max_tokens=450,
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error generando recomendación: {str(e)}"