#!/usr/bin/env python3
# src/screen_recorder/core/config_manager.py

"""
Gestor de configuración para el Capturador de Audio y Video.
Maneja la carga y guardado de preferencias del usuario.
"""

import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """Gestiona la configuración del grabador de pantalla."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.logger = logging.getLogger('screen_recorder.config')
        
        # Valores por defecto para una grabación de alta calidad
        self.default_config = {
            # Configuración de video
            "video_codec": "libx264",       # Códec H.264 (alta compatibilidad)
            "preset": "medium",             # Balance entre calidad y velocidad
            "crf": "18",                    # Factor de tasa constante (18-23 es alta calidad)
            "framerate": 30,                # Cuadros por segundo
            "pixfmt": "yuv420p",            # Formato de pixel (compatibilidad)
            
            # Configuración de audio
            "audio_codec": "aac",           # Códec de audio AAC (alta compatibilidad)
            "audio_bitrate": "192k",        # Bitrate de audio (calidad alta)
            "record_mic": True,             # Grabar micrófono por defecto
            "record_loopback": True,        # Grabar audio del sistema por defecto
            
            # Configuración de dispositivos (específico de plataforma)
            "mic_device": "",               # Se detectará automáticamente
            "loopback_device": "",          # Se detectará automáticamente
            
            # Configuración de salida
            "output_dir": str(Path.home() / "Videos"),  # Directorio por defecto
            "filename_template": "grabacion_%Y%m%d_%H%M%S.mp4"  # Formato de nombre
        }
        
        # Opcionalmente sobrescribir con archivo externo
        self.config_file = config_file or self._get_default_config_path()
        self.config = self._load_config()
        
    def _get_default_config_path(self) -> str:
        """Obtiene la ruta del archivo de configuración según la plataforma."""
        if os.name == 'nt':  # Windows
            config_dir = os.path.join(os.environ.get('APPDATA', ''), 'ScreenRecorder')
        else:  # Linux/Mac
            config_dir = os.path.join(os.path.expanduser('~'), '.config', 'screen-recorder')
            
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, 'config.json')
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración del archivo, o crea uno nuevo con valores predeterminados."""
        config = self.default_config.copy()
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # Actualizar configuración con valores del usuario
                    config.update(user_config)
                self.logger.info(f"Configuración cargada desde: {self.config_file}")
            else:
                self._save_config(config)
                self.logger.info(f"Configuración predeterminada creada en: {self.config_file}")
        except Exception as e:
            self.logger.error(f"Error al cargar la configuración: {e}")
        
        return config
    
    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Guarda la configuración en el archivo."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Configuración guardada en: {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error al guardar la configuración: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración. Devuelve default si no existe."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Establece un valor de configuración."""
        self.config[key] = value
    
    def save(self) -> bool:
        """Guarda la configuración actual."""
        return self._save_config(self.config)
    
    def reset_to_defaults(self) -> None:
        """Restablece la configuración a valores predeterminados."""
        self.config = self.default_config.copy()
    
    def get_quality_presets(self) -> Dict[str, Dict[str, Any]]:
        """Devuelve presets de calidad predefinidos."""
        return {
            "baja": {
                "video_codec": "libx264",
                "preset": "veryfast",
                "crf": "28",
                "framerate": 15,
                "audio_bitrate": "96k",
            },
            "media": {
                "video_codec": "libx264",
                "preset": "medium",
                "crf": "23",
                "framerate": 30,
                "audio_bitrate": "128k",
            },
            "alta": {
                "video_codec": "libx264",
                "preset": "medium",
                "crf": "18",
                "framerate": 30,
                "audio_bitrate": "192k",
            },
            "ultra": {
                "video_codec": "libx264",
                "preset": "slow",
                "crf": "16",
                "framerate": 60,
                "audio_bitrate": "256k",
            }
        }
    
    def apply_quality_preset(self, preset_name: str) -> bool:
        """Aplica un preset de calidad predefinido."""
        presets = self.get_quality_presets()
        if preset_name in presets:
            for key, value in presets[preset_name].items():
                self.config[key] = value
            return True
        return False

    def get_audio_devices(self) -> Dict[str, list]:
        """
        Obtiene los dispositivos de audio disponibles en el sistema.
        Devuelve un diccionario con listas de micrófonos y dispositivos de loopback.
        """
        import subprocess
        import sys
        
        result = {
            "microphones": [],
            "loopback": []
        }
        
        try:
            if sys.platform == "win32":
                # En Windows, usar ffmpeg para listar dispositivos DirectShow
                cmd = ["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"]
                output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
                
                # Analizar salida para encontrar dispositivos
                audio_section = False
                for line in output.splitlines():
                    if "DirectShow audio devices" in line:
                        audio_section = True
                        continue
                    if audio_section and "Alternative name" in line:
                        device_name = line.split('"')[1]
                        # Estéreo Mix suele ser el dispositivo de loopback
                        if "mix" in device_name.lower() or "loopback" in device_name.lower():
                            result["loopback"].append(device_name)
                        else:
                            result["microphones"].append(device_name)
            
            elif sys.platform.startswith("linux"):
                # En Linux, usar pactl (PulseAudio) para listar dispositivos
                try:
                    cmd = ["pactl", "list", "sources"]
                    output = subprocess.check_output(cmd, text=True)
                    
                    current_device = None
                    for line in output.splitlines():
                        if line.strip().startswith("Name:"):
                            current_device = line.split("Name:")[1].strip()
                        # Buscar descripciones de dispositivos
                        if line.strip().startswith("Description:"):
                            description = line.split("Description:")[1].strip()
                            # Monitor = dispositivo de loopback
                            if "monitor" in current_device.lower():
                                result["loopback"].append(current_device)
                            else:
                                result["microphones"].append(current_device)
                except:
                    # Alternativa: intentar usar ALSA
                    try:
                        cmd = ["arecord", "-L"]
                        output = subprocess.check_output(cmd, text=True)
                        for line in output.splitlines():
                            if not line.startswith(" ") and line != "":
                                if "loopback" in line.lower():
                                    result["loopback"].append(line)
                                else:
                                    result["microphones"].append(line)
                    except:
                        self.logger.error("No se pudieron detectar dispositivos de audio en Linux")
        
        except Exception as e:
            self.logger.error(f"Error al obtener dispositivos de audio: {e}")
        
        return result