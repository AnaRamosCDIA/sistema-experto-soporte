from datetime import datetime
import uvicorn
import uuid
from typing import List, Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Importa la lógica experta y el modelo de datos desde la subcarpeta
from experto_soporte.engine import Sintomas, motor_reglas

# --- SIMULACIÓN DE BASE DE DATOS (Persistencia y Desafío Avanzado) ---
# Almacena el historial de sesiones en memoria RAM.
historial_sesiones: List[Dict[str, Any]] = []

# --- CONFIGURACIÓN DE FASTAPI ---
app = FastAPI(
    title="Sistema Experto de Soporte Técnico",
    description="Motor de Inferencia y Persistencia para el diagnóstico de software.",
    version="1.0.0"
)

# Configuración CORS: Crucial para que el frontend funcione al abrir el archivo local.
# Permite que el archivo .jsx acceda a la API desde el navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite cualquier origen (necesario para el desarrollo local)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LÓGICA DE PATRONES Y APRENDIZAJE (Desafío Avanzado) ---

def buscar_patrones(sintomas: Sintomas, diagnostico_principal: str) -> List[str]:
    """
    Busca en el historial si el diagnóstico principal sugerido falló repetidamente
    para síntomas similares, activando la 'Inteligencia Artificial' de la recomendación.
    """
    patrones_de_falla = 0
    # Extrae solo los síntomas que el usuario seleccionó (True)
    sintomas_activos = [k for k, v in sintomas.model_dump().items() if v]

    for sesion in historial_sesiones:
        sesion_sintomas_activos = [k for k, v in sesion['sintomas'].items() if v]
        
        # Compara si los síntomas son idénticos (usamos sorted para ignorar el orden)
        if sorted(sesion_sintomas_activos) == sorted(sintomas_activos):
            
            # Verifica si el diagnóstico sugerido falló anteriormente
            if sesion.get('diagnostico_sugerido') == diagnostico_principal and sesion.get('resultado') == 'FALLIDO':
                patrones_de_falla += 1

    alerta_ia = []
    # Umbral de activación de la alerta de patrón (IA)
    if patrones_de_falla >= 2:
        alerta_ia.append(
            f"🚨 ALERTA DE PATRÓN (IA): Se detectaron {patrones_de_falla} fallos previos con este diagnóstico. "
            "Esto sugiere que la solución superficial no es suficiente. Se recomienda proceder directamente a una reinstalación o restauración."
        )
    return alerta_ia

# --- ENDPOINTS DE LA API ---

@app.post("/diagnosticar")
async def diagnosticar_problema(sintomas: Sintomas):
    """
    Recibe los síntomas, ejecuta el motor de reglas (Canvas) y devuelve el diagnóstico.
    """
    # Ejecutar el motor de reglas
    resultado_reglas = motor_reglas(sintomas)
    diagnostico_principal = resultado_reglas["diagnostico_principal"]
    
    # Ejecutar la lógica de patrones (IA)
    alerta_ia = buscar_patrones(sintomas, diagnostico_principal)

    # Crear una nueva sesión de historial
    sesion_id = str(uuid.uuid4())
    nueva_sesion = {
        "id": sesion_id,
        "sintomas": sintomas.model_dump(),
        "diagnostico_sugerido": diagnostico_principal,
        "detalles_reglas": resultado_reglas["detalles_recomendaciones"],
        "alerta_ia": alerta_ia,
        "resultado": "PENDIENTE", 
        "timestamp": datetime.now().isoformat()
    }
    historial_sesiones.append(nueva_sesion)
    
    # Preparar respuesta final para el frontend
    respuesta = {
        "sesion_id": sesion_id,
        "diagnostico_principal": diagnostico_principal,
        "detalles_recomendaciones": resultado_reglas["detalles_recomendaciones"],
        "alerta_ia": alerta_ia
    }
    return respuesta


@app.post("/feedback/{sesion_id}")
async def registrar_feedback(sesion_id: str, resultado: str):
    """
    Recibe el feedback del usuario (EXITOSO o FALLIDO) para alimentar la lógica de patrones.
    """
    resultado = resultado.upper()
    
    for sesion in historial_sesiones:
        if sesion["id"] == sesion_id:
            if sesion["resultado"] == "PENDIENTE":
                sesion["resultado"] = resultado
                return {"mensaje": f"Feedback registrado ({resultado}) para la sesión {sesion_id}."}

    return {"mensaje": "Error: Sesión no encontrada."}, 404