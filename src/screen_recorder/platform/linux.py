#!/usr/bin/env python3
# src/screen_recorder/platform/linux.py

"""
Funcionalidades específicas para la plataforma Linux.
Este módulo contiene código optimizado para sistemas Linux.
"""

import os
import sys
import subprocess
from typing import List, Dict, Optional, Any, Tuple

def get_ffmpeg_command_args(config: Dict[str, Any], output_filename: str) -> List[str]:
    """
    Genera argumentos de comando FFmpeg optimizados para Linux.
    
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
    
    # 1. Entrada de Video (x11grab)
    # Obtener tamaño de pantalla
    try:
        # Usar xdpyinfo si está disponible
        display_info = subprocess.check_output(["xdpyinfo"], text=True)
        dimensions_line = [line for line in display_info.split('\n') 
                           if "dimensions:" in line][0]
        resolution = dimensions_line.split("dimensions:")[1].strip().split()[0]
        width, height = resolution.split("x")
    except (subprocess.SubprocessError, IndexError, ValueError):
        # Fallback a valores comunes
        width, height = "1920", "1080"
        print(f"No se pudo detectar resolución de pantalla. Usando {width}x{height}")
    
    cmd.extend([
        "-f", "x11grab",
        "-framerate", str(framerate),
        "-video_size", f"{width}x{height}",
        "-i", ":0.0",  # Capturar pantalla principal
    ])
    
    video_input_index = 0  # x11grab es la entrada 0
    
    # 2. Entrada de Audio (pulse/alsa)
    audio_inputs = []
    next_audio_index = 1  # El siguiente índice después del video
    
    # Micrófono
    if config.get("record_audio_mic", True):
        mic_device = config.get("audio_mic_device_name")
        if mic_device:
            cmd.extend(["-f", "pulse", "-i", mic_device])
        else:
            # Usar dispositivo por defecto
            cmd.extend(["-f", "pulse", "-i", "default"])
        
        audio_inputs.append({"index": next_audio_index, "type": "mic"})
        next_audio_index += 1
        print(f"Añadiendo entrada de micrófono (índice: {audio_inputs[-1]['index']})")
    
    # Audio del sistema (loopback)
    if config.get("record_audio_loopback", True):
        # En PulseAudio, el monitor se puede acceder como "monitor_de_dispositivo"
        loopback_device = config.get("audio_loopback_device_name")
        
        if not loopback_device:
            # Intentar encontrar automáticamente el monitor de salida por defecto
            try:
                output = subprocess.check_output(
                    ["pactl", "list", "short", "sources"], 
                    text=True
                )
                for line in output.splitlines():
                    if "monitor" in line.lower():
                        loopback_device = line.split()[1]
                        break
            except subprocess.SubprocessError:
                loopback_device = None
        
        if loopback_device:
            cmd.extend(["-f", "pulse", "-i", loopback_device])
            audio_inputs.append({"index": next_audio_index, "type": "loopback"})
            next_audio_index += 1
            print(f"Añadiendo entrada de audio del sistema: {loopback_device} (índice: {audio_inputs[-1]['index']})")
        else:
            print("No se pudo encontrar dispositivo loopback para audio del sistema")
    
    # 3. Códecs y mapeo
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
        print("Configurando FFmpeg sin audio")
    elif len(audio_inputs) == 1:
        # Una sola fuente de audio
        audio_index = audio_inputs[0]["index"]
        cmd.extend(["-map", f"{audio_index}:a"])
        cmd.extend(["-c:a", audio_codec, "-b:a", audio_bitrate])
        print(f"Configurando FFmpeg con 1 fuente de audio (índice: {audio_index})")
    elif len(audio_inputs) == 2:
        # Mezclar las dos fuentes de audio
        idx1 = audio_inputs[0]["index"]
        idx2 = audio_inputs[1]["index"]
        filter_complex = f"[{idx1}:a][{idx2}:a]amix=inputs=2:duration=longest[aout]"
        cmd.extend(["-filter_complex", filter_complex])
        cmd.extend(["-map", "[aout]"])  # Mapear la salida del filtro
        cmd.extend(["-c:a", audio_codec, "-b:a", audio_bitrate])
        print(f"Configurando FFmpeg con 2 fuentes de audio (índices: {idx1}, {idx2}), mezclando con amix")
    
    # 4. Opciones finales y archivo de salida
    cmd.extend(["-y", output_filename])
    
    return cmd

def get_audio_devices() -> Dict[str, List[Dict[str, Any]]]:
    """
    Obtiene información sobre dispositivos de audio en Linux.
    
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
        # Intentar obtener dispositivos con pactl (PulseAudio)
        output = subprocess.check_output(
            ["pactl", "list", "short", "sources"], 
            text=True
        )
        
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                device_id = parts[0]
                device_name = parts[1]
                
                device_info = {
                    "id": device_id,
                    "name": device_name,
                    "description": " ".join(parts[2:]) if len(parts) > 2 else device_name
                }
                
                if "monitor" in device_name.lower():
                    result["loopback"].append(device_info)
                else:
                    result["input"].append(device_info)
        
        # Obtener dispositivos de salida
        output = subprocess.check_output(
            ["pactl", "list", "short", "sinks"], 
            text=True
        )
        
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                device_id = parts[0]
                device_name = parts[1]
                
                device_info = {
                    "id": device_id,
                    "name": device_name,
                    "description": " ".join(parts[2:]) if len(parts) > 2 else device_name
                }
                
                result["output"].append(device_info)
                
    except (subprocess.SubprocessError, FileNotFoundError):
        print("No se pudo obtener información de dispositivos de audio con PulseAudio")
        
        # Intentar con arecord/aplay (ALSA) como fallback
        try:
            output = subprocess.check_output(
                ["arecord", "-l"], 
                text=True
            )
            
            # Parsing básico de la salida de arecord
            for line in output.splitlines():
                if line.startswith("card "):
                    parts = line.split(":")
                    if len(parts) >= 2:
                        device_info = {
                            "id": parts[0].strip(),
                            "name": parts[1].strip(),
                            "description": parts[1].strip()
                        }
                        result["input"].append(device_info)
            
            # Para dispositivos de salida
            output = subprocess.check_output(
                ["aplay", "-l"], 
                text=True
            )
            
            for line in output.splitlines():
                if line.startswith("card "):
                    parts = line.split(":")
                    if len(parts) >= 2:
                        device_info = {
                            "id": parts[0].strip(),
                            "name": parts[1].strip(),
                            "description": parts[1].strip()
                        }
                        result["output"].append(device_info)
                        
        except (subprocess.SubprocessError, FileNotFoundError):
            print("No se pudo obtener información de dispositivos de audio con ALSA")
    
    return result

