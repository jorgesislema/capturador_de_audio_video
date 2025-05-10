#!/usr/bin/env python3
# src/screen_recorder/core/config_manager.py

"""
Gestor de configuración para el Capturador de Audio y Video.
Maneja la carga y guardado de preferencias del usuario.
"""

import os
import json
import appdirs
from typing import Dict, Any, Optional

# Configurar rutas de aplicación
APP_NAME = "capturador_de_audio_video"
APP_AUTHOR = "jorge-sislema"

# Obtener directorio de configuración específico de la plataforma
config_dir = appdirs.user_config_dir(APP_NAME, APP_AUTHOR)
config_file = os.path.join(config_dir, "config.json")

# Configuración por defecto
DEFAULT_CONFIG: Dict[str, Any] = {
    "output_dir": os.path.expanduser("~/Videos"),
    "record_audio_mic": True,
    "record_audio_loopback": True,
    "audio_mic_device_name": None,  # Se detectará automáticamente
    "audio_loopback_device_name": None,  # Se detectará automáticamente
    "ffmpeg_path": None,  # Se buscará en el PATH
    "video_quality": "medium",  # low, medium, high
    "video_framerate": 30,
    "file_format": "mp4"
}

def ensure_config_dir() -> bool:
    """
    Crea el directorio de configuración si no existe.
    
    Returns:
        bool: True si el directorio existe o se creó correctamente, False en caso contrario.
    """
    try:
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        return True
    except Exception as e:
        print(f"Error al crear directorio de configuración: {e}")
        return False

def load_config() -> Dict[str, Any]:
    """
    Carga la configuración desde el archivo JSON.
    Si no existe, crea una configuración por defecto.
    
    Returns:
        Dict[str, Any]: La configuración cargada o por defecto.
    """
    if not os.path.exists(config_file):
        print(f"Archivo de configuración no encontrado en {config_file}.")
        print("Creando configuración por defecto...")
        if ensure_config_dir():
            save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # Asegurar que todos los valores por defecto existan
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = value
                
        return config
    except Exception as e:
        print(f"Error al cargar configuración: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]) -> bool:
    """
    Guarda la configuración en un archivo JSON.
    
    Args:
        config (Dict[str, Any]): La configuración a guardar.
        
    Returns:
        bool: True si se guardó correctamente, False en caso contrario.
    """
    if not ensure_config_dir():
        return False
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        print(f"Configuración guardada en {config_file}")
        return True
    except Exception as e:
        print(f"Error al guardar configuración: {e}")
        return False

def get_config_path() -> str:
    """
    Devuelve la ruta al archivo de configuración.
    
    Returns:
        str: Ruta al archivo de configuración.
    """
    return config_file

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Obtiene un valor específico de la configuración.
    
    Args:
        key (str): La clave del valor a obtener.
        default (Any, opcional): Valor por defecto si no existe la clave.
        
    Returns:
        Any: El valor de la configuración o el valor por defecto.
    """
    config = load_config()
    return config.get(key, default)

def set_config_value(key: str, value: Any) -> bool:
    """
    Establece un valor específico en la configuración y la guarda.
    
    Args:
        key (str): La clave a establecer.
        value (Any): El valor a establecer.
        
    Returns:
        bool: True si se guardó correctamente, False en caso contrario.
    """
    config = load_config()
    config[key] = value
    return save_config(config)

if __name__ == "__main__":
    # Código de prueba para desarrollo
    print(f"Directorio de configuración: {config_dir}")
    print(f"Archivo de configuración: {config_file}")
    
    config = load_config()
    print("Configuración actual:")
    for key, value in config.items():
        print(f"  {key}: {value}")