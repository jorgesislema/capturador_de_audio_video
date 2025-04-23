# src/screen_recorder/core/config_manager.py

import json
import os
import appdirs
import sys

# Importar utils para obtener defaults (si es necesario, opcional)
# from . import audio_utils

APP_NAME = "ScreenRecorderApp"
APP_AUTHOR = "ScreenRecorderDev"

try:
    config_dir = appdirs.user_config_dir(APP_NAME, APP_AUTHOR)
except Exception as e:
    print(f"Error al obtener directorio de configuración de appdirs: {e}", file=sys.stderr)
    config_dir = os.path.join(os.path.expanduser("~"), f".{APP_NAME.lower()}_config")

config_file = os.path.join(config_dir, "config.json")

# --- Configuración por Defecto Actualizada ---
DEFAULT_CONFIG = {
    "output_dir": None,
    "ffmpeg_path": None,
    # Nuevas claves de audio
    "record_audio_mic": True,           # Grabar micrófono por defecto: Sí
    "audio_mic_device_name": None,      # Usar dispositivo por defecto si es None
    "record_audio_loopback": True,      # Grabar audio sistema por defecto: Sí
    "audio_loopback_device_name": None, # Intentar detectar por defecto si es None
    # Futuras: format, quality, framerate, etc.
}

def ensure_config_dir_exists() -> bool:
    """Asegura que el directorio de configuración exista."""
    try:
        os.makedirs(config_dir, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error al crear directorio de configuración '{config_dir}': {e}", file=sys.stderr)
        return False

def load_config() -> dict:
    """
    Carga la configuración desde el archivo JSON. Combina con valores por defecto.
    """
    current_defaults = DEFAULT_CONFIG.copy()
    # Opcional: Podríamos intentar obtener nombres de dispositivo por defecto aquí
    # si los valores en DEFAULT_CONFIG son None, pero es mejor hacerlo en Recorder
    # para tener la info más actualizada al iniciar la app.

    if not os.path.exists(config_file):
        print(f"Archivo de configuración no encontrado en '{config_file}'. Usando valores por defecto.")
        return current_defaults

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        loaded_config = current_defaults # Empezar con defaults actualizados
        if isinstance(config_data, dict):
            # Sobrescribir defaults solo con las claves presentes en el archivo
            for key in current_defaults: # Iterar sobre claves de default
                if key in config_data:
                    loaded_config[key] = config_data[key]
        else:
             print(f"Advertencia: El archivo '{config_file}' no es un JSON válido. Usando defaults.", file=sys.stderr)
             return current_defaults

        print(f"Configuración cargada desde '{config_file}': {loaded_config}")
        return loaded_config
    except (FileNotFoundError, json.JSONDecodeError, TypeError, OSError) as e:
        print(f"Error al cargar config desde '{config_file}': {e}. Usando defaults.", file=sys.stderr)
        return current_defaults

def save_config(config_data: dict) -> bool:
    """
    Guarda el diccionario de configuración proporcionado en el archivo JSON.
    Solo guarda claves que existen en DEFAULT_CONFIG.
    """
    if not ensure_config_dir_exists():
        return False

    try:
        # Filtrar para guardar solo las claves conocidas
        config_to_save = {key: config_data.get(key) for key in DEFAULT_CONFIG if key in config_data}

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_to_save, f, indent=4, ensure_ascii=False)
        print(f"Configuración guardada en '{config_file}': {config_to_save}")
        return True
    except (OSError, TypeError) as e:
        print(f"Error al guardar config en '{config_file}': {e}", file=sys.stderr)
        return False