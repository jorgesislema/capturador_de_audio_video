#!/usr/bin/env python3
# src/screen_recorder/platform/windows.py

"""
Funcionalidades específicas para la plataforma Windows.
Este módulo contiene código optimizado para sistemas Windows.
"""

import os
import sys
import subprocess
import platform
import winreg
from typing import List, Dict, Optional, Any, Tuple

def get_ffmpeg_command_args(config: Dict[str, Any], output_filename: str) -> List[str]:
    """
    Genera argumentos de comando FFmpeg optimizados para Windows.
    
    Args:
        config (Dict[str, Any]): Configuración de la aplicación.
        output_filename (str): Ruta del archivo de salida.
        
    Returns:
        List[str]: Lista de argumentos para FFmpeg.
    """
    # --- Configuración (de config o valores por defecto) ---
    framerate = config.get("video_framerate", 30)
    quality_preset = config.get("video_quality", "medium")
    
    # Mapear presets de calidad a parámetros de FFmpeg
    quality_map = {
        "low": {"preset": "ultrafast", "crf": "28"},
        "medium": {"preset": "veryfast", "crf": "23"},
        "high": {"preset": "medium", "crf": "18"}
    }
    
    preset = quality_map.get(quality_preset, quality_map["medium"])
    
    # Códecs
    video_codec = "libx264"
    audio_codec = "aac"
    audio_bitrate = "128k"
    pix_fmt = "yuv420p"  # Necesario para compatibilidad
    
    # --- Construcción del Comando ---
    cmd = []
    
    # 1. Entrada de Video (gdigrab)
    cmd.extend([
        "-f", "gdigrab",
        "-framerate", str(framerate),
        "-i", "desktop",  # Capturar pantalla completa
    ])
    
    video_input_index = 0  # gdigrab es la entrada 0
    
    # 2. Entrada de Audio (dshow)
    audio_inputs = []
    next_audio_index = 1  # El siguiente índice después del video
    
    # Micrófono
    if config.get("record_audio_mic", True):
        mic_device = config.get("audio_mic_device_name")
        if mic_device:
            mic_input_str = f"audio={mic_device}"
            cmd.extend(["-f", "dshow", "-i", mic_input_str])
            audio_inputs.append({"index": next_audio_index, "type": "mic"})
            next_audio_index += 1
            print(f"Añadiendo entrada de Micrófono: {mic_input_str} (Índice: {audio_inputs[-1]['index']})")
        else:
            print("Advertencia: Grabar Micrófono está activado pero no se encontró/configuró dispositivo.")
    
    # Audio del sistema (loopback/"Stereo Mix")
    if config.get("record_audio_loopback", True):
        loopback_device = config.get("audio_loopback_device_name")
        if loopback_device:
            loopback_input_str = f"audio={loopback_device}"
            cmd.extend(["-f", "dshow", "-i", loopback_input_str])
            audio_inputs.append({"index": next_audio_index, "type": "loopback"})
            next_audio_index += 1
            print(f"Añadiendo entrada de Loopback: {loopback_input_str} (Índice: {audio_inputs[-1]['index']})")
        else:
            print("Advertencia: Grabar Loopback está activado pero no se encontró/configuró dispositivo.")
            print("             Asegúrate de que 'Stereo Mix' o similar esté habilitado en Windows.")
    
    # 3. Códecs y Mapeo
    cmd.extend([
        "-c:v", video_codec,
        "-preset", preset["preset"],
        "-crf", preset["crf"],
        "-pix_fmt", pix_fmt
    ])
    
    cmd.extend(["-map", f"{video_input_index}:v"])  # Mapear siempre el video
    
    # Configuración de audio según entradas disponibles
    if not audio_inputs:
        cmd.extend(["-an"])  # Sin audio
        print("Configurando FFmpeg sin audio.")
    elif len(audio_inputs) == 1:
        # Una sola fuente de audio
        audio_index = audio_inputs[0]["index"]
        cmd.extend(["-map", f"{audio_index}:a"])
        cmd.extend(["-c:a", audio_codec, "-b:a", audio_bitrate])
        print(f"Configurando FFmpeg con 1 fuente de audio (Índice: {audio_index}).")
    elif len(audio_inputs) == 2:
        # Mezclar las dos fuentes de audio
        idx1 = audio_inputs[0]["index"]
        idx2 = audio_inputs[1]["index"]
        filter_complex = f"[{idx1}:a][{idx2}:a]amix=inputs=2:duration=longest[aout]"
        cmd.extend(["-filter_complex", filter_complex])
        cmd.extend(["-map", "[aout]"])  # Mapear la salida del filtro
        cmd.extend(["-c:a", audio_codec, "-b:a", audio_bitrate])
        print(f"Configurando FFmpeg con 2 fuentes de audio (Índices: {idx1}, {idx2}), mezclando con amix.")
    
    # 4. Opciones finales y archivo de salida
    cmd.extend(["-y", output_filename])
    
    return cmd

