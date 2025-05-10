#!/usr/bin/env python3
# src/screen_recorder/utils/logger.py

"""
Sistema de logging para el Capturador de Audio y Video.
Proporciona funcionalidad de registro para las diferentes partes de la aplicación.
"""

import os
import sys
import logging
import appdirs
from datetime import datetime
from typing import Optional

# Configuración básica
APP_NAME = "capturador_de_audio_video"
APP_AUTHOR = "jorge-sislema"

# Niveles de log
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

# Ruta del archivo de log
log_dir = appdirs.user_log_dir(APP_NAME, APP_AUTHOR)

# Asegurar que el directorio de logs exista
if not os.path.exists(log_dir):
    try:
        os.makedirs(log_dir)
    except Exception as e:
        print(f"Error al crear directorio de logs: {e}", file=sys.stderr)

# Nombre del archivo basado en la fecha
log_file = os.path.join(log_dir, f"{APP_NAME}_{datetime.now().strftime('%Y-%m-%d')}.log")

# Formato del log
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Logger principal
app_logger = logging.getLogger(APP_NAME)
app_logger.setLevel(logging.DEBUG)  # Nivel base (se puede filtrar en los handlers)

# Handler para consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Por defecto, mostrar INFO o superior en consola
console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
console_handler.setFormatter(console_formatter)
app_logger.addHandler(console_handler)

# Handler para archivo
try:
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)  # Guardar todos los niveles en el archivo
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    app_logger.addHandler(file_handler)
except Exception as e:
    print(f"No se pudo configurar el archivo de log: {e}", file=sys.stderr)

def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger específico para un componente.
    
    Args:
        name (str): Nombre del componente (e.g., 'gui', 'core.recorder').
        
    Returns:
        logging.Logger: Logger configurado para el componente.
    """
    # Prefijamos con el nombre de la aplicación
    if not name.startswith(APP_NAME):
        name = f"{APP_NAME}.{name}"
    return logging.getLogger(name)

def set_level(level: str, handler_type: Optional[str] = None) -> None:
    """
    Cambia el nivel de log para los handlers especificados.
    
    Args:
        level (str): Nivel de log ('debug', 'info', 'warning', 'error', 'critical').
        handler_type (str, opcional): Tipo de handler ('console', 'file', None para ambos).
    """
    log_level = LOG_LEVELS.get(level.lower())
    if not log_level:
        app_logger.error(f"Nivel de log inválido: {level}")
        return
    
    if handler_type is None or handler_type == 'console':
        console_handler.setLevel(log_level)
        app_logger.info(f"Nivel de log de consola cambiado a: {level.upper()}")
    
    if handler_type is None or handler_type == 'file':
        for handler in app_logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.setLevel(log_level)
                app_logger.info(f"Nivel de log de archivo cambiado a: {level.upper()}")

def get_log_file_path() -> str:
    """
    Devuelve la ruta al archivo de log actual.
    
    Returns:
        str: Ruta al archivo de log.
    """
    return log_file

# Mensajes de inicialización
app_logger.info(f"===== Inicio de sesión: {APP_NAME} =====")
app_logger.info(f"Archivo de log: {log_file}")

if __name__ == "__main__":
    # Código de prueba para el sistema de logging
    logger = get_logger("test")
    
    logger.debug("Este es un mensaje de depuración")
    logger.info("Este es un mensaje informativo")
    logger.warning("Este es un mensaje de advertencia")
    logger.error("Este es un mensaje de error")
    logger.critical("Este es un mensaje crítico")
    
    print(f"Logs guardados en: {get_log_file_path()}")