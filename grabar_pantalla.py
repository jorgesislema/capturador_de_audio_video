
import subprocess
import datetime
import os
import signal
import sys
import shutil # Importar shutil para verificar si ffmpeg está disponible

# --- Configuración ---
# Define la resolución de la pantalla a grabar (debe coincidir con tu pantalla o ser menor)
# Ejemplo para Full HD: '1920x1080'
# Ejemplo para HD: '1280x720'
RESOLUCION = '1920x1080' # Cambia esto a tu resolución deseada

# Define la velocidad de fotogramas (frames por segundo)
FPS = 30

# Dispositivo de audio a grabar. 'default' suele funcionar para la entrada por defecto.
# Si necesitas un dispositivo específico, puedes encontrarlo con 'pactl list sources'
# y cambiar 'default' por el nombre del dispositivo (ej: 'alsa_input.pci-0000_00_1f.3.analog-stereo')
DISPOSITIVO_AUDIO = 'default'

# Carpeta donde se guardarán las grabaciones
CARPETA_SALIDA = os.path.join(os.path.expanduser("~"), "Videos", "GrabacionesPantalla")

# Prefijo para el nombre del archivo
PREFIJO_NOMBRE_ARCHIVO = "grabacion_"

# Formato del archivo de salida (mp4 es común y compatible)
FORMATO_ARCHIVO = "mp4"

# Configuración de calidad de video (para H.264)
# CRF (Constant Rate Factor): Un valor más bajo significa mejor calidad pero archivo más grande.
# Un rango común es 18-24. 21 es un buen balance para HD.
CRF_CALIDAD = 21

# Codecs
CODEC_VIDEO = 'libx264' # H.264 es muy compatible
CODEC_AUDIO = 'aac'     # AAC es común para audio en MP4

# --- Script ---

# Función para verificar si ffmpeg está instalado
def is_ffmpeg_installed():
    return shutil.which("ffmpeg") is not None

# Verificar si ffmpeg está instalado antes de continuar
if not is_ffmpeg_installed():
    print("Error: ffmpeg no está instalado.")
    print("Por favor, instala ffmpeg ejecutando en la terminal:")
    print("sudo apt update")
    print("sudo apt install ffmpeg")
    sys.exit(1) # Salir con un código de error

# Asegúrate de que la carpeta de salida exista
try:
    os.makedirs(CARPETA_SALIDA, exist_ok=True)
except OSError as e:
    print(f"Error al crear la carpeta de salida {CARPETA_SALIDA}: {e}")
    sys.exit(1)

# Genera un nombre de archivo único basado en la fecha y hora
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
nombre_archivo_salida = f"{PREFIJO_NOMBRE_ARCHIVO}{timestamp}.{FORMATO_ARCHIVO}"
ruta_completa_salida = os.path.join(CARPETA_SALIDA, nombre_archivo_salida)

print(f"Preparando para grabar la pantalla ({RESOLUCION}@{FPS}fps) y el audio ({DISPOSITIVO_AUDIO})...")
print(f"El archivo de salida será: {ruta_completa_salida}")
print("Presiona ENTER en esta terminal para detener la grabación.")

# Comando ffmpeg para grabar pantalla (usando x11grab) y audio (usando pulse)
# -y: Sobrescribir archivo de salida sin preguntar si ya existe
# -f x11grab: Usar el dispositivo de entrada x11grab para la pantalla
# -s {RESOLUCION}: Especificar la resolución de captura
# -i :0.0+0,0: Capturar la primera pantalla (:0.0) desde la esquina superior izquierda (+0,0)
# -f pulse: Usar el dispositivo de entrada pulse para el audio
# -i {DISPOSITIVO_AUDIO}: Especificar el nombre del dispositivo de audio
# -c:v {CODEC_VIDEO}: Especificar el codec de video
# -preset medium: Balance entre velocidad de codificación y compresión (otros: ultrafast, fast, slow, etc.)
# -crf {CRF_CALIDAD}: Control de calidad de video (usado con libx264)
# -pix_fmt yuv420p: Formato de pixel común para compatibilidad
# -r {FPS}: Especificar la velocidad de fotogramas
# -c:a {CODEC_AUDIO}: Especificar el codec de audio
# -loglevel error: Mostrar solo errores críticos de ffmpeg
ffmpeg_command = [
    'ffmpeg',
    '-y',
    '-f', 'x11grab',
    '-s', RESOLUCION,
    '-i', ':0.0+0,0',
    '-f', 'pulse',
    '-i', DISPOSITIVO_AUDIO,
    '-c:v', CODEC_VIDEO,
    '-preset', 'medium',
    '-crf', str(CRF_CALIDAD),
    '-pix_fmt', 'yuv420p',
    '-r', str(FPS),
    '-c:a', CODEC_AUDIO,
    '-loglevel', 'error', # O 'quiet' para menos mensajes, 'info' para más
    ruta_completa_salida
]

# Variable para guardar el proceso de ffmpeg
ffmpeg_process = None

# Handler para la señal SIGINT (Ctrl+C)
def signal_handler(sig, frame):
    print("\nSeñal de interrupción recibida (Ctrl+C). Deteniendo grabación...")
    if ffmpeg_process and ffmpeg_process.poll() is None:
        # Envía la señal de interrupción a ffmpeg para que finalice limpiamente
        # SIGINT (2) es la señal que ffmpeg espera para detener la grabación correctamente.
        ffmpeg_process.send_signal(signal.SIGINT)
        print("Esperando a que ffmpeg termine de guardar el archivo...")
        # No hacemos wait() aquí, ya que la señal handler debe ser rápida.
        # El bloque finally manejará la espera.
    # No salimos inmediatamente, el finally se encargará de limpiar.
    # sys.exit(0) # Evitar sys.exit() dentro del handler si se usa finally para cleanup

# Registrar el handler para SIGINT
original_sigint_handler = signal.signal(signal.SIGINT, signal_handler)

try:
    # Inicia el proceso de ffmpeg
    print("Iniciando grabación...")
    # stderr=subprocess.PIPE puede ser útil para capturar errores si loglevel es más bajo,
    # pero para loglevel error, print directamente funciona bien.
    ffmpeg_process = subprocess.Popen(ffmpeg_command)

    # Espera a que el usuario presione ENTER en la terminal donde se ejecuta el script
    input("")
    # Si el usuario presiona ENTER, el input() termina.
    # Luego, el bloque finally se encarga de detener ffmpeg.

except FileNotFoundError:
    # Aunque ya verificamos con shutil.which, esta es una capa extra si la llamada real falla
    print(f"Error de ejecución: Asegúrate de que 'ffmpeg' sea accesible en tu PATH.")
    sys.exit(1)
except Exception as e:
    print(f"Ocurrió un error inesperado: {e}")
    sys.exit(1)

finally:
    # Este bloque se ejecuta tanto si se presiona ENTER, como si ocurre una excepción,
    # o si se recibe Ctrl+C (después de que el signal_handler envíe SIGINT).
    if ffmpeg_process and ffmpeg_process.poll() is None:
        print("Deteniendo grabación...")
        try:
            # Envía la señal de interrupción (si no se envió ya por Ctrl+C)
            # Esto es redundante si el signal_handler ya corrió, pero seguro.
            ffmpeg_process.send_signal(signal.SIGINT)
            print("Esperando a que ffmpeg termine de guardar el archivo...")
            # Espera a que el proceso ffmpeg finalice después de recibir la señal
            ffmpeg_process.wait()
        except Exception as e:
             print(f"Error al intentar detener ffmpeg: {e}")
    elif ffmpeg_process and ffmpeg_process.returncode != 0:
         print(f"ffmpeg terminó con código de error {ffmpeg_process.returncode}.")
         print("Revisa la configuración (resolución, dispositivo de audio) o el loglevel para más detalles.")

    if os.path.exists(ruta_completa_salida) and os.path.getsize(ruta_completa_salida) > 0:
         print(f"Grabación finalizada. Archivo guardado en: {ruta_completa_salida}")
    else:
         print(f"Grabación finalizada, pero el archivo de salida ({ruta_completa_salida}) no se creó o está vacío.")
         print("Esto podría indicar un problema con la grabación. Revisa los mensajes de error anteriores.")

    # Restaurar el handler original de SIGINT al salir
    signal.signal(signal.SIGINT, original_sigint_handler)