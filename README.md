# Capturador de Audio y Video

Una aplicación multiplataforma para grabar la pantalla con audio del sistema y/o micrófono, desarrollada en Python usando PySide6 (Qt) y FFmpeg.

![Estado: En Desarrollo](https://img.shields.io/badge/Estado-En%20Desarrollo-yellow)

## Características

- 📹 Grabación de pantalla completa
- 🎤 Captura de audio del micrófono
- 🔊 Captura de audio del sistema (loopback)
- 💾 Formato de salida MP4 de alta calidad
- 🖥️ Interfaz gráfica intuitiva
- 🌐 Diseñado para funcionar en diferentes plataformas

## Requisitos

- Python 3.9 o superior
- FFmpeg instalado en el sistema
- PySide6 y otras dependencias listadas en `requirements.txt`

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/capturador_de_audio_video.git
cd capturador_de_audio_video
```

### 2. Configurar entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Instalar FFmpeg (si aún no lo tienes)

- **Ubuntu/Debian**: `sudo apt install ffmpeg`
- **Windows**: Descargar desde [ffmpeg.org](https://ffmpeg.org/download.html)
- **macOS**: `brew install ffmpeg`

## Uso

```bash
python grabar_pantalla.py
```

O alternativamente:

```bash
python -m screen_recorder.main
```

## Configuración

La aplicación guarda la configuración de usuario en:
- **Linux**: `~/.config/capturador_de_audio_video/config.json`
- **Windows**: `%APPDATA%\capturador_de_audio_video\config.json`
- **macOS**: `~/Library/Application Support/capturador_de_audio_video/config.json`

## Desarrollo

Para información sobre cómo configurar un entorno de desarrollo, consulta la [guía de configuración de desarrollo](docs/development_setup.md).

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Ver archivo [LICENSE](LICENSE) para más detalles.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, sigue estas pautas:

1. Haz un fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/nueva-caracteristica`)
3. Haz tus cambios y asegúrate de que las pruebas pasan
4. Envía un pull request

## Capturas de Pantalla

*Próximamente*

## Agradecimientos

- [FFmpeg](https://ffmpeg.org/) - El backend de captura de audio/video
- [Qt/PySide6](https://www.qt.io/) - Framework de interfaz gráfica
- Todos los contribuyentes y probadores