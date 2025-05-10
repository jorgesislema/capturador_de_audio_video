#!/bin/bash
# Script de instalación para Capturador de Audio y Video en Linux

# Colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Directorios
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
INSTALL_DIR="$HOME/.local/share/capturador-audio-video"
DESKTOP_FILE="$SCRIPT_DIR/capturador-audio-video.desktop"
DESKTOP_INSTALL_PATH="$HOME/.local/share/applications/capturador-audio-video.desktop"
ICON_PATH="$HOME/.local/share/icons/hicolor/scalable/apps/recorder.svg"

# Verificar dependencias
echo -e "${YELLOW}Verificando dependencias...${NC}"

# Verificar Python
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}Error: Python 3 no está instalado${NC}"
    echo "Por favor, instala Python 3 con: sudo apt install python3 python3-pip"
    exit 1
fi

# Verificar FFmpeg
if ! command -v ffmpeg &>/dev/null; then
    echo -e "${RED}Error: FFmpeg no está instalado${NC}"
    echo "Por favor, instala FFmpeg con: sudo apt install ffmpeg"
    exit 1
fi

# Crear directorio de instalación
echo -e "${YELLOW}Creando directorios de instalación...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$HOME/.local/share/icons/hicolor/scalable/apps"

# Copiar archivos del proyecto
echo -e "${YELLOW}Copiando archivos del proyecto...${NC}"
cp -r "$PROJECT_DIR"/* "$INSTALL_DIR/"

# Crear icono simple SVG si no existe
if [ ! -f "$PROJECT_DIR/packaging/linux/recorder.svg" ]; then
    echo -e "${YELLOW}Creando icono por defecto...${NC}"
    cat > "$SCRIPT_DIR/recorder.svg" << EOF
<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <circle cx="24" cy="24" r="20" fill="#2196F3"/>
  <circle cx="24" cy="24" r="16" fill="#1565C0"/>
  <circle cx="24" cy="24" r="8" fill="#FF0000"/>
</svg>
EOF
fi

# Copiar icono
cp "$SCRIPT_DIR/recorder.svg" "$ICON_PATH"

# Modificar y copiar archivo .desktop
echo -e "${YELLOW}Configurando archivo .desktop...${NC}"
sed "s|PATHDIR|$INSTALL_DIR|g" "$DESKTOP_FILE" > "$DESKTOP_INSTALL_PATH"
chmod +x "$DESKTOP_INSTALL_PATH"

# Hacer ejecutable el script principal
chmod +x "$INSTALL_DIR/grabar_pantalla.py"

# Crear enlace simbólico al ejecutable en PATH
mkdir -p "$HOME/.local/bin"
ln -sf "$INSTALL_DIR/grabar_pantalla.py" "$HOME/.local/bin/capturador-audio-video"

# Verificar que .local/bin esté en PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}Añadiendo ~/.local/bin a tu PATH...${NC}"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo 'Recuerda reiniciar tu terminal o ejecutar: source ~/.bashrc'
fi

# Instalar dependencias de Python
echo -e "${YELLOW}Instalando dependencias de Python...${NC}"
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    pip3 install --user -r "$INSTALL_DIR/requirements.txt"
else
    pip3 install --user PySide6 appdirs sounddevice
fi

# Actualizar caché de aplicaciones de escritorio
echo -e "${YELLOW}Actualizando caché de aplicaciones...${NC}"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo -e "${GREEN}¡Instalación completada!${NC}"
echo -e "Puedes iniciar la aplicación desde el menú de aplicaciones o ejecutando: capturador-audio-video"