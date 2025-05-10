# Configuración del Entorno de Desarrollo

Este documento describe cómo configurar un entorno de desarrollo para trabajar en el proyecto "Capturador de Audio y Video".

## Requisitos Previos

- Python 3.9 o superior
- FFmpeg instalado en el sistema
- Dispositivos de audio (para pruebas)

## Configuración del Entorno Virtual

### Usando venv

```bash
# Crear el entorno virtual
python3 -m venv .venv

# Activar el entorno virtual (Linux/macOS)
source .venv/bin/activate

# Activar el entorno virtual (Windows)
# .venv\Scripts\activate
```

### Usando Poetry (recomendado)

```bash
# Instalar Poetry si no lo tienes
pip install poetry

# Configurar Poetry para crear entorno virtual en el directorio del proyecto
poetry config virtualenvs.in-project true

# Instalar dependencias
poetry install
```

## Instalación de Dependencias

Si no estás usando Poetry, puedes instalar las dependencias con pip:

```bash
pip install -r requirements.txt
```

## Instalación de FFmpeg

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

### Arch Linux
```bash
sudo pacman -S ffmpeg
```

### Fedora
```bash
sudo dnf install ffmpeg
```

### Windows
Descarga desde [ffmpeg.org](https://ffmpeg.org/download.html) y añade al PATH.

## Configuración del IDE

### VS Code
Extensiones recomendadas:
- Python
- Pylance
- Ruff
- Python Test Explorer

Configuración recomendada (settings.json):
```json
{
    "python.formatting.provider": "none",
    "editor.formatOnSave": true,
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": false,
    "python.linting.ruffEnabled": true,
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll": true
        }
    }
}
```

## Verificación de la Configuración

Para verificar que tu entorno está correctamente configurado:

```bash
# Ejecutar pruebas
pytest

# Verificar tipos con mypy
mypy src/

# Ejecutar linting
ruff check src/
```

## Ejecución del Proyecto en Desarrollo

```bash
# Usando Python directamente
python -m screen_recorder.main

# O usando el script de conveniencia
python grabar_pantalla.py
```

## Estructura del Proyecto

```
capturador_de_audio_video/
├── docs/                    # Documentación
├── packaging/               # Scripts de empaquetado
├── src/                     # Código fuente principal
│   └── screen_recorder/     # Paquete principal
│       ├── core/            # Lógica principal
│       ├── gui/             # Interfaz gráfica
│       ├── platform/        # Código específico por plataforma
│       └── utils/           # Utilidades generales
├── tests/                   # Pruebas automatizadas
└── grabar_pantalla.py       # Script ejecutable principal
```