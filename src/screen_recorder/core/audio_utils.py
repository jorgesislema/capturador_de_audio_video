#!/usr/bin/env python3
# src/screen_recorder/core/audio_utils.py

"""
Utilidades para la detección y gestión de dispositivos de audio.
Proporciona funciones para identificar dispositivos de entrada/salida
y especialmente para encontrar dispositivos loopback para grabar audio del sistema.
"""

import sys
import platform
from typing import Dict, List, Optional, Any

try:
    import sounddevice as sd
except ImportError:
    print("Error: No se pudo importar sounddevice. Instale con 'pip install sounddevice'")
    # No fallamos aquí para permitir usar partes de la aplicación sin audio

def get_all_audio_devices() -> List[Dict[str, Any]]:
    """
    Obtiene una lista de todos los dispositivos de audio disponibles.
    
    Returns:
        List[Dict[str, Any]]: Lista de diccionarios con información de los dispositivos.
    """
    try:
        devices = sd.query_devices()
        return devices if isinstance(devices, list) else [devices]
    except Exception as e:
        print(f"Error al obtener dispositivos de audio: {e}")
        return []

def get_default_device_info(kind: str = 'input') -> Optional[Dict[str, Any]]:
    """
    Obtiene información sobre el dispositivo de audio predeterminado.
    
    Args:
        kind (str): 'input' para dispositivo de entrada, 'output' para salida.
    
    Returns:
        Optional[Dict[str, Any]]: Diccionario con información del dispositivo o None si hay error.
    """
    if kind not in ('input', 'output'):
        raise ValueError("'kind' debe ser 'input' o 'output'")
    
    try:
        device_id = sd.default.device[0 if kind == 'input' else 1]
        if device_id is not None:
            device_info = sd.query_devices(device=device_id)
            return device_info
    except Exception as e:
        print(f"Error al obtener dispositivo {kind} predeterminado: {e}")
    
    return None

def print_audio_devices() -> None:
    """Muestra por consola todos los dispositivos de audio disponibles."""
    try:
        devices = get_all_audio_devices()
        print("\n=== Dispositivos de Audio Disponibles ===")
        for i, dev in enumerate(devices):
            # Manejar diferentes tipos de objetos de dispositivo
            if isinstance(dev, dict):
                # Si es un diccionario
                host_api = dev.get('hostapi', 0)
                channels_in = dev.get('max_input_channels', 0)
                channels_out = dev.get('max_output_channels', 0)
                name = dev.get('name', 'Desconocido')
            else:
                # Si es un objeto DeviceList
                try:
                    host_api = getattr(dev, 'hostapi', 0)
                    channels_in = getattr(dev, 'max_input_channels', 0)
                    channels_out = getattr(dev, 'max_output_channels', 0)
                    name = getattr(dev, 'name', 'Desconocido')
                except Exception as e:
                    print(f"Error al acceder a atributos del dispositivo {i}: {e}")
                    continue
            
            default_mark = ""
            
            if i == sd.default.device[0]:
                default_mark += "[Entrada Default] "
            if i == sd.default.device[1]:
                default_mark += "[Salida Default] "
                
            dev_type = []
            if channels_in > 0:
                dev_type.append(f"Entrada ({channels_in} canales)")
            if channels_out > 0:
                dev_type.append(f"Salida ({channels_out} canales)")
                
            print(f"ID: {i}, {default_mark}Nombre: {name}")
            print(f"    Tipo: {', '.join(dev_type)}")
            print(f"    API: {host_api}")
    except Exception as e:
        print(f"Error al imprimir dispositivos de audio: {e}")

