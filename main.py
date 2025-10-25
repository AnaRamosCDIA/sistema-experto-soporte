# main.py
from datetime import datetime
import uvicorn
import uuid
from typing import List, Dict, Any
from pydantic import BaseModel
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Importa la lógica experta y el modelo de datos desde la subcarpeta
from experto_soporte.engine import Sintomas, motor_reglas

# --- SIMULACIÓN DE BASE DE DATOS (Persistencia y Desafío Avanzado) ---
# Almacena el historial de sesiones en memoria RAM.
historial_sesiones: List[Dict[str, Any]] = []

# --- CONFIGURACIÓN DE FASTAPI ---
# Título actualizado
app = FastAPI(
    title="SISTEMA DE SOPORTE TÉCNICO",
    description="Diagnóstico automático para problemas de software: sistema operativo, controladores (drivers) y aplicaciones.",
    version="1.0.0"
)

# Configuración CORS: Crucial para que el frontend funcione al abrir el archivo local.
# Permite que el archivo HTML/JS acceda a la API desde el navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite cualquier origen (necesario para el desarrollo local)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LÓGICA DE PATRONES Y APRENDIZAJE (Desafío Avanzado) ---

def buscar_patrones(sintomas: Sintomas, diagnostico_principal: str) -> Dict[str, Any]:
    """
    Busca en el historial si el diagnóstico principal sugerido falló repetidamente
    para síntomas similares, activando la 'Inteligencia Artificial' de la recomendación.
    Retorna un diccionario con el mensaje de alerta y el conteo de fallos.
    """
    patrones_de_falla = 0
    # Extrae solo los síntomas que el usuario seleccionó (True)
    sintomas_activos = [k for k, v in sintomas.model_dump().items() if v]

    for sesion in historial_sesiones:
        # Añadir verificación de existencia para evitar errores si 'sintomas' no está en un historial antiguo
        if 'sintomas' in sesion:
            sesion_sintomas_activos = [k for k, v in sesion['sintomas'].items() if v]
            
            # Compara si los síntomas son idénticos (usamos sorted para ignorar el orden)
            if sorted(sesion_sintomas_activos) == sorted(sintomas_activos):
                
                # Verifica si el diagnóstico sugerido falló anteriormente y si ya fue evaluado
                if sesion.get('diagnostico_original') == diagnostico_principal and sesion.get('resultado') == 'FALLIDO':
                    patrones_de_falla += 1
    
    # Umbral de activación de la alerta de patrón (IA)
    # Se activa si ya hay 2 fallos previos (el tercer intento)
    if patrones_de_falla >= 2:
        return {
            "alerta_activa": True,
            "conteo": patrones_de_falla,
            "mensaje_notificacion": f"Se detectaron {patrones_de_falla} fallos previos similares.",
        }
    
    return {"alerta_activa": False, "conteo": 0, "mensaje_notificacion": "No se detectó patrón de falla."}

# Archivo JSON donde se guardarán los reportes
JSON_FILE = "reportes_problemas.json"

# Modelo de datos
class Reporte(BaseModel):
    descripcion: str

# Crear archivo JSON si no existe
if not os.path.exists(JSON_FILE):
    try:
        with open(JSON_FILE, "w") as f:
            json.dump([], f)
    except Exception:
        # No hace falta levantar la excepción aquí, pero es bueno ser explícito
        pass

# --- ENDPOINTS DE LA API ---