def get_audio_devices() -> Dict[str, List[Dict[str, Any]]]:
    """
    Obtiene información sobre dispositivos de audio en Windows.
    
    Returns:
        Dict[str, List[Dict[str, Any]]]: Diccionario con listas de dispositivos 
                                        separados en 'input', 'output' y 'loopback'.
    """
    result = {
        "input": [],
        "output": [],
        "loopback": []
    }
    
    try:
        # Usar ffmpeg para enumerar dispositivos dshow
        output = subprocess.check_output(
            ["ffmpeg", "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
            stderr=subprocess.STDOUT,
            text=True,
            errors='replace'
        )
        
        lines = output.splitlines()
        device_type = None
        
        for line in lines:
            # Detectar sección de dispositivos
            if "DirectShow audio devices" in line:
                device_type = "audio"
                continue
            elif "DirectShow video devices" in line:
                device_type = "video"
                continue
            
            # Procesar solo líneas de dispositivos de audio
            if device_type == "audio" and "\"" in line:
                # Formato típico: [dshow @ 0000020ad8b92a00] "Nombre del dispositivo"
                try:
                    device_name = line.split("\"")[1]
                    
                    device_info = {
                        "id": device_name,
                        "name": device_name,
                        "description": device_name
                    }
                    
                    # Detectar si es loopback ("Stereo Mix" u otros)
                    loopback_keywords = ["stereo mix", "what u hear", "wave out", "mix", "loopback"]
                    is_loopback = any(keyword in device_name.lower() for keyword in loopback_keywords)
                    
                    if is_loopback:
                        result["loopback"].append(device_info)
                    else:
                        result["input"].append(device_info)
                except Exception as e:
                    print(f"Error al procesar línea de dispositivo: {e}")
    
    except subprocess.SubprocessError as e:
        print(f"Error al enumerar dispositivos DirectShow: {e}")
    
    # Obtener dispositivos de salida de Windows
    try:
        # Enumerar dispositivos de audio de salida usando el registro de Windows
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render") as key:
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    with winreg.OpenKey(key, subkey_name + r"\Properties") as subkey:
                        try:
                            # {a45c254e-df1c-4efd-8020-67d146a850e0},2 es el valor del nombre del dispositivo
                            device_name_value = winreg.QueryValueEx(subkey, "{a45c254e-df1c-4efd-8020-67d146a850e0},2")
                            device_name = device_name_value[0]
                            
                            result["output"].append({
                                "id": subkey_name,
                                "name": device_name,
                                "description": device_name
                            })
                        except WindowsError:
                            pass
                except WindowsError:
                    pass
    except Exception as e:
        print(f"Error al enumerar dispositivos de salida: {e}")
    
    return result

def enable_stereo_mix() -> bool:
    """
    Intenta habilitar el dispositivo Stereo Mix en Windows.
    
    Returns:
        bool: True si se habilitó correctamente, False en caso contrario.
    """
    try:
        # Este es un enfoque simplificado. En la práctica, esto es difícil
        # de hacer programáticamente y podría requerir privilegios elevados.
        print("Intentando habilitar 'Stereo Mix'...")
        
        # Buscar un dispositivo Stereo Mix existente pero deshabilitado
        # Esto requeriría un enfoque más avanzado utilizando APIs nativas de Windows
        # como Core Audio APIs, lo cual está fuera del alcance de este ejemplo simple.
        
        print("Nota: La habilitación automática de Stereo Mix requiere permisos elevados.")
        print("Por favor, habilita 'Stereo Mix' manualmente en la configuración de sonido de Windows:")
        print("1. Haz clic derecho en el icono de sonido en la barra de tareas")
        print("2. Selecciona 'Abrir configuración de sonido'")
        print("3. En 'Dispositivos de entrada', haz clic derecho en un área vacía")
        print("4. Marca 'Mostrar dispositivos deshabilitados'")
        print("5. Habilita 'Stereo Mix' si aparece")
        
        # En una implementación real, se podría intentar ejecutar un comando como:
        # subprocess.run(["powershell", "-Command", "script para habilitar Stereo Mix"], check=True)
        
        return False  # En esta implementación simple, asumimos que falla
    except Exception as e:
        print(f"Error al habilitar Stereo Mix: {e}")
        return False

def get_display_info() -> Dict[str, Any]:
    """
    Obtiene información sobre las pantallas conectadas en Windows.
    
    Returns:
        Dict[str, Any]: Información sobre las pantallas.
    """
    result = {
        "displays": [],
        "primary": None,
        "total_width": 0,
        "total_height": 0
    }
    
    try:
        # En Windows, podemos usar PySide6 para obtener esta información
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QRect
        
        # Necesitamos una instancia de QApplication para esto
        app = QApplication.instance()
        if not app:
            # Crear una instancia temporal
            app = QApplication([])
        
        # Obtener información de todas las pantallas
        screens = app.screens()
        primary_screen = app.primaryScreen()
        
        result["primary"] = primary_screen.name()
        
        for i, screen in enumerate(screens):
            geometry = screen.geometry()
            is_primary = (screen == primary_screen)
            
            display_info = {
                "name": screen.name(),
                "primary": is_primary,
                "width": geometry.width(),
                "height": geometry.height(),
                "position_x": geometry.x(),
                "position_y": geometry.y(),
                "physical_size": {
                    "width_mm": screen.physicalSize().width(),
                    "height_mm": screen.physicalSize().height()
                },
                "device_pixel_ratio": screen.devicePixelRatio()
            }
            
            result["displays"].append(display_info)
            
            # Actualizar dimensiones totales
            result["total_width"] = max(result["total_width"], geometry.x() + geometry.width())
            result["total_height"] = max(result["total_height"], geometry.y() + geometry.height())
            
            if is_primary:
                result["primary"] = screen.name()
    
    except ImportError:
        print("No se pudo importar PySide6. Usando valores predeterminados.")
        
        # Valores predeterminados si no podemos obtener la información real
        result["displays"].append({
            "name": "default",
            "primary": True,
            "width": 1920,
            "height": 1080,
            "position_x": 0,
            "position_y": 0
        })
        
        result["primary"] = "default"
        result["total_width"] = 1920
        result["total_height"] = 1080
    
    return result

if __name__ == "__main__":
    # Código de prueba para funciones específicas de Windows
    if platform.system() != "Windows":
        print("Este módulo está diseñado para ejecutarse en Windows.")
        print(f"Sistema actual detectado: {platform.system()}")
        sys.exit(1)
    
    print("=== Información de Pantalla ===")
    display_info = get_display_info()
    print(f"Pantallas detectadas: {len(display_info['displays'])}")
    print(f"Pantalla primaria: {display_info['primary']}")
    print(f"Dimensiones totales: {display_info['total_width']}x{display_info['total_height']}")
    
    for i, display in enumerate(display_info['displays']):
        print(f"Pantalla {i+1}: {display['name']}")
        print(f"  Resolución: {display['width']}x{display['height']}")
        print(f"  Posición: +{display['position_x']}+{display['position_y']}")
        print(f"  Primaria: {'Sí' if display['primary'] else 'No'}")
    
    print("\n=== Dispositivos de Audio ===")
    audio_devices = get_audio_devices()
    
    print(f"Dispositivos de entrada: {len(audio_devices['input'])}")
    for device in audio_devices['input']:
        print(f"  {device['name']}")
    
    print(f"Dispositivos de salida: {len(audio_devices['output'])}")
    for device in audio_devices['output']:
        print(f"  {device['name']}")
    
    print(f"Dispositivos loopback: {len(audio_devices['loopback'])}")
    for device in audio_devices['loopback']:
        print(f"  {device['name']}")
    
    if not audio_devices['loopback']:
        print("\n=== Intento de habilitación de Stereo Mix ===")
        result = enable_stereo_mix()
        if result:
            print("Stereo Mix habilitado correctamente.")
        else:
            print("No se pudo habilitar Stereo Mix automáticamente.")
    
    print("\n=== Ejemplo de comando FFmpeg ===")
    config = {
        "video_framerate": 30,
        "video_quality": "medium",
        "record_audio_mic": True,
        "record_audio_loopback": True,
        "audio_mic_device_name": audio_devices['input'][0]['name'] if audio_devices['input'] else None,
        "audio_loopback_device_name": audio_devices['loopback'][0]['name'] if audio_devices['loopback'] else None
    }
    
    cmd = get_ffmpeg_command_args(config, "C:\\temp\\test_recording.mp4")
    print("ffmpeg " + " ".join(cmd))