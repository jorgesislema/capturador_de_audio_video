# src/screen_recorder/gui/main_window.py

import sys
import os
from enum import Enum, auto
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import QSize, Slot, QTimer
from PySide6.QtGui import QIcon # Opcional para iconos

# Asegurar import correcto
from screen_recorder.core.recorder import Recorder
from screen_recorder.core import config_manager
from screen_recorder.core import audio_utils # Importar para acceso a nombres default si fuera necesario

class State(Enum):
    IDLE = auto()
    RECORDING = auto()
    PAUSED = auto()

class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._state: State = State.IDLE
        self.config = config_manager.load_config()
        self.output_dir: str | None = self.config.get("output_dir")

        # Crear instancia del Recorder (ahora usa config para audio y ffmpeg)
        self.recorder = Recorder(self.config)
        self.ffmpeg_ok = self.recorder.ffmpeg_ready

        self.record_timer = QTimer(self)
        self.record_timer.setInterval(1000)
        self.record_timer.timeout.connect(self._update_timer_display)
        self.elapsed_seconds: int = 0

        self.setWindowTitle("Capturador de Audio y Video")
        self.resize(QSize(550, 250)) # Un poco más grande

        self._setup_ui()
        self._connect_signals()
        self._check_ffmpeg_status()
        self._update_audio_status_labels() # Actualizar etiquetas de audio iniciales
        self._set_state(State.IDLE) # Estado inicial

    def _setup_ui(self) -> None:
        """Crea y organiza los widgets de la interfaz."""
        # --- Labels ---
        self.status_label = QLabel("Estado: Listo")
        self.timer_label = QLabel("00:00:00")
        self.output_dir_label = QLabel(self._get_output_dir_display_text())
        self.output_dir_label.setWordWrap(True)
        # Etiquetas para estado de audio
        self.mic_status_label = QLabel("Mic: Cargando...")
        self.loopback_status_label = QLabel("Sistema: Cargando...")

        # --- Buttons ---
        self.record_button = QPushButton("Grabar")
        self.pause_button = QPushButton("Pausa")
        self.stop_button = QPushButton("Detener")
        self.screenshot_button = QPushButton("📷 Captura")
        self.output_dir_button = QPushButton("Carpeta Salida...")
        self.help_audio_button = QPushButton("❓ Ayuda Audio")
        
        self.pause_button.setEnabled(False)
        self.pause_button.setToolTip("La pausa no está implementada en esta versión.")
        self.screenshot_button.setToolTip("Toma una captura de la pantalla completa")

        # --- Layouts ---
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.record_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.screenshot_button)

        config_layout = QHBoxLayout()
        config_layout.addWidget(self.output_dir_button)
        config_layout.addWidget(self.output_dir_label, 1)

        # Layout para audio con botón de ayuda
        audio_layout = QHBoxLayout()
        audio_info_layout = QVBoxLayout()
        audio_info_layout.addWidget(self.mic_status_label)
        audio_info_layout.addWidget(self.loopback_status_label)
        audio_layout.addLayout(audio_info_layout)
        audio_layout.addWidget(self.help_audio_button)

        # Layout para info de estado y audio
        info_layout = QVBoxLayout()
        info_layout.addWidget(self.status_label)
        info_layout.addWidget(self.timer_label)
        info_layout.addLayout(audio_layout)
        info_layout.addStretch(1) # Empujar hacia arriba

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.addLayout(info_layout) # Info arriba
        main_layout.addLayout(config_layout) # Config dir abajo de info
        main_layout.addStretch(1) # Espacio flexible en medio
        main_layout.addLayout(button_layout) # Botones al final

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def _connect_signals(self) -> None:
        """Conecta las señales a los slots."""
        self.record_button.clicked.connect(self._on_record_clicked)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.output_dir_button.clicked.connect(self._select_output_dir)
        self.help_audio_button.clicked.connect(self._show_audio_help)
        self.screenshot_button.clicked.connect(self._on_screenshot_clicked)
        # self.pause_button.clicked.connect(...) # Sigue desconectado

    def _check_ffmpeg_status(self) -> None:
        """Verifica FFmpeg y actualiza UI si falta."""
        if not self.ffmpeg_ok:
            # Mensaje de error y deshabilitar botones (igual que antes)
            QMessageBox.critical(
                self, "Error: FFmpeg no encontrado",
                (f"No se pudo encontrar o inicializar FFmpeg.\n"
                 f"La grabación no funcionará.\n\n"
                 f"Instálalo y asegúrate de que esté en el PATH,\n"
                 f"o configura la ruta en:\n{config_manager.config_file}")
            )
            self.record_button.setEnabled(False)
            self.record_button.setToolTip("FFmpeg no encontrado o no configurado.")
            self.stop_button.setEnabled(False)

    def _update_audio_status_labels(self) -> None:
        """Actualiza las etiquetas que muestran el estado de captura de audio."""
        mic_active = self.config.get('record_audio_mic', False)
        mic_device = self.recorder.mic_dev_name # Nombre ya resuelto (config o default)
        mic_text = f"Micrófono: {'ACT' if mic_active else 'OFF'} ({mic_device or 'No encontrado/Default'})"
        self.mic_status_label.setText(mic_text)

        loop_active = self.config.get('record_audio_loopback', False)
        loop_device = self.recorder.loopback_dev_name # Nombre ya resuelto
        loop_text = f"Audio Sistema: {'ACT' if loop_active else 'OFF'} ({loop_device or 'No encontrado/Default'})"
        # Añadir nota si loopback no encontrado pero activado
        if loop_active and not loop_device:
            loop_text += " (Revisa si 'Stereo Mix' está habilitado)"
        self.loopback_status_label.setText(loop_text)


    def _get_output_dir_display_text(self) -> str:
        """Genera el texto para mostrar la carpeta de salida."""
        path_to_display = self.output_dir
        if path_to_display and not os.path.isdir(path_to_display):
             path_to_display = None
        return f"Guardar en: {path_to_display or 'No seleccionada / Inválida'}"


    def _set_state(self, new_state: State) -> None:
        """Actualiza el estado interno y la interfaz de usuario."""
        if not self.ffmpeg_ok and new_state in (State.RECORDING, State.PAUSED):
            if self._state != State.IDLE: new_state = State.IDLE
            else: return

        self._state = new_state
        print(f"Cambiando al estado: {new_state.name}")

        is_idle = self._state == State.IDLE
        is_recording = self._state == State.RECORDING

        self.status_label.setText(f"Estado: {new_state.name.replace('_', ' ').capitalize()}")
        if is_idle:
            self.timer_label.setText("00:00:00")

        self.record_button.setEnabled(is_idle and self.ffmpeg_ok)
        self.record_button.setText("Grabar")
        self.pause_button.setEnabled(False) # Siempre deshabilitado
        self.stop_button.setEnabled(is_recording and self.ffmpeg_ok)
        self.output_dir_button.setEnabled(is_idle)
        
        # El botón de captura de pantalla siempre está disponible si FFmpeg está listo
        self.screenshot_button.setEnabled(self.ffmpeg_ok)
        
        self._update_audio_status_labels() # Actualizar estado audio en cada cambio


    # --- Slots (Manejadores de Eventos) ---
    # _on_record_clicked, _on_pause_clicked, _on_stop_clicked,
    # _update_timer_display, _select_output_dir
    # (La lógica interna de estos no necesita cambiar significativamente respecto
    # a la Etapa 5, ya que la complejidad de construir el comando ffmpeg
    # con audio se movió a Recorder._get_platform_cmd_args)
    # Solo necesitamos asegurarnos de que llaman a los métodos del recorder.

    @Slot()
    def _on_record_clicked(self) -> None:
        """Slot para manejar el clic en el botón Grabar."""
        if not self.ffmpeg_ok: return # Salir si FFmpeg no está listo

        if self._state == State.IDLE:
            if not self.output_dir or not os.path.isdir(self.output_dir):
                if not self._select_output_dir(): return

            try:
                now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"recording_{now}.mp4" # Asumir mp4 por ahora
                full_output_path = os.path.join(self.output_dir, filename)
            except Exception as e:
                QMessageBox.warning(self,"Error de Archivo",f"No se pudo generar ruta:\n{e}")
                return

            print(f"Intentando iniciar grabación en: {full_output_path}")
            if self.recorder.start(full_output_path):
                self.elapsed_seconds = 0
                self._update_timer_display()
                self.record_timer.start()
                self._set_state(State.RECORDING)
            else:
                 QMessageBox.warning(self,"Error de Grabación", "No se pudo iniciar el proceso.\nRevisa la consola.")
                 self._set_state(State.IDLE)

    @Slot()
    def _on_pause_clicked(self) -> None:
        """Slot para Pausa (Deshabilitado)."""
        print("El botón Pausa está deshabilitado.")

    @Slot()
    def _on_stop_clicked(self) -> None:
        """Slot para manejar el clic en el botón Detener."""
        if self._state == State.RECORDING: # Solo detener si está grabando
            print("Acción: Deteniendo grabación...")
            self.record_timer.stop()
            stop_result = self.recorder.stop()
            self._set_state(State.IDLE) # Volver a IDLE
            if stop_result:
                print(f"Grabación detenida. Archivo: {stop_result}")
                QMessageBox.information(self, "Grabación Finalizada", f"Archivo guardado (o debería):\n{stop_result}")
            else:
                print("El recorder indicó un problema al detener.")
                QMessageBox.warning(self, "Error al Detener", "Hubo un problema al detener la grabación.")


    @Slot()
    def _update_timer_display(self) -> None:
        """Actualiza la etiqueta del temporizador cada segundo."""
        self.elapsed_seconds += 1
        td = timedelta(seconds=self.elapsed_seconds)
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
        self.timer_label.setText(time_str)

    @Slot()
    def _select_output_dir(self) -> bool:
        """Abre diálogo para seleccionar carpeta y guarda la config."""
        start_dir = self.output_dir if self.output_dir and os.path.isdir(self.output_dir) else os.path.expanduser("~")
        selected_dir = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Salida", start_dir)
        if selected_dir:
            self.output_dir = selected_dir
            print(f"Carpeta de salida seleccionada: {self.output_dir}")
            self.output_dir_label.setText(self._get_output_dir_display_text())
            self.config["output_dir"] = self.output_dir
            if not config_manager.save_config(self.config):
                QMessageBox.warning(self,"Error de Configuración","No se pudo guardar la carpeta seleccionada.")
            return True
        else:
            print("Selección de carpeta cancelada.")
            return False

    @Slot()
    def _show_audio_help(self) -> None:
        """Muestra un diálogo de ayuda con instrucciones para configurar el audio del sistema."""
        import platform
        
        title = "Configuración de Audio del Sistema"
        system = platform.system().lower()
        
        if system == "linux":
            message = (
                "<h3>Cómo habilitar la captura de audio del sistema en Linux</h3>"
                "<p><b>Para sistemas con PulseAudio (la mayoría de distribuciones):</b></p>"
                "<ol>"
                "<li>Instala pavucontrol si no lo tienes:<br>"
                "<code>sudo apt install pavucontrol</code></li>"
                "<li>Abre Control de Volumen de PulseAudio (pavucontrol)</li>"
                "<li>Ve a la pestaña <b>Dispositivos de entrada</b></li>"
                "<li>Cambia el selector 'Mostrar:' a <b>Todos los dispositivos de entrada</b></li>"
                "<li>Deberías ver uno o más dispositivos llamados 'Monitor of...'</li>"
                "<li>Asegúrate de que no estén silenciados (icono de altavoz tachado)</li>"
                "</ol>"
                "<p><b>Después de seguir estos pasos:</b></p>"
                "<ol>"
                "<li>Reinicia esta aplicación</li>"
                "<li>El dispositivo 'Monitor of...' debería aparecer automáticamente</li>"
                "</ol>"
                "<p><b>Nota:</b> Para grabar audio del sistema mientras se reproduce, debes asegurarte de estar usando el dispositivo de salida cuyo 'Monitor' quieres capturar.</p>"
            )
        elif system == "windows":
            message = (
                "<h3>Cómo habilitar Stereo Mix en Windows</h3>"
                "<p>Para capturar el audio del sistema en Windows, necesitas habilitar 'Stereo Mix':</p>"
                "<ol>"
                "<li>Haz clic derecho en el icono de volumen en la barra de tareas</li>"
                "<li>Selecciona 'Sonidos' o 'Configuración de sonido'</li>"
                "<li>Ve a la pestaña 'Grabación'</li>"
                "<li>Haz clic derecho en un área vacía y marca 'Mostrar dispositivos deshabilitados'</li>"
                "<li>Debería aparecer 'Stereo Mix' (o un nombre similar como 'Lo que escuchas', 'What U Hear', etc.)</li>"
                "<li>Haz clic derecho en 'Stereo Mix' y selecciona 'Habilitar'</li>"
                "<li>Haz clic derecho de nuevo y selecciona 'Establecer como dispositivo predeterminado'</li>"
                "</ol>"
                "<p><b>Si no ves Stereo Mix:</b></p>"
                "<ul>"
                "<li>Tu tarjeta de sonido podría no soportarlo</li>"
                "<li>Prueba actualizar los controladores de audio</li>"
                "<li>Como alternativa, puedes usar software como 'Voicemeeter' o 'Virtual Audio Cable'</li>"
                "</ul>"
                "<p><b>Después de seguir estos pasos:</b></p>"
                "<ol>"
                "<li>Reinicia esta aplicación</li>"
                "<li>El dispositivo 'Stereo Mix' debería aparecer automáticamente</li>"
                "</ol>"
            )
        else:  # macOS u otros
            message = (
                "<h3>Configuración de Audio del Sistema</h3>"
                "<p>Tu sistema operativo necesita pasos especiales para capturar el audio del sistema:</p>"
                "<ul>"
                "<li>En macOS, necesitas instalar software adicional como 'Soundflower', 'BlackHole', 'Loopback', etc.</li>"
                "<li>En otros sistemas, busca herramientas específicas que permitan capturar el audio del sistema</li>"
                "</ul>"
                "<p>Consulta la documentación en línea para tu sistema operativo específico.</p>"
            )
        
        # Mostrar un diálogo con instrucciones detalladas
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setTextFormat(1)  # Qt.RichText
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()

    @Slot()
    def _on_screenshot_clicked(self) -> None:
        """Slot para manejar el clic en el botón de captura de pantalla."""
        if not self.ffmpeg_ok:
            QMessageBox.warning(self, "Error", "FFmpeg no está disponible para capturar pantalla.")
            return
            
        # Verificar que tenemos una carpeta de salida
        if not self.output_dir or not os.path.isdir(self.output_dir):
            if not self._select_output_dir():
                return
        
        try:
            # Preguntar al usuario si quiere capturar toda la pantalla o un área
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Tipo de Captura")
            msg_box.setText("¿Qué tipo de captura deseas realizar?")
            area_btn = msg_box.addButton("Seleccionar Área", QMessageBox.ActionRole)
            completa_btn = msg_box.addButton("Pantalla Completa", QMessageBox.ActionRole)
            cancelar_btn = msg_box.addButton("Cancelar", QMessageBox.RejectRole)
            
            msg_box.exec()
            
            # Si el usuario canceló, salir
            if msg_box.clickedButton() == cancelar_btn:
                return
                
            # Determinar si se seleccionará un área
            select_area = (msg_box.clickedButton() == area_btn)
                
            # Generar nombre de archivo con timestamp para la captura
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"captura_{now}.png"  # Usar formato PNG por defecto
            full_output_path = os.path.join(self.output_dir, filename)
            
            # Actualizar estado temporalmente
            prev_text = self.status_label.text()
            area_text = "seleccionada " if select_area else ""
            self.status_label.setText(f"Estado: Capturando área {area_text}...")
            self.repaint()  # Forzar actualización inmediata
            
            # Si se va a seleccionar un área, minimizar la ventana para no interferir
            if select_area:
                self.showMinimized()
                # Pequeña pausa para permitir que la ventana se minimice completamente
                QApplication.processEvents()
                import time
                time.sleep(0.5)
            
            # Tomar la captura
            screenshot_path = self.recorder.take_screenshot(full_output_path, select_area)
            
            # Restaurar ventana
            if select_area:
                self.showNormal()
                
            # Restaurar estado
            self.status_label.setText(prev_text)
            
            if screenshot_path:
                print(f"Captura de pantalla {area_text}guardada en: {screenshot_path}")
                
                # Mostrar mensaje con opción para abrir la imagen
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Captura Realizada")
                msg_box.setText(f"Captura {area_text}guardada en:\n{screenshot_path}")
                msg_box.setIcon(QMessageBox.Information)
                
                # Botones: Abrir imagen, Abrir carpeta, Cerrar
                abrir_btn = msg_box.addButton("Abrir Imagen", QMessageBox.ActionRole)
                carpeta_btn = msg_box.addButton("Abrir Carpeta", QMessageBox.ActionRole)
                msg_box.addButton(QMessageBox.Close)
                
                msg_box.exec()
                
                # Manejar clic en botones
                if msg_box.clickedButton() == abrir_btn:
                    self._open_file(screenshot_path)
                elif msg_box.clickedButton() == carpeta_btn:
                    self._open_directory(os.path.dirname(screenshot_path))
            else:
                if select_area:
                    QMessageBox.information(self, "Captura Cancelada", "Has cancelado la selección del área.")
                else:
                    QMessageBox.warning(self, "Error", "No se pudo capturar la pantalla. Revisa la consola para más detalles.")
        except Exception as e:
            print(f"Error al capturar pantalla: {e}")
            QMessageBox.warning(self, "Error", f"Error al capturar pantalla:\n{e}")
            
    def _open_file(self, path: str) -> None:
        """Abre un archivo con la aplicación predeterminada del sistema."""
        try:
            import subprocess
            import platform
            
            system = platform.system().lower()
            if system == 'windows':
                os.startfile(path)
            elif system == 'darwin':  # macOS
                subprocess.run(['open', path], check=True)
            else:  # Linux o otros
                subprocess.run(['xdg-open', path], check=True)
        except Exception as e:
            print(f"Error al abrir archivo: {e}")
            
    def _open_directory(self, path: str) -> None:
        """Abre un directorio con el explorador de archivos del sistema."""
        self._open_file(path)