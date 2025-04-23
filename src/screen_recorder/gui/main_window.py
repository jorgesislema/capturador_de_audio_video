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

        self.setWindowTitle("Screen Recorder")
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
        # Nuevas etiquetas para estado de audio
        self.mic_status_label = QLabel("Mic: Cargando...")
        self.loopback_status_label = QLabel("Sistema: Cargando...")

        # --- Buttons ---
        self.record_button = QPushButton("Grabar")
        self.pause_button = QPushButton("Pausa")
        self.stop_button = QPushButton("Detener")
        self.output_dir_button = QPushButton("Carpeta Salida...")

        self.pause_button.setEnabled(False)
        self.pause_button.setToolTip("La pausa no está implementada en esta versión.")

        # --- Layouts ---
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.record_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.stop_button)

        config_layout = QHBoxLayout()
        config_layout.addWidget(self.output_dir_button)
        config_layout.addWidget(self.output_dir_label, 1)

        # Layout para info de estado y audio
        info_layout = QVBoxLayout()
        info_layout.addWidget(self.status_label)
        info_layout.addWidget(self.timer_label)
        info_layout.addWidget(self.mic_status_label) # Añadir label mic
        info_layout.addWidget(self.loopback_status_label) # Añadir label loopback
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