def find_loopback_device_info() -> Optional[Dict[str, Any]]:
    """
    Intenta encontrar un dispositivo de loopback para capturar audio del sistema.
    En Windows, busca 'Stereo Mix', 'What U Hear', 'Wave Out', etc.
    En Linux, busca un dispositivo monitor.
    
    Returns:
        Optional[Dict[str, Any]]: Información del dispositivo loopback o None si no se encuentra.
    """
    try:
        devices = get_all_audio_devices()
        
        # Términos de búsqueda para encontrar dispositivos loopback
        search_terms = ['stereo mix', 'what u hear', 'wave out', 'mix', 'loopback']
        
        system = platform.system().lower()
        
        # Búsqueda específica por plataforma
        for device in devices:
            # Comprobar el tipo de device y manejarlo apropiadamente
            if isinstance(device, dict):
                # Si es un diccionario, usamos get() como estaba previsto
                name = device.get('name', '').lower()
                max_input_channels = device.get('max_input_channels', 0)
            else:
                # Si es un objeto DeviceList, accedemos a los atributos directamente
                try:
                    name = getattr(device, 'name', '').lower()
                    max_input_channels = getattr(device, 'max_input_channels', 0)
                except Exception as e:
                    print(f"Error al acceder a atributos del dispositivo: {e}")
                    continue
            
            # En Windows, buscar nombres comunes de loopback
            if system == 'windows':
                if any(term in name for term in search_terms):
                    if max_input_channels > 0:  # Debe tener canales de entrada
                        return device
            
            # En Linux con PulseAudio, buscar dispositivos "Monitor of"
            elif system == 'linux':
                if ('monitor' in name or '.monitor' in name) and max_input_channels > 0:
                    return device
        
        # No se encontró un dispositivo específico
        if system == 'linux':
            print("\nAVISO: No se encontró dispositivo para capturar audio del sistema.")
            print("Para habilitar este dispositivo en Linux:")
            print("1. Abre 'pavucontrol' (Instalalo con: sudo apt install pavucontrol)")
            print("2. Ve a la pestaña 'Dispositivos de entrada'")
            print("3. Cambia 'Mostrar:' a 'Todos los dispositivos de entrada'")
            print("4. Debería aparecer 'Monitor of...' para cada salida de audio")
            print("5. Asegúrate de que no esté silenciado\n")
        elif system == 'windows':
            print("\nAVISO: No se encontró dispositivo para capturar audio del sistema.")
            print("Para habilitar 'Stereo Mix' en Windows:")
            print("1. Haz clic derecho en el icono de sonido en la barra de tareas")
            print("2. Selecciona 'Sonidos' o 'Abrir configuración de sonido'")
            print("3. Ve a 'Administrar dispositivos de audio' o 'Dispositivos de grabación'")
            print("4. Haz clic derecho en un área vacía y marca 'Mostrar dispositivos deshabilitados'")
            print("5. Haz clic derecho en 'Stereo Mix' y selecciona 'Habilitar'\n")
        
        return None
    except Exception as e:
        print(f"Error al buscar dispositivo loopback: {e}")
        return None

def get_device_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Busca un dispositivo de audio por su nombre.
    
    Args:
        name (str): Nombre del dispositivo a buscar.
        
    Returns:
        Optional[Dict[str, Any]]: Información del dispositivo o None si no se encuentra.
    """
    if not name:
        return None
        
    devices = get_all_audio_devices()
    name_lower = name.lower()
    
    for device in devices:
        # Manejar tanto diccionarios como objetos DeviceList
        if isinstance(device, dict):
            device_name = device.get('name', '')
        else:
            try:
                device_name = getattr(device, 'name', '')
            except Exception as e:
                print(f"Error al acceder al nombre del dispositivo: {e}")
                continue
                
        if device_name.lower() == name_lower:
            return device
    
    return None

if __name__ == "__main__":
    # Código de prueba para desarrollo
    print(f"Sistema: {platform.system()}")
    print_audio_devices()
    
    print("\n=== Dispositivo de Entrada Predeterminado ===")
    input_dev = get_default_device_info('input')
    if input_dev:
        print(f"Nombre: {input_dev.get('name')}")
    else:
        print("No se encontró dispositivo de entrada predeterminado.")
    
    print("\n=== Dispositivo Loopback ===")
    loopback_dev = find_loopback_device_info()
    if loopback_dev:
        print(f"Encontrado: {loopback_dev.get('name')}")
    else:
        print("No se encontró dispositivo loopback.")