def setup_audio_loopback() -> Optional[str]:
    """
    Configura un dispositivo de loopback para capturar audio del sistema en Linux.
    Intenta configurar PulseAudio para habilitar la captura del audio del sistema.
    
    Returns:
        Optional[str]: Nombre del dispositivo loopback configurado o None si falló.
    """
    # En Linux con PulseAudio, los monitores de salida suelen estar ya disponibles
    try:
        output = subprocess.check_output(
            ["pactl", "list", "short", "sources"], 
            text=True
        )
        
        # Buscar monitores existentes
        for line in output.splitlines():
            if "monitor" in line.lower():
                device_name = line.split()[1]
                print(f"Dispositivo loopback encontrado: {device_name}")
                return device_name
                
        print("No se encontraron dispositivos de monitor. Intentando configurar uno...")
        
        # Obtener el dispositivo de salida por defecto
        output = subprocess.check_output(
            ["pactl", "info"], 
            text=True
        )
        
        default_sink = None
        for line in output.splitlines():
            if "Default Sink:" in line:
                default_sink = line.split(":")[1].strip()
                break
        
        if default_sink:
            monitor_name = f"{default_sink}.monitor"
            print(f"Monitor del dispositivo de salida por defecto: {monitor_name}")
            return monitor_name
    
    except subprocess.SubprocessError:
        print("Error al configurar el loopback de audio")
    
    return None

def get_display_info() -> Dict[str, Any]:
    """
    Obtiene información sobre las pantallas conectadas en Linux.
    
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
        # Intentar usar xrandr para obtener información de pantalla
        output = subprocess.check_output(
            ["xrandr", "--query"], 
            text=True
        )
        
        current_display = None
        
        for line in output.splitlines():
            # Líneas que comienzan con un nombre de pantalla
            if " connected " in line:
                parts = line.split()
                display_name = parts[0]
                is_primary = "primary" in line
                
                # Buscar resolución y posición
                resolution_part = line.split("connected")[1].strip()
                width, height = 0, 0
                position_x, position_y = 0, 0
                
                if is_primary:
                    result["primary"] = display_name
                
                # Parsear resolución y posición
                for part in resolution_part.split():
                    if "x" in part and "+" in part:
                        # Formato típico: 1920x1080+0+0
                        resolution = part.split("+")[0]
                        width, height = map(int, resolution.split("x"))
                        position_parts = part.split(resolution)[1]
                        position_x, position_y = map(int, position_parts.lstrip("+").split("+"))
                        break
                
                display_info = {
                    "name": display_name,
                    "primary": is_primary,
                    "width": width,
                    "height": height,
                    "position_x": position_x,
                    "position_y": position_y
                }
                
                result["displays"].append(display_info)
                
                # Actualizar dimensiones totales
                result["total_width"] = max(result["total_width"], position_x + width)
                result["total_height"] = max(result["total_height"], position_y + height)
    
    except (subprocess.SubprocessError, FileNotFoundError):
        print("No se pudo obtener información de pantalla con xrandr")
        
        # Usar un fallback simple
        try:
            # Intentar con xdpyinfo
            output = subprocess.check_output(["xdpyinfo"], text=True)
            dimensions_line = [line for line in output.split('\n') 
                              if "dimensions:" in line][0]
            resolution = dimensions_line.split("dimensions:")[1].strip().split()[0]
            width, height = map(int, resolution.split("x"))
            
            result["displays"].append({
                "name": "default",
                "primary": True,
                "width": width,
                "height": height,
                "position_x": 0,
                "position_y": 0
            })
            
            result["primary"] = "default"
            result["total_width"] = width
            result["total_height"] = height
            
        except (subprocess.SubprocessError, IndexError, ValueError):
            # Último recurso: valores predeterminados
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
    # Código de prueba para funciones específicas de Linux
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
        print(f"  {device['name']}: {device['description']}")
    
    print(f"Dispositivos de salida: {len(audio_devices['output'])}")
    for device in audio_devices['output']:
        print(f"  {device['name']}: {device['description']}")
    
    print(f"Dispositivos loopback: {len(audio_devices['loopback'])}")
    for device in audio_devices['loopback']:
        print(f"  {device['name']}: {device['description']}")
    
    print("\n=== Loopback de Audio ===")
    loopback_device = setup_audio_loopback()
    if loopback_device:
        print(f"Dispositivo loopback configurado: {loopback_device}")
    else:
        print("No se pudo configurar un dispositivo loopback")
    
    print("\n=== Ejemplo de comando FFmpeg ===")
    config = {
        "video_framerate": 30,
        "video_quality": "medium",
        "record_audio_mic": True,
        "record_audio_loopback": True
    }
    
    cmd = get_ffmpeg_command_args(config, "/tmp/test_recording.mp4")
    print("ffmpeg " + " ".join(cmd))