@app.post("/reportar_problema")
async def reportar_problema(reporte: Reporte):
    try:
        # Leer JSON existente
        try:
            with open(JSON_FILE, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        # Crear nueva entrada
        nueva_entrada = {
            "id": str(uuid.uuid4()),
            "descripcion": reporte.descripcion,
            "timestamp": datetime.now().isoformat()
        }

        data.append(nueva_entrada)

        # Guardar nuevamente en JSON
        with open(JSON_FILE, "w") as f:
            json.dump(data, f, indent=4)

        return {"mensaje": "Reporte guardado correctamente", "id": nueva_entrada["id"]}

    except Exception as e:
        # Aseguramos que los errores se devuelvan como HTTP 500
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/diagnosticar")
async def diagnosticar_problema(sintomas: Sintomas):
    """
    Recibe los síntomas, ejecuta el motor de reglas (Canvas) y devuelve el diagnóstico.
    """
    # Ejecutar el motor de reglas
    resultado_reglas = motor_reglas(sintomas)
    
    # Guarda el diagnóstico determinado por las reglas como 'original'
    diagnostico_original = resultado_reglas["diagnostico_principal"]
    justificacion_regla = resultado_reglas["justificacion_regla"]
    recomendaciones_reglas = resultado_reglas["detalles_recomendaciones"]
    sintomas_activos_dict = sintomas.model_dump()
    
    # Ejecutar la lógica de patrones (IA)
    alerta_ia_data = buscar_patrones(sintomas, diagnostico_original)
    ia_activa = alerta_ia_data["alerta_activa"]
    
    # Ajuste de recomendación si la IA dispara la alerta
    if ia_activa:
        # La IA solo cambia la recomendación final.
        recomendaciones_finales = ["Contactarse con un técnico especializado"]
        diagnostico_accion_final = "CONSULTAR_TECNICO_ESPECIALIZADO" 
    else:
        # Aquí se filtra la recomendación de las reglas para eliminar el diagnóstico inicial.
        # En la implementación de engine.py, el primer elemento es el Diagnóstico detallado.
        if recomendaciones_reglas and recomendaciones_reglas[0].startswith("Diagnóstico:"):
            # Se elimina el primer elemento que es el diagnóstico detallado
            recomendaciones_finales = recomendaciones_reglas[1:] 
        else:
            recomendaciones_finales = recomendaciones_reglas
        diagnostico_accion_final = diagnostico_original


    # Crear una nueva sesión de historial
    sesion_id = str(uuid.uuid4())
    nueva_sesion = {
        "id": sesion_id,
        "sintomas": sintomas_activos_dict,
        "diagnostico_original": diagnostico_original,
        "diagnostico_sugerido": diagnostico_accion_final,
        "justificacion_regla": justificacion_regla, 
        "detalles_reglas": recomendaciones_reglas,
        "alerta_ia_data": alerta_ia_data,
        "resultado": "PENDIENTE", 
        "timestamp": datetime.now().isoformat()
    }
    historial_sesiones.append(nueva_sesion)
    
    # Lista de mapeo de síntomas (duplicada aquí ya que no podemos importar del frontend)
    SYMPTOM_MAPPING = [
        {'key': 'app_lenta_o_congela', 'label': 'Aplicación Lenta o Congelada'},
        {'key': 'app_cierra_inesperadamente', 'label': 'Aplicación se Cierra Sola'},
        {'key': 'instalacion_o_actualizacion_fallida', 'label': 'Instalación / Update Fallido'},
        {'key': 'pantalla_azul_o_negra_reciente', 'label': 'Pantalla Azul o Bloqueo Reciente (BSOD)'},
        {'key': 'periferico_no_detectado', 'label': 'Periférico (USB/Cámara) No Detectado'}
    ]

    # Mapeo de keys de síntomas a labels legibles para la UI
    # Este array es el que el frontend usa como 'sintomas_activos'
    sintomas_mapeados = [item['label'] for key, active in sintomas_activos_dict.items() if active 
                         for item in SYMPTOM_MAPPING if item['key'] == key]

    # Preparar respuesta final para el frontend
    respuesta = {
        "sesion_id": sesion_id,
        "sintomas_activos": sintomas_mapeados, # <-- ¡Aseguramos que esto esté aquí!
        "diagnostico_principal": diagnostico_original, # Causa Raíz (para la caja verde)
        "diagnostico_accion_final": diagnostico_accion_final, # Acción final (para los pasos a seguir)
        "justificacion_regla": justificacion_regla, 
        "detalles_recomendaciones": recomendaciones_finales,
        "alerta_ia_data": alerta_ia_data,
        "alerta_ia_activa": ia_activa 
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
                # log the feedback, but do not use print()
                return {"mensaje": f"Feedback registrado ({resultado}) para la sesión {sesion_id}. El historial de patrones se ha actualizado."}

    raise HTTPException(status_code=404, detail="Sesión no encontrada.")

# --- ENDPOINTS DEL PANEL ADMINISTRADOR ---

@app.get("/admin/historial")
async def obtener_historial():
    """Retorna el historial de sesiones en memoria y los reportes de problemas."""
    try:
        with open(JSON_FILE, "r") as f:
            reportes_problemas = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        reportes_problemas = []
        
    return {
        "sesiones_diagnostico": historial_sesiones,
        "reportes_manuales": reportes_problemas
    }

@app.get("/admin/estadisticas")
async def obtener_estadisticas():
    """Genera estadísticas clave del historial de sesiones."""
    total_sesiones = len(historial_sesiones)
    fallidas = sum(1 for s in historial_sesiones if s.get('resultado') == 'FALLIDO')
    exitosas = sum(1 for s in historial_sesiones if s.get('resultado') == 'EXITOSO')
    pendientes = total_sesiones - fallidas - exitosas
    
    # Conteo de diagnósticos principales y síntomas
    conteo_diagnosticos = {}
    conteo_sintomas = {}
    
    for sesion in historial_sesiones:
        diag = sesion.get('diagnostico_sugerido', 'DESCONOCIDO')
        conteo_diagnosticos[diag] = conteo_diagnosticos.get(diag, 0) + 1
        
        # Conteo de síntomas activos (solo keys que son True)
        if 'sintomas' in sesion: # Validación añadida para robustez
            for k, v in sesion['sintomas'].items():
                # Corregir lógica: la clave 'sintomas' en el historial de sesión contiene el diccionario de síntomas bool.
                # Aseguramos que 'v' sea booleano antes de la verificación
                if isinstance(v, bool) and v:
                    conteo_sintomas[k] = conteo_sintomas.get(k, 0) + 1

    return {
        "totales": {
            "sesiones": total_sesiones,
            "fallidas": fallidas,
            "exitosas": exitosas,
            "pendientes": pendientes,
            "tasa_exito": (exitosas / total_sesiones * 100) if total_sesiones > 0 else 0
        },
        "diagnosticos_mas_comunes": dict(sorted(conteo_diagnosticos.items(), key=lambda item: item[1], reverse=True)),
        "sintomas_mas_reportados": dict(sorted(conteo_sintomas.items(), key=lambda item: item[1], reverse=True))
    }

# Script para iniciar el servidor uvicorn si se ejecuta este archivo directamente
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
