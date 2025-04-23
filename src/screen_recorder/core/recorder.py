# src/screen_recorder/core/recorder.py

import sys
import os
import time
from .ffmpeg_runner import FFmpegRunner, find_ffmpeg_path
# Importar utilidades de audio
from . import audio_utils

class Recorder:
    """Gestiona la lógica principal de grabación usando FFmpeg."""
    def __init__(self, config: dict) -> None:
        """Inicializador del Recorder."""
        self.config = config
        self.ffmpeg_path: str | None = None
        self.ffmpeg_runner: FFmpegRunner | None = None
        self.ffmpeg_ready: bool = False
        self.last_output_path: str | None = None

        # --- Configuración de Audio ---
        self.record_mic: bool = config.get('record_audio_mic', True)
        self.record_loopback: bool = config.get('record_audio_loopback', True)
        # Obtener nombres de config o intentar detectar los por defecto
        self.mic_dev_name: str | None = self._get_configured_or_default_device(
            config.get('audio_mic_device_name'), 'input'
        )
        self.loopback_dev_name: str | None = self._get_configured_or_default_device(
            config.get('audio_loopback_device_name'), 'loopback'
        )
        print(f"Configuración Audio - Micrófono: {'Activado' if self.record_mic else 'Desactivado'}, Dispositivo: {self.mic_dev_name or 'No encontrado/Default'}")
        print(f"Configuración Audio - Sistema: {'Activado' if self.record_loopback else 'Desactivado'}, Dispositivo: {self.loopback_dev_name or 'No encontrado/Default'}")
        # Nota: Guardar la configuración actualizada con los defaults detectados
        # podría ser útil, pero lo haremos solo cuando el usuario cambie algo explícitamente.

        print("Recorder: Inicializando FFmpeg...")
        self._initialize_ffmpeg()

    def _get_configured_or_default_device(self, config_name: str | None, kind: str) -> str | None:
        """Obtiene el nombre del dispositivo de la config o busca el default."""
        if config_name:
            # TODO: Podríamos añadir una verificación aquí si el dispositivo aún existe
            print(f"Usando dispositivo '{kind}' desde config: {config_name}")
            return config_name

        print(f"Nombre para '{kind}' no en config, buscando default...")
        device_info: dict | None = None
        if kind == 'input':
            device_info = audio_utils.get_default_device_info('input')
        elif kind == 'loopback':
            device_info = audio_utils.find_loopback_device_info()
        # Podríamos añadir 'output' si fuera necesario en el futuro

        if device_info:
            print(f"Dispositivo default '{kind}' encontrado: {device_info.get('name')}")
            return device_info.get('name') # Devolver solo el nombre
        else:
             print(f"No se encontró dispositivo default para '{kind}'.")
             return None

    def _initialize_ffmpeg(self) -> None:
        """Busca FFmpeg y prepara el runner."""
        self.ffmpeg_path = find_ffmpeg_path(self.config.get('ffmpeg_path'))
        if self.ffmpeg_path:
            self.ffmpeg_runner = FFmpegRunner(self.ffmpeg_path)
            self.ffmpeg_ready = self.ffmpeg_runner.ready
            if self.ffmpeg_ready:
                print(f"Recorder: FFmpeg listo en '{self.ffmpeg_path}'.")
            else:
                print("Recorder Error: FFmpegRunner no pudo inicializarse.", file=sys.stderr)
        else:
            self.ffmpeg_ready = False
            print("Recorder Error: FFmpeg no encontrado.", file=sys.stderr)

    def _get_platform_cmd_args(self, output_filename: str) -> list[str] | None:
        """Genera los argumentos FFmpeg para Video + Audio en Windows (dshow)."""
        if sys.platform != "win32":
             print(f"Plataforma no soportada para grabación con audio dshow: {sys.platform}", file=sys.stderr)
             # TODO: Implementar lógica para Linux/macOS aquí
             return None

        print("Generando argumentos FFmpeg para Windows (gdigrab + dshow)...")

        # --- Configuración (Podrían venir de self.config) ---
        framerate = 30
        preset = "veryfast"
        crf = "28"
        video_codec = "libx264"
        audio_codec = "aac" # Códec de audio común
        audio_bitrate = "128k"
        pix_fmt = "yuv420p" # Necesario para compatibilidad con libx264

        # --- Construcción del Comando ---
        cmd = [self.ffmpeg_path]

        # 1. Entrada de Video (gdigrab) - Siempre presente
        cmd.extend(['-f', 'gdigrab', '-framerate', str(framerate), '-i', 'desktop'])
        video_input_index = 0 # gdigrab es la entrada 0

        # 2. Entradas de Audio (dshow) - Opcionales
        audio_inputs = []
        next_audio_index = 1 # El siguiente índice de entrada después del video

        # Micrófono
        if self.record_mic and self.mic_dev_name:
            # ¡Importante! Los nombres dshow deben ser exactos. Ejecutar
            # 'ffmpeg -list_devices true -f dshow -i dummy' para verificarlos.
            mic_input_str = f"audio={self.mic_dev_name}"
            cmd.extend(['-f', 'dshow', '-i', mic_input_str])
            audio_inputs.append({'index': next_audio_index, 'type': 'mic'})
            next_audio_index += 1
            print(f"Añadiendo entrada de Micrófono: {mic_input_str} (Índice: {audio_inputs[-1]['index']})")
        elif self.record_mic:
            print("Advertencia: Grabar Micrófono está activado pero no se encontró/configuró dispositivo.")

        # Loopback (Audio del sistema)
        if self.record_loopback and self.loopback_dev_name:
            loopback_input_str = f"audio={self.loopback_dev_name}"
            cmd.extend(['-f', 'dshow', '-i', loopback_input_str])
            audio_inputs.append({'index': next_audio_index, 'type': 'loopback'})
            next_audio_index += 1
            print(f"Añadiendo entrada de Loopback: {loopback_input_str} (Índice: {audio_inputs[-1]['index']})")
        elif self.record_loopback:
            print("Advertencia: Grabar Loopback está activado pero no se encontró/configuró dispositivo.")
            print("             Asegúrate de que 'Stereo Mix' o similar esté habilitado en Windows.")


        # 3. Códecs y Mapeo
        cmd.extend(['-c:v', video_codec, '-preset', preset, '-crf', crf, '-pix_fmt', pix_fmt])
        cmd.extend(['-map', f"{video_input_index}:v"]) # Mapear siempre el video

        if len(audio_inputs) == 0:
            cmd.extend(['-an']) # Sin audio
            print("Configurando FFmpeg sin audio.")
        elif len(audio_inputs) == 1:
            # Mapear la única fuente de audio directamente
            audio_index = audio_inputs[0]['index']
            cmd.extend(['-map', f"{audio_index}:a"])
            cmd.extend(['-c:a', audio_codec, '-b:a', audio_bitrate])
            print(f"Configurando FFmpeg con 1 fuente de audio (Índice: {audio_index}).")
        elif len(audio_inputs) == 2:
            # Mezclar las dos fuentes de audio usando amix
            idx1 = audio_inputs[0]['index']
            idx2 = audio_inputs[1]['index']
            filter_complex = f"[{idx1}:a][{idx2}:a]amix=inputs=2:duration=longest[aout]"
            cmd.extend(['-filter_complex', filter_complex])
            cmd.extend(['-map', '[aout]']) # Mapear la salida del filtro
            cmd.extend(['-c:a', audio_codec, '-b:a', audio_bitrate])
            print(f"Configurando FFmpeg con 2 fuentes de audio (Índices: {idx1}, {idx2}), mezclando con amix.")

        # 4. Archivo de Salida y Opciones Finales
        cmd.extend(['-y', output_filename])

        return cmd

    def start(self, output_filename: str) -> bool:
        """Inicia la grabación (Video + Audio configurado) usando FFmpeg."""
        if not self.ffmpeg_ready or self.ffmpeg_runner is None:
            print("Error: FFmpeg no listo.", file=sys.stderr)
            return False
        if self.ffmpeg_runner.process is not None:
            print("Advertencia: Grabación ya en curso.", file=sys.stderr)
            return False

        cmd_args = self._get_platform_cmd_args(output_filename)
        if cmd_args is None:
             print("Error: No se pudieron generar los argumentos de comando para FFmpeg.", file=sys.stderr)
             return False # Plataforma no soportada o error

        if self.ffmpeg_runner.start_recording(output_filename, cmd_args[1:]): # Pasar args sin el path a ffmpeg
            self.last_output_path = output_filename
            return True
        else:
            self.last_output_path = None
            return False

    def pause(self) -> None:
        """Pausa la grabación (Placeholder)."""
        print("Recorder: Pausa no implementada.")

    def resume(self) -> None:
        """Reanuda la grabación (Placeholder)."""
        print("Recorder: Reanudar no implementado.")

    def stop(self) -> str | None:
        """Detiene la grabación activa de FFmpeg."""
        if not self.ffmpeg_ready or self.ffmpeg_runner is None:
            print("Error: FFmpeg no listo.", file=sys.stderr)
            return None
        if self.ffmpeg_runner.process is None:
            print("Advertencia: No había grabación activa.")
            return None

        print("Solicitando detención al FFmpegRunner...")
        if self.ffmpeg_runner.stop_recording():
            print("Recorder: Detención completada.")
            stopped_path = self.last_output_path
            self.last_output_path = None
            return stopped_path
        else:
            print("Recorder Error: Problemas al detener FFmpeg.", file=sys.stderr)
            self.last_output_path = None
            return None