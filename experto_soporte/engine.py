from typing import List, Dict, Any
from pydantic import BaseModel, Field

# --- Modelos de Datos del Dominio (HECHOS) ---

class Sintomas(BaseModel):
    """Define los hechos (inputs) que el usuario puede reportar en la interfaz."""
    # Problemas de Aplicación
    app_lenta_o_congela: bool = Field(False)
    app_cierra_inesperadamente: bool = Field(False)
    
    # Problemas de Instalación/Sistema
    instalacion_o_actualizacion_fallida: bool = Field(False)
    pantalla_azul_o_negra_reciente: bool = Field(False)
    
    # Problemas de Hardware/Drivers
    periferico_no_detectado: bool = Field(False)

# --- Motor de Inferencia (Reglas SI... ENTONCES... Avanzadas y Jerárquicas) ---

def motor_reglas(sintomas: Sintomas) -> Dict[str, Any]:
    """
    Aplica las reglas lógicas y el conocimiento experto para generar un diagnóstico
    y sugerencias de solución, incluyendo la justificación (Regla 3).
    """
    recomendaciones: List[str] = []
    justificacion_regla: str = ""
    diagnostico_principal: str = "DESCONOCIDO" # Inicializar con un valor por defecto

    # 1. Regla de Máxima Prioridad: Fallo Crítico (Corrupción Total / Triple Síntoma Grave)
    # Si hay BSOD y además problemas de aplicación, se asume corrupción grave del OS.
    if sintomas.pantalla_azul_o_negra_reciente and (sintomas.app_cierra_inesperadamente or sintomas.instalacion_o_actualizacion_fallida):
        justificacion_regla = "Detección de BSOD/Bloqueo Crítico junto con fallos de software. Esto indica una alta probabilidad de CORRUPCIÓN en el kernel del sistema o un conflicto de drivers esenciales de bajo nivel."
        recomendaciones.append("Diagnóstico CRÍTICO: El problema es de nivel Sistema Operativo/Drivers. Se requiere una acción de recuperación profunda.")
        recomendaciones.append("Reiniciar en Modo Seguro y ejecutar la 'Reparación de Inicio' o 'Restauración del Sistema' a un punto anterior estable.")
        recomendaciones.append("Si falla, considere una reinstalación limpia del sistema operativo o el uso de medios de recuperación.")
        diagnostico_principal = "CORRUPCION_SISTEMA_CRITICA"
        
    # 2. Regla de Conflicto de Aplicaciones/Recursos (App + Instalación Fallida)
    # Indica que un cambio reciente (update/instalación) ha roto otra app o el sistema.
    elif (sintomas.app_lenta_o_congela or sintomas.app_cierra_inesperadamente) and sintomas.instalacion_o_actualizacion_fallida:
        justificacion_regla = "Una aplicación está fallando tras un intento de instalación o actualización. Esto sugiere un CONFLICTO directo de librerías (DLL Hell) o de versiones de software."
        recomendaciones.append("Diagnóstico: Conflicto de software o falta de recursos tras un cambio reciente.")
        recomendaciones.append("Revertir o desinstalar la última aplicación instalada que coincide con el momento de la falla.")
        recomendaciones.append("Utilizar la herramienta 'msconfig' para deshabilitar temporalmente los programas de inicio y aislar el conflicto.")
        diagnostico_principal = "CONFLICTO_DE_SOFTWARE_O_LIBRERIAS"

    # 3. Regla de Corrupción de Aplicación Específica (Cierre Inesperado)
    # La app muere sola sin BSOD ni instalación fallida, es corrupción local.
    elif sintomas.app_cierra_inesperadamente:
        justificacion_regla = "El cierre inesperado de una aplicación sin evidencia de fallos del sistema generalmente apunta a CORRUPCIÓN interna de los archivos de la aplicación o errores de memoria específicos."
        recomendaciones.append("Diagnóstico: La aplicación está corrupta, obsoleta o tiene un error de memoria.")
        recomendaciones.append("Reinstalar la aplicación limpiando el caché (si es posible) y actualizando a la última versión disponible del desarrollador.")
        recomendaciones.append("Verificar los requisitos mínimos de RAM/CPU, ya que puede ser una limitación de recursos.")
        diagnostico_principal = "REINSTALAR_APLICACION_LIMPIANDO_CACHE"

    # 4. Regla de Instalación Fallida (Problema de Permisos o Pre-requisito)
    elif sintomas.instalacion_o_actualizacion_fallida:
        justificacion_regla = "El proceso de instalación falló solo. Esto suele ser un problema de PERMISOS insuficientes o que falta un pre-requisito (ej. .NET Framework, Visual C++ Redistributable)."
        recomendaciones.append("Diagnóstico: Problemas de permisos o pre-requisitos.")
        recomendaciones.append("Intentar la instalación nuevamente ejecutando el archivo como 'Administrador'.")
        recomendaciones.append("Desactivar temporalmente el antivirus o firewall antes de reintentar.")
        recomendaciones.append("Instalar manualmente los pre-requisitos de software comunes.")
        diagnostico_principal = "REINTENTAR_COMO_ADMINISTRADOR"
    
    # 5. Regla de Rendimiento o Bloqueo Simple (App Lenta/Congelada)
    elif sintomas.app_lenta_o_congela:
        justificacion_regla = "La lentitud o congelación es el síntoma más común de FUGA DE MEMORIA o sobrecarga de la CPU por procesos en segundo plano."
        recomendaciones.append("Diagnóstico: Sobrecarga temporal de recursos o fuga de memoria.")
        recomendaciones.append("Cerrar la aplicación con el Administrador de Tareas o simplemente reiniciarla para liberar memoria.")
        recomendaciones.append("Revisar el Administrador de Tareas para identificar y finalizar procesos con alto consumo de recursos.")
        diagnostico_principal = "FINALIZAR_TAREA_Y_REINICIAR_APP"
        
    # 6. Regla de Periféricos Desconocidos
    elif sintomas.periferico_no_detectado:
        justificacion_regla = "Un periférico no detectado es un problema directo de DRIVERS (Controladores) o del puerto físico (hardware) donde está conectado."
        recomendaciones.append("Diagnóstico: Problema de detección de hardware o falta de drivers.")
        recomendaciones.append("Desconectar y reconectar el periférico en otro puerto USB (aísla el problema del puerto).")
        recomendaciones.append("Ir al Administrador de Dispositivos y 'Actualizar Controlador' o 'Reinstalar' el dispositivo para forzar la detección.")
        diagnostico_principal = "ACTUALIZAR_DRIVER_O_PUERTO"

    else:
        # Regla de respaldo/default
        justificacion_regla = "No se reportaron síntomas específicos. Se asume que la falla es intermitente o desconocida."
        recomendaciones.append("No se detectaron síntomas específicos. La acción más segura para resolver fallos intermitentes y limpiar la memoria es un reinicio completo del equipo.")
        diagnostico_principal = "REINICIAR_SISTEMA_SIMPLE"

    return {
        "diagnostico_principal": diagnostico_principal,
        "justificacion_regla": justificacion_regla,
        "detalles_recomendaciones": recomendaciones,
    }
