# src/screen_recorder/core/recorder.py

import sys
import os
import time
from .ffmpeg_runner import FFmpegRunner, find_ffmpeg_path
# Importar utilidades de audio
from . import audio_utils

# Para captura de área seleccionada
import tempfile
from PySide6.QtWidgets import QDialog, QApplication
from PySide6.QtGui import QPainter, QColor, QScreen, QPixmap
from PySide6.QtCore import Qt, QPoint, QRect, QSize

class AreaSelectionDialog(QDialog):
    """Diálogo para seleccionar un área de la pantalla para captura."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        
        # Cubrir toda la pantalla disponible
        available_geometry = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(available_geometry)
        
        # Variables para seguimiento de selección
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.is_selecting = False
        self.selection_rect = QRect()
        
        # Mensaje de instrucción
        self.instruction_text = "Haz clic y arrastra para seleccionar un área"
        self.cancel_text = "Presiona ESC para cancelar"
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.end_point = self.start_point
            self.is_selecting = True
            self.update()
    
    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_point = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.end_point = event.pos()
            self.is_selecting = False
            self.selection_rect = QRect(self.start_point, self.end_point).normalized()
            # Si la selección es demasiado pequeña, no la aceptamos
            if self.selection_rect.width() > 10 and self.selection_rect.height() > 10:
                self.accept()
            else:
                # Reiniciar para una nueva selección
                self.update()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
    
    def paintEvent(self, event):
        """Dibuja la interfaz de selección de área."""
        painter = QPainter(self)
        
        # Dibujar un fondo semi-transparente
        bg_color = QColor(0, 0, 0, 128)  # RGBA: negro semi-transparente
        painter.fillRect(self.rect(), bg_color)
        
        # Dibujar el área seleccionada (transparente)
        if self.is_selecting or not self.selection_rect.isEmpty():
            select_rect = QRect(self.start_point, self.end_point).normalized()
            
            # Recortar el área seleccionada del fondo para que sea transparente
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(select_rect, Qt.transparent)
            
            # Dibujar un borde alrededor de la selección
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(QColor(255, 255, 255, 200))  # Blanco semi-transparente
            painter.drawRect(select_rect)
            
            # Mostrar las dimensiones
            dimension_text = f"{select_rect.width()} × {select_rect.height()}"
            text_x = select_rect.right() - 120
            text_y = select_rect.bottom() + 30
            
            if text_y > self.height() - 10:
                text_y = select_rect.top() - 20
            
            painter.setPen(QColor(255, 255, 255, 255))
            painter.drawText(text_x, text_y, dimension_text)
        
        # Dibujar instrucciones
        painter.setPen(QColor(255, 255, 255, 200))
        painter.drawText(10, 30, self.instruction_text)
        painter.drawText(10, 60, self.cancel_text)
    
    def get_selection(self):
        """Retorna el rectángulo de selección."""
        return self.selection_rect
    
    @staticmethod
    def get_area_selection():
        """Método estático para mostrar el diálogo y obtener la selección."""
        dialog = AreaSelectionDialog()
        if dialog.exec() == QDialog.Accepted:
            return dialog.get_selection()
        return None

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
        """Genera los argumentos FFmpeg para Video + Audio dependiendo de la plataforma."""
        if sys.platform == "win32":
            return self._get_windows_cmd_args(output_filename)
        elif sys.platform.startswith("linux"):
            return self._get_linux_cmd_args(output_filename)
        else:
            print(f"Plataforma no soportada para grabación: {sys.platform}", file=sys.stderr)
            return None

    def _get_linux_cmd_args(self, output_filename: str) -> list[str]:
        """Genera los argumentos FFmpeg para Video + Audio en Linux (x11grab + pulse/alsa)."""
        print("Generando argumentos FFmpeg para Linux (x11grab + pulse)...")

        # --- Configuración de calidad de video ---
        framerate = self.config.get('framerate', 30)
        preset = self.config.get('preset', "medium")  # Mejor calidad que "veryfast"
        crf = self.config.get('crf', "18")  # Menor valor = mejor calidad (18-28 es rango normal)
        video_codec = self.config.get('video_codec', "libx264")
        audio_codec = self.config.get('audio_codec', "aac")
        audio_bitrate = self.config.get('audio_bitrate', "192k")  # Aumentado de 128k a 192k
        pix_fmt = "yuv420p"  # Necesario para compatibilidad

        # --- Construcción del Comando ---
        cmd = [self.ffmpeg_path]

        # 1. Configuración de entrada de video con x11grab
        display = os.environ.get('DISPLAY', ':0.0')
        video_size = self.config.get('video_size', '')
        if not video_size:
            # Usar dimensiones completas de la pantalla si no se especifica
            import subprocess
            try:
                # Obtener resolución de pantalla
                xrandr_output = subprocess.check_output(['xrandr', '--current']).decode('utf-8')
                for line in xrandr_output.split('\n'):
                    if '*' in line:  # La línea con * tiene la resolución actual
                        parts = line.split()
                        for part in parts:
                            if 'x' in part and part[0].isdigit():
                                video_size = part
                                break
                        break
            except (subprocess.SubprocessError, FileNotFoundError):
                print("No se pudo determinar resolución de pantalla, usando 1920x1080")
                video_size = "1920x1080"

        # Añadir entrada de video
        cmd.extend([
            '-f', 'x11grab',
            '-framerate', str(framerate),
            '-video_size', video_size,
            '-i', display
        ])
        video_input_index = 0

        # 2. Entradas de Audio (PulseAudio)
        audio_inputs = []
        next_audio_index = 1

        # Micrófono
        if self.record_mic:
            cmd.extend([
                '-f', 'pulse',
                '-i', 'default'  # Usa el micrófono predeterminado
            ])
            audio_inputs.append({'index': next_audio_index, 'type': 'mic'})
            next_audio_index += 1
            print("Añadiendo entrada de Micrófono: default (PulseAudio)")

        # Audio del sistema (monitor)
        if self.record_loopback:
            # En PulseAudio, el monitor suele ser "nombre_del_dispositivo.monitor"
            monitor_device = "0.monitor"  # Usa el monitor de salida predeterminada
            cmd.extend([
                '-f', 'pulse',
                '-i', monitor_device
            ])
            audio_inputs.append({'index': next_audio_index, 'type': 'loopback'})
            next_audio_index += 1
            print(f"Añadiendo entrada de Loopback: {monitor_device} (PulseAudio)")

        # 3. Códecs y Mapeo
        cmd.extend(['-c:v', video_codec, '-preset', preset, '-crf', crf, '-pix_fmt', pix_fmt])
        cmd.extend(['-map', f"{video_input_index}:v"])  # Mapear siempre el video

        if len(audio_inputs) == 0:
            cmd.extend(['-an'])  # Sin audio
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
            cmd.extend(['-map', '[aout]'])  # Mapear la salida del filtro
            cmd.extend(['-c:a', audio_codec, '-b:a', audio_bitrate])
            print(f"Configurando FFmpeg con 2 fuentes de audio mezclados con amix.")

        # 4. Archivo de Salida y Opciones Finales
        cmd.extend(['-y', output_filename])

        return cmd

    def _get_windows_cmd_args(self, output_filename: str) -> list[str]:
        """Genera los argumentos FFmpeg para Video + Audio en Windows (dshow)."""
        print("Generando argumentos FFmpeg para Windows (gdigrab + dshow)...")

        # --- Configuración de calidad de video ---
        framerate = self.config.get('framerate', 30)
        preset = self.config.get('preset', "medium")  # Mejor calidad que "veryfast"
        crf = self.config.get('crf', "18")  # Menor valor = mejor calidad (18-28 es rango normal)
        video_codec = self.config.get('video_codec', "libx264")
        audio_codec = self.config.get('audio_codec', "aac")
        audio_bitrate = self.config.get('audio_bitrate', "192k")  # Aumentado de 128k a 192k
        pix_fmt = "yuv420p"  # Necesario para compatibilidad

        # --- Construcción del Comando ---
        cmd = [self.ffmpeg_path]

        # 1. Entrada de Video (gdigrab) - Siempre presente
        cmd.extend(['-f', 'gdigrab', '-framerate', str(framerate), '-i', 'desktop'])
        video_input_index = 0  # gdigrab es la entrada 0

        # 2. Entradas de Audio (dshow) - Opcionales
        audio_inputs = []
        next_audio_index = 1  # El siguiente índice de entrada después del video

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
        cmd.extend(['-map', f"{video_input_index}:v"])  # Mapear siempre el video

        if len(audio_inputs) == 0:
            cmd.extend(['-an'])  # Sin audio
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
            cmd.extend(['-map', '[aout]'])  # Mapear la salida del filtro
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

    def take_screenshot(self, output_filename: str, select_area: bool = False) -> str | None:
        """Captura una imagen de la pantalla completa o de un área seleccionada.
        
        Args:
            output_filename: Ruta completa donde guardar la captura
            select_area: Si es True, permite al usuario seleccionar un área específica
            
        Returns:
            La ruta donde se guardó la captura o None si hubo un error
        """
        if not self.ffmpeg_ready or self.ffmpeg_path is None:
            print("Error: FFmpeg no listo para captura de pantalla.", file=sys.stderr)
            return None
            
        # Verificar que la extensión sea compatible
        ext = os.path.splitext(output_filename)[1].lower()
        if ext not in ['.png', '.jpg', '.jpeg']:
            print(f"Error: Formato no soportado para captura: {ext}. Use .png, .jpg o .jpeg", file=sys.stderr)
            return None
        
        # Si se solicita selección de área, importar e iniciar el diálogo mejorado
        selected_rect = None
        if select_area:
            try:
                # Usar la implementación mejorada de area_selection.py
                from ..gui.area_selection import AreaSelectionDialog as EnhancedAreaSelectionDialog
                selected_rect = EnhancedAreaSelectionDialog.get_area_selection()
                if not selected_rect:
                    print("Selección de área cancelada por el usuario")
                    return None
                print(f"Área seleccionada: {selected_rect.width()}x{selected_rect.height()} en posición ({selected_rect.x()}, {selected_rect.y()})")
            except ImportError as e:
                print(f"No se pudo importar AreaSelectionDialog mejorado: {e}", file=sys.stderr)
                # Fallback a la implementación local
                selected_rect = AreaSelectionDialog.get_area_selection()
                if not selected_rect:
                    print("Selección de área cancelada por el usuario")
                    return None
        
        # Determinar parámetros según plataforma
        is_linux = sys.platform.startswith('linux')
        
        # Si tenemos área seleccionada y estamos en Linux, podemos usar el método de captura directa de Qt
        if select_area and selected_rect:
            try:
                # Intentar primero con el método Qt que funciona en todas las plataformas
                screen = QApplication.primaryScreen()
                if not screen:
                    print("Error: No se pudo acceder a la pantalla primaria", file=sys.stderr)
                    return None
                
                pixmap = screen.grabWindow(
                    0,  # Capturar toda la pantalla (0 = desktop)
                    selected_rect.x(), 
                    selected_rect.y(),
                    selected_rect.width(), 
                    selected_rect.height()
                )
                
                if pixmap and not pixmap.isNull():
                    if pixmap.save(output_filename):
                        print(f"Captura de área seleccionada guardada en: {output_filename}")
                        return output_filename
                    else:
                        print(f"Error al guardar la captura: {output_filename}", file=sys.stderr)
                else:
                    print("Error al capturar el área seleccionada", file=sys.stderr)
            except Exception as e:
                print(f"Error con método Qt de captura: {e}", file=sys.stderr)
        
        # Si la captura con Qt falló o no tenemos área seleccionada, usar FFmpeg
        try:
            # Generar comando FFmpeg base
            cmd = [
                self.ffmpeg_path,
                "-f", "x11grab" if is_linux else "gdigrab",
                "-framerate", "1",  # Solo necesitamos un frame
            ]
            
            # Configurar parámetros según plataforma y si hay área seleccionada
            if is_linux:
                # Linux con x11grab
                if select_area and selected_rect:
                    # Agregar parámetros para área seleccionada
                    cmd.extend([
                        "-video_size", f"{selected_rect.width()}x{selected_rect.height()}",
                        "-i", f":0.0+{selected_rect.x()},{selected_rect.y()}"
                    ])
                else:
                    # Captura completa
                    from subprocess import check_output
                    try:
                        # Obtener resolución de pantalla
                        xrandr_output = check_output(["xrandr"]).decode()
                        import re
                        match = re.search(r'connected primary (\d+x\d+)', xrandr_output)
                        if match:
                            resolution = match.group(1)
                        else:
                            match = re.search(r'(\d+x\d+) \+', xrandr_output)
                            resolution = match.group(1) if match else "1920x1080"
                        print(f"Resolución detectada para captura: {resolution}")
                    except Exception as e:
                        print(f"Error detectando resolución: {e}, usando valor por defecto")
                        resolution = "1920x1080"
                        
                    cmd.extend(["-video_size", resolution])
                    cmd.extend(["-i", ":0.0"])
            else:
                # Windows con gdigrab
                if select_area and selected_rect:
                    # Agregar parámetros para área seleccionada en Windows
                    cmd.extend([
                        "-offset_x", str(selected_rect.x()),
                        "-offset_y", str(selected_rect.y()),
                        "-video_size", f"{selected_rect.width()}x{selected_rect.height()}",
                        "-i", "desktop"
                    ])
                else:
                    # Captura completa
                    cmd.extend(["-i", "desktop"])
            
            # Finalizar comando común
            cmd.extend([
                "-frames:v", "1",   # Capturar solo 1 frame
                "-y",               # Sobrescribir sin preguntar
                output_filename
            ])
            
            print(f"Ejecutando comando para captura de pantalla: {' '.join(cmd)}")
            
            # Ejecutar el comando
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.returncode != 0:
                print(f"Error en FFmpeg (código {result.returncode}):", file=sys.stderr)
                print(f"Salida de error: {result.stderr}", file=sys.stderr)
                
                # Si falla con x11grab, intentar con alternativas
                if is_linux:
                    print("Intentando método alternativo...")
                    try:
                        alt_cmd = None
                        if select_area and selected_rect:
                            # Para área seleccionada intentar con otras herramientas
                            if subprocess.run(["which", "gnome-screenshot"], capture_output=True).returncode == 0:
                                alt_cmd = ["gnome-screenshot", "-a", "-f", output_filename]
                            elif subprocess.run(["which", "scrot"], capture_output=True).returncode == 0:
                                alt_cmd = ["scrot", "-s", output_filename]
                            elif subprocess.run(["which", "import"], capture_output=True).returncode == 0:
                                # ImageMagick import
                                alt_cmd = ["import", output_filename]
                        else:
                            # Para pantalla completa
                            if subprocess.run(["which", "scrot"], capture_output=True).returncode == 0:
                                alt_cmd = ["scrot", output_filename]
                            elif subprocess.run(["which", "gnome-screenshot"], capture_output=True).returncode == 0:
                                alt_cmd = ["gnome-screenshot", "-f", output_filename]
                                
                        if alt_cmd:
                            print(f"Ejecutando alternativa: {' '.join(alt_cmd)}")
                            subprocess.run(alt_cmd, check=True)
                            if os.path.exists(output_filename):
                                return output_filename
                    except Exception as e:
                        print(f"Error con método alternativo: {e}", file=sys.stderr)
                
                return None
            
            if os.path.exists(output_filename):
                print(f"Captura de pantalla guardada en: {output_filename}")
                return output_filename
            else:
                print(f"Error: No se pudo crear el archivo {output_filename}", file=sys.stderr)
                return None
                
        except Exception as e:
            print(f"Error al capturar pantalla: {e}", file=sys.stderr)
            return None