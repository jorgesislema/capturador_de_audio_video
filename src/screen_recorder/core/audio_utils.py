# src/screen_recorder/core/audio_utils.py

import sounddevice as sd
import sys
from typing import List, Dict, Any, Optional

# --- Constantes Heurísticas (Ajustar según sea necesario) ---
# Nombres comunes para dispositivos loopback en Windows (sensible a idioma/drivers)
WINDOWS_LOOPBACK_KEYWORDS = ["Stereo Mix", "Mezcla estéreo", "What U Hear", "Loopback"]

def list_audio_devices() -> Dict[str, List[Dict[str, Any]]]:
    """
    Lista los dispositivos de audio disponibles usando sounddevice.

    Returns:
        Un diccionario con 'input' y 'output' como claves, cada una
        conteniendo una lista de diccionarios con info de cada dispositivo.
        Ej: {'name': 'Micrófono (...)', 'index': 1, 'hostapi_name': 'MME', ...}
    """
    devices = {'input': [], 'output': []}
    try:
        device_list = sd.query_devices()
        host_apis = sd.query_hostapis()

        # Asegurarse de que device_list es una lista (puede ser un solo dict si solo hay 1)
        if isinstance(device_list, dict):
            device_list = [device_list]

        for i, device in enumerate(device_list):
            device_info = device.copy() # Copiar para no modificar original
            device_info['index'] = i # Añadir índice original
            try:
                # Añadir nombre de Host API para más contexto
                hostapi_index = device_info.get('hostapi', -1)
                if 0 <= hostapi_index < len(host_apis):
                    device_info['hostapi_name'] = host_apis[hostapi_index]['name']
                else:
                    device_info['hostapi_name'] = 'N/A'
            except Exception:
                 device_info['hostapi_name'] = 'Error' # Fallback si algo va mal

            # Clasificar por canales de entrada/salida
            if device_info.get('max_input_channels', 0) > 0:
                devices['input'].append(device_info)
            if device_info.get('max_output_channels', 0) > 0:
                devices['output'].append(device_info)

    except Exception as e:
        print(f"Error al listar dispositivos de audio: {e}", file=sys.stderr)
    return devices

def get_default_device_info(kind: str = 'input') -> Optional[Dict[str, Any]]:
    """
    Obtiene la información del dispositivo de audio predeterminado (entrada o salida).

    Args:
        kind: 'input' o 'output'.

    Returns:
        Diccionario con info del dispositivo predeterminado, o None si no se encuentra/error.
    """
    try:
        default_idx = sd.default.device[0 if kind == 'input' else 1]
        if default_idx == -1:
            print(f"No hay dispositivo {kind} predeterminado configurado.", file=sys.stderr)
            return None
        device_info = sd.query_devices(default_idx)
        device_info['index'] = default_idx # Añadir índice
        # Añadir Host API Name (código duplicado de list_audio_devices, podría refactorizarse)
        host_apis = sd.query_hostapis()
        hostapi_index = device_info.get('hostapi', -1)
        if 0 <= hostapi_index < len(host_apis):
             device_info['hostapi_name'] = host_apis[hostapi_index]['name']
        else:
             device_info['hostapi_name'] = 'N/A'
        return device_info
    except Exception as e:
        print(f"Error al obtener dispositivo {kind} predeterminado: {e}", file=sys.stderr)
        return None

def find_loopback_device_info() -> Optional[Dict[str, Any]]:
    """
    Intenta encontrar un dispositivo de loopback de audio (grabación de audio del sistema).
    Esta función es heurística y depende de la plataforma y configuración.

    Returns:
        Diccionario con info del dispositivo loopback encontrado, o None.
    """
    print("Intentando encontrar dispositivo loopback (heurístico)...")
    try:
        devices_info = list_audio_devices()

        if sys.platform == "win32":
            # En Windows, buscar en dispositivos de ENTRADA por nombres clave
            # ¡Importante!: El dispositivo ("Stereo Mix", etc.) debe estar HABILITADO
            # en el panel de control de Sonido de Windows (Grabación -> Mostrar deshabilitados).
            print(f"Buscando keywords {WINDOWS_LOOPBACK_KEYWORDS} en dispositivos de entrada...")
            for device in devices_info.get('input', []):
                name_lower = device.get('name', '').lower()
                for keyword in WINDOWS_LOOPBACK_KEYWORDS:
                    if keyword.lower() in name_lower:
                        print(f"Posible loopback encontrado (Windows/Input): {device['name']} (Index: {device['index']})")
                        # Podríamos verificar la Host API si es necesario, pero dshow lo encontrará por nombre
                        return device
            print("No se encontró dispositivo loopback por nombre clave en Windows.")

        elif sys.platform == "linux":
            # En Linux (PulseAudio/PipeWire), buscar en dispositivos de SALIDA por "Monitor of"
            # O usar directamente nombres como 'alsa_output.pci-....monitor'
            print("Buscando 'Monitor of' en dispositivos de salida (Linux/Pulse)...")
            for device in devices_info.get('output', []): # ¡Ojo! Salida para monitores Pulse
                name = device.get('name', '')
                # Heurística simple: buscar monitores pulseaudio
                if 'monitor' in name.lower():
                    # FFmpeg con -f pulse suele necesitar el *nombre* del monitor
                    print(f"Posible loopback encontrado (Linux/Output Monitor): {name} (Index: {device['index']})")
                    # Para -f pulse, necesitamos el nombre, no el índice sounddevice
                    # Devolver el dict completo, el Recorder usará el nombre
                    return device
            print("No se encontró dispositivo loopback por nombre clave en Linux (Pulse).")
            # Podría intentarse con APIs específicas de PipeWire si es necesario

        else:
            print(f"Detección de loopback no implementada para plataforma: {sys.platform}")

    except Exception as e:
        print(f"Error al buscar dispositivo loopback: {e}", file=sys.stderr)

    return None # No encontrado o error

# --- Ejemplo de uso (para probar el módulo directamente) ---
if __name__ == "__main__":
    print("\n--- Listando Dispositivos de Audio ---")
    all_devices = list_audio_devices()
    import pprint
    pprint.pprint(all_devices)

    print("\n--- Dispositivo de Entrada Predeterminado ---")
    default_in = get_default_device_info('input')
    pprint.pprint(default_in)

    print("\n--- Buscando Dispositivo Loopback ---")
    loopback = find_loopback_device_info()
    pprint.pprint(loopback)

    # Extra: Mostrar nombres para FFmpeg dshow en Windows
    if sys.platform == "win32":
         print("\n--- Nombres para FFmpeg -f dshow (Windows) ---")
         print("# Ejecuta 'ffmpeg -list_devices true -f dshow -i dummy' para ver nombres exactos")
         print("# Nombres según sounddevice (pueden necesitar ajuste para ffmpeg):")
         for device in all_devices.get('input', []):
              print(f"  Input: \"{device.get('name', 'N/A')}\" (API: {device.get('hostapi_name', 'N/A')})")
         # Loopback (Stereo Mix) aparece como Input