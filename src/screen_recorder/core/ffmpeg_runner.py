#!/usr/bin/env python3
# src/screen_recorder/core/ffmpeg_runner.py

"""
FFmpegRunner - Módulo para interactuar con FFmpeg.
Proporciona una interfaz para iniciar y detener procesos de FFmpeg.
"""

import os
import sys
import signal
import platform
import subprocess
from typing import List, Optional, Union

def find_ffmpeg_path(custom_path: Optional[str] = None) -> Optional[str]:
    """
    Busca el ejecutable de FFmpeg en el sistema.
    
    Args:
        custom_path (str, opcional): Ruta personalizada a FFmpeg si se proporciona.
        
    Returns:
        Optional[str]: Ruta al ejecutable de FFmpeg o None si no se encuentra.
    """
    # 1. Verificar la ruta personalizada si se proporciona
    if custom_path and os.path.isfile(custom_path) and os.access(custom_path, os.X_OK):
        return custom_path
    
    # 2. Buscar en el PATH
    ffmpeg_names = ["ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"]
    
    for path_dir in os.environ.get("PATH", "").split(os.pathsep):
        for name in ffmpeg_names:
            ffmpeg_path = os.path.join(path_dir, name)
            if os.path.isfile(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
                return ffmpeg_path
    
    # 3. Verificar ubicaciones comunes según la plataforma
    if platform.system() == "Windows":
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        common_paths = [
            os.path.join(program_files, "FFmpeg", "bin", "ffmpeg.exe"),
            os.path.join(program_files_x86, "FFmpeg", "bin", "ffmpeg.exe"),
        ]
    elif platform.system() == "Darwin":  # macOS
        common_paths = [
            "/usr/local/bin/ffmpeg",
            "/opt/homebrew/bin/ffmpeg",
            "/opt/local/bin/ffmpeg",
        ]
    else:  # Linux/Unix
        common_paths = [
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "/opt/ffmpeg/bin/ffmpeg",
        ]
    
    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    
    # 4. No se pudo encontrar FFmpeg
    return None

class FFmpegRunner:
    """Gestiona la ejecución de procesos FFmpeg para grabación."""
    
    def __init__(self, ffmpeg_path: Optional[str] = None) -> None:
        """
        Inicializa el runner de FFmpeg.
        
        Args:
            ffmpeg_path (str, opcional): Ruta al ejecutable de FFmpeg.
                                         Si es None, intentará buscarlo.
        """
        self.ffmpeg_path = ffmpeg_path or find_ffmpeg_path()
        self.process: Optional[subprocess.Popen] = None
        self.output_file: Optional[str] = None
        self.ready = self.ffmpeg_path is not None
        
        if not self.ready:
            print("Error: No se pudo encontrar FFmpeg.", file=sys.stderr)
        else:
            self._check_version()
    
    def _check_version(self) -> None:
        """Verifica la versión de FFmpeg y registra información útil."""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                check=True
            )
            version_info = result.stdout.split('\n')[0]
            print(f"FFmpeg encontrado: {version_info}")
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"Error al verificar la versión de FFmpeg: {e}", file=sys.stderr)
            self.ready = False
    
    def start_recording(self, output_file: str, ffmpeg_args: List[str]) -> bool:
        """
        Inicia un proceso de grabación con FFmpeg.
        
        Args:
            output_file (str): Ruta donde se guardará el archivo de salida.
            ffmpeg_args (List[str]): Argumentos para FFmpeg (sin incluir el propio 'ffmpeg').
            
        Returns:
            bool: True si el proceso se inició correctamente, False en caso contrario.
        """
        if not self.ready:
            print("Error: FFmpeg no está listo.", file=sys.stderr)
            return False
        
        if self.process is not None:
            print("Error: Ya hay un proceso de grabación en curso.", file=sys.stderr)
            return False
        
        # Asegurar que el directorio de salida exista
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError as e:
                print(f"Error al crear directorio de salida: {e}", file=sys.stderr)
                return False
        
        # Construir comando completo
        cmd = [self.ffmpeg_path] + ffmpeg_args
        
        try:
            # Imprimir comando para depuración (sin mostrar toda la ruta)
            print("Ejecutando:", ' '.join(['ffmpeg'] + ffmpeg_args))
            
            # Iniciar proceso
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False  # Mantener como binario para evitar problemas de codificación
            )
            
            self.output_file = output_file
            print(f"Proceso FFmpeg iniciado (PID: {self.process.pid})")
            print(f"Guardando en: {self.output_file}")
            return True
            
        except Exception as e:
            print(f"Error al iniciar proceso FFmpeg: {e}", file=sys.stderr)
            self.process = None
            self.output_file = None
            return False
    
    def stop_recording(self) -> bool:
        """
        Detiene el proceso de grabación en curso.
        
        Returns:
            bool: True si el proceso se detuvo correctamente, False en caso contrario.
        """
        if self.process is None:
            print("No hay proceso de grabación activo.")
            return False
        
        try:
            print("Enviando señal de terminación a FFmpeg...")
            
            # Enviar 'q' a stdin es la forma más segura de terminar FFmpeg
            if self.process.stdin:
                try:
                    self.process.stdin.write(b'q')
                    self.process.stdin.flush()
                except (BrokenPipeError, IOError):
                    pass  # Ignorar si el pipe ya está cerrado
            
            # Esperar un tiempo razonable para terminación normal
            try:
                self.process.wait(timeout=3)
                print("FFmpeg terminado normalmente.")
            except subprocess.TimeoutExpired:
                print("FFmpeg no respondió a 'q', enviando señal de interrupción...")
                
                # En Windows, terminate() y kill() son equivalentes
                if platform.system() == "Windows":
                    self.process.terminate()
                else:
                    # En Unix/Linux, enviar SIGINT (similar a Ctrl+C)
                    self.process.send_signal(signal.SIGINT)
                
                try:
                    self.process.wait(timeout=3)
                    print("FFmpeg terminado con señal de interrupción.")
                except subprocess.TimeoutExpired:
                    print("FFmpeg no responde, forzando terminación...")
                    self.process.kill()
                    self.process.wait()
                    print("FFmpeg terminado forzosamente.")
            
            # Capturar cualquier error en la salida
            if self.process.stderr:
                stderr_data = self.process.stderr.read()
                if stderr_data:
                    # Mostrar solo las últimas líneas relevantes
                    try:
                        stderr_text = stderr_data.decode('utf-8', errors='replace')
                        last_lines = '\n'.join(stderr_text.split('\n')[-5:])
                        print(f"Últimas líneas de FFmpeg:\n{last_lines}")
                    except Exception:
                        pass
            
            # Verificar si el archivo de salida se creó correctamente
            if self.output_file and os.path.exists(self.output_file):
                file_size = os.path.getsize(self.output_file)
                print(f"Archivo grabado: {self.output_file} ({file_size / 1024 / 1024:.1f} MB)")
                
                if file_size == 0:
                    print("Advertencia: El archivo de salida tiene tamaño cero.", file=sys.stderr)
            else:
                print("Advertencia: No se encontró el archivo de salida.", file=sys.stderr)
            
            # Reiniciar estado
            self.process = None
            temp_file = self.output_file
            self.output_file = None
            
            return True
            
        except Exception as e:
            print(f"Error al detener proceso FFmpeg: {e}", file=sys.stderr)
            # Reiniciar estado incluso con error
            self.process = None
            self.output_file = None
            return False

if __name__ == "__main__":
    # Código de prueba para desarrollo
    ffmpeg_path = find_ffmpeg_path()
    if ffmpeg_path:
        print(f"FFmpeg encontrado en: {ffmpeg_path}")
        
        runner = FFmpegRunner(ffmpeg_path)
        # Aquí podrías agregar código para probar grabaciones de prueba
    else:
        print("No se pudo encontrar FFmpeg.")