# src/screen_recorder/core/ffmpeg_runner.py

import subprocess
import shutil
import os
import sys
import time

def find_ffmpeg_path(config_path: str | None = None) -> str | None:
    """
    Busca el ejecutable de FFmpeg.

    Primero intenta usar la ruta proporcionada en 'config_path'.
    Si no es válida o no se proporciona, busca 'ffmpeg' en el PATH del sistema.

    Args:
        config_path: Ruta potencial al ejecutable de ffmpeg desde la configuración.

    Returns:
        Ruta completa al ejecutable de ffmpeg encontrado, o None si no se encuentra.
    """
    # 1. Intentar con la ruta de configuración
    if config_path and os.path.isfile(config_path):
        # Podríamos añadir una verificación más robusta aquí (ej. ejecutar ffmpeg -version)
        print(f"Usando FFmpeg desde ruta configurada: {config_path}")
        return config_path

    # 2. Intentar buscar en el PATH del sistema
    print("Buscando FFmpeg en el PATH del sistema...")
    system_path = shutil.which('ffmpeg')
    if system_path:
        print(f"FFmpeg encontrado en el PATH: {system_path}")
        return system_path

    print("FFmpeg no encontrado en config ni en PATH.", file=sys.stderr)
    return None


class FFmpegRunner:
    """
    Gestiona la ejecución del proceso FFmpeg para grabación.
    """
    def __init__(self, ffmpeg_path: str):
        """
        Inicializa el runner con la ruta a FFmpeg.

        Args:
            ffmpeg_path: Ruta completa al ejecutable de FFmpeg.
        """
        self.ffmpeg_path = ffmpeg_path
        self.process: subprocess.Popen | None = None
        self.ready = os.path.isfile(self.ffmpeg_path)
        if not self.ready:
            print(f"Error: La ruta de FFmpeg proporcionada no es válida: {self.ffmpeg_path}", file=sys.stderr)

    def start_recording(self, output_path: str, ffmpeg_cmd_args: list[str]) -> bool:
        """
        Inicia un proceso FFmpeg con los argumentos dados.

        Args:
            output_path: Ruta completa del archivo de salida.
            ffmpeg_cmd_args: Lista de argumentos para FFmpeg (excluyendo el propio ejecutable).

        Returns:
            True si el proceso se inició correctamente, False en caso contrario.
        """
        if not self.ready:
            print("FFmpegRunner no está listo (ruta inválida).", file=sys.stderr)
            return False
        if self.process is not None:
            print("FFmpegRunner ya tiene un proceso activo.", file=sys.stderr)
            return False

        command = [self.ffmpeg_path] + ffmpeg_cmd_args
        print(f"Ejecutando comando FFmpeg: {' '.join(command)}")

        try:
            # Ocultar ventana de consola en Windows
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW

            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,     # Para poder enviar 'q' para detener
                stdout=subprocess.DEVNULL, # Ocultar salida estándar de ffmpeg
                stderr=subprocess.DEVNULL, # Ocultar salida de error (podría redirigirse a log)
                creationflags=creationflags
            )
            print(f"Proceso FFmpeg iniciado con PID: {self.process.pid}")
            # Pequeña pausa para ver si falla inmediatamente
            time.sleep(0.5)
            if self.process.poll() is not None:
                print(f"Error: Proceso FFmpeg terminó inesperadamente con código {self.process.returncode}", file=sys.stderr)
                self.process = None
                return False
            return True
        except (FileNotFoundError, OSError, ValueError) as e:
            print(f"Error al iniciar FFmpeg: {e}", file=sys.stderr)
            self.process = None
            return False

    def stop_recording(self) -> bool:
        """
        Intenta detener el proceso FFmpeg en ejecución enviando 'q'.
        Si falla, usa terminate/kill.

        Returns:
            True si el proceso se detuvo (o no estaba corriendo), False si hubo problemas graves.
        """
        if self.process is None:
            print("No hay proceso FFmpeg para detener.")
            return True # Ya está detenido

        print(f"Intentando detener proceso FFmpeg (PID: {self.process.pid})...")
        if self.process.poll() is None: # Verificar si aún está corriendo
            try:
                print("Enviando 'q' a stdin de FFmpeg...")
                self.process.stdin.write(b'q\n')
                self.process.stdin.flush()
                self.process.stdin.close() # Cerrar stdin después de escribir
                print("Esperando finalización graceful (5s)...")
                self.process.wait(timeout=5)
                print("Proceso FFmpeg detenido correctamente con 'q'.")
            except (subprocess.TimeoutExpired, OSError, BrokenPipeError, ValueError) as e:
                print(f"No se pudo detener con 'q' o timeout expiró ({e}). Intentando terminate/kill...", file=sys.stderr)
                try:
                    self.process.terminate()
                    self.process.wait(timeout=2)
                    print("Proceso FFmpeg terminado con terminate().")
                except (subprocess.TimeoutExpired, OSError) as e2:
                    print(f"terminate() falló ({e2}). Intentando kill...", file=sys.stderr)
                    try:
                        self.process.kill()
                        self.process.wait(timeout=1)
                        print("Proceso FFmpeg terminado con kill().")
                    except OSError as e3:
                        print(f"kill() falló ({e3}). El proceso podría seguir activo.", file=sys.stderr)
                        # Considerar devolver False aquí si kill falla
            except Exception as e_fatal:
                # Captura cualquier otra excepción inesperada durante la detención
                print(f"Error inesperado al intentar detener FFmpeg: {e_fatal}", file=sys.stderr)
                self.process = None # Limpiar de todas formas
                return False
        else:
            print(f"Proceso FFmpeg ya había terminado (código: {self.process.returncode}).")

        self.process = None # Limpiar la referencia al proceso
        return True