# Arquitectura del Capturador de Audio y Video

Este documento describe la arquitectura y diseño técnico del proyecto Capturador de Audio y Video.

## Visión General

El Capturador de Audio y Video es una aplicación multiplataforma para grabar la pantalla con audio del sistema y micrófono, utilizando FFmpeg como backend de grabación y PySide6 (Qt) como framework de interfaz gráfica.

## Componentes Principales

### 1. Módulo GUI (`gui/`)

- **MainWindow**: Ventana principal de la aplicación con controles para iniciar/detener grabación.
- Gestiona el estado de la aplicación (IDLE, RECORDING, PAUSED) y muestra estado actual.
- Proporciona interfaz para configuración básica (directorios de salida, etc.).

### 2. Módulo Core (`core/`)

- **Recorder**: Clase principal que orquesta el proceso de grabación.
- **FFmpegRunner**: Maneja la interacción directa con el ejecutable FFmpeg.
- **ConfigManager**: Gestiona la configuración persistente de la aplicación.
- **AudioUtils**: Proporciona funciones para detectar y configurar dispositivos de audio.

### 3. Módulo Platform (`platform/`)

- Implementa código específico por plataforma para Windows, Linux y potencialmente macOS.
- Adapta las llamadas a FFmpeg y la detección de audio según el sistema operativo.

### 4. Módulo Utils (`utils/`)

- **Logger**: Sistema de logging para diagnóstico y depuración.
- Funciones de utilidad general reutilizables.

## Flujo de Datos

1. **Entrada de Usuario** → GUI (MainWindow) → Recorder → FFmpegRunner → FFmpeg (proceso externo)
2. **Salida de FFmpeg** → Archivo MP4 en el directorio seleccionado

## Diagrama de Clases Simplificado

```
+-----------------+       +------------------+        +------------------+
| MainWindow      |------>| Recorder         |------->| FFmpegRunner     |
| - record_button |       | - start()        |        | - process        |
| - stop_button   |       | - stop()         |        | - start_recording|
| - config        |       | - _init_ffmpeg() |        | - stop_recording |
+-----------------+       +------------------+        +------------------+
        |                         |                            |
        v                         v                            v
+-----------------+       +------------------+        +------------------+
| ConfigManager   |       | AudioUtils       |        | Platform-specific|
| - load_config() |       | - get_devices()  |        | - _get_cmd_args()|
| - save_config() |       | - find_loopback()|        | - OS adaptations |
+-----------------+       +------------------+        +------------------+
```

## Gestión de Estado

La aplicación utiliza un patrón de máquina de estados simple:

- **IDLE**: Estado inicial y después de detener una grabación.
- **RECORDING**: Durante una grabación activa.
- **PAUSED**: (Planificado para futuras versiones) Grabación pausada temporalmente.

## Conceptos Técnicos Clave

### Captura de Video

- Utiliza el backend `gdigrab` (Windows) o `x11grab` (Linux) de FFmpeg para capturar la pantalla.
- La calidad de video y framerate son configurables.

### Captura de Audio

- **Audio del Micrófono**: Captura directa del dispositivo de entrada seleccionado.
- **Audio del Sistema (Loopback)**: 
  - En Windows: Utiliza dispositivos loopback como "Stereo Mix"
  - En Linux: Utiliza módulos de ALSA o PulseAudio para loopback

### Arquitectura Multiplataforma

El diseño sigue estos principios para compatibilidad multiplataforma:

1. **Abstracción de Plataforma**: Código específico aislado en el módulo `platform/`
2. **Detección Automática**: El sistema detecta dispositivos y configuraciones disponibles
3. **Configuración Adaptativa**: Se adapta a las limitaciones de cada sistema operativo

## Configuración Persistente

Utiliza el módulo `appdirs` para guardar la configuración en ubicaciones estándar según el sistema:

- Carpeta de salida predeterminada
- Dispositivos de audio preferidos
- Ajustes de calidad de grabación 
- Rutas a herramientas externas (FFmpeg)

## Extensibilidad

El diseño modular permite expandirse en el futuro con:

- Soporte para grabación de áreas específicas de la pantalla
- Grabación de webcam en imagen-en-imagen
- Streaming en vivo
- Programación de grabaciones
- Plugins de post-procesamiento