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

# Comprobar si PySide6 está instalado o se puede instalar
python3 -c "import PySide6" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Intentando instalar PySide6 (interfaz gráfica)...${NC}"
    pip3 install --user PySide6 || {
        echo -e "${RED}Error al instalar PySide6. Intentando con apt...${NC}"
        sudo apt-get install -y python3-pyside6 || {
            echo -e "${RED}No se pudo instalar PySide6. El programa puede no funcionar correctamente.${NC}"
            echo "Puedes intentar instalarlo manualmente con: pip3 install PySide6"
        }
    }
fi

# Crear directorio de instalación
echo -e "${YELLOW}Creando directorios de instalación...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$HOME/.local/share/icons/hicolor/scalable/apps"

# Eliminar instalación anterior si existe
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Eliminando instalación anterior...${NC}"
    rm -rf "$INSTALL_DIR"/*
fi

# Copiar archivos del proyecto
echo -e "${YELLOW}Copiando archivos del proyecto...${NC}"
cp -r "$PROJECT_DIR"/* "$INSTALL_DIR/"

# Crear icono simple SVG si no existe
if [ ! -f "$SCRIPT_DIR/recorder.svg" ]; then
    echo -e "${YELLOW}Creando icono por defecto...${NC}"
    cat > "$SCRIPT_DIR/recorder.svg" << EOF
<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <rect x="2" y="2" width="44" height="44" rx="8" fill="#3949AB" />
  <rect x="8" y="8" width="32" height="24" rx="2" fill="#E0E0E0" />
  <circle cx="24" cy="36" r="6" fill="#F44336" />
  <path d="M14,28 Q14,32 14,36" stroke="#4CAF50" stroke-width="2" fill="none" />
  <path d="M12,30 Q12,32 12,34" stroke="#4CAF50" stroke-width="2" fill="none" />
  <path d="M10,31 Q10,32 10,33" stroke="#4CAF50" stroke-width="2" fill="none" />
  <path d="M34,28 Q34,32 34,36" stroke="#4CAF50" stroke-width="2" fill="none" />
  <path d="M36,30 Q36,32 36,34" stroke="#4CAF50" stroke-width="2" fill="none" />
  <path d="M38,31 Q38,32 38,33" stroke="#4CAF50" stroke-width="2" fill="none" />
</svg>
EOF
fi

# Copiar icono
cp "$SCRIPT_DIR/recorder.svg" "$ICON_PATH"

# Crear un script wrapper para ejecutar la aplicación
cat > "$INSTALL_DIR/capturador-wrapper.sh" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
python3 "$INSTALL_DIR/grabar_pantalla.py" "\$@"
EOF

# Hacer ejecutable el wrapper
chmod +x "$INSTALL_DIR/capturador-wrapper.sh"

# Modificar y copiar archivo .desktop
echo -e "${YELLOW}Configurando archivo .desktop...${NC}"
sed "s|PATHDIR|$INSTALL_DIR|g" "$DESKTOP_FILE" > "$DESKTOP_INSTALL_PATH"
# Asegurar que el comando Exec use el wrapper
sed -i "s|Exec=.*|Exec=$INSTALL_DIR/capturador-wrapper.sh|g" "$DESKTOP_INSTALL_PATH"
chmod +x "$DESKTOP_INSTALL_PATH"

# Hacer ejecutable el script principal
chmod +x "$INSTALL_DIR/grabar_pantalla.py"

# Crear enlace simbólico al ejecutable en PATH
mkdir -p "$HOME/.local/bin"
ln -sf "$INSTALL_DIR/capturador-wrapper.sh" "$HOME/.local/bin/capturador-audio-video"

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
    echo -e "${YELLOW}No se encontró requirements.txt, instalando dependencias básicas...${NC}"
    pip3 install --user PySide6 appdirs sounddevice
fi

# Intentar arreglar posibles problemas de permisos
find "$INSTALL_DIR" -type d -exec chmod 755 {} \;
find "$INSTALL_DIR" -name "*.py" -exec chmod 755 {} \;

# Verificar si podemos ejecutar el script principal
echo -e "${YELLOW}Verificando si el script principal puede ejecutarse...${NC}"
python3 -c "import sys; sys.path.insert(0, '$INSTALL_DIR'); from screen_recorder.main import run_app" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Hubo un problema al importar los módulos de la aplicación.${NC}"
    echo -e "${YELLOW}Intentando solucionar el problema...${NC}"
    
    # Crear un archivo __init__.py si no existe
    find "$INSTALL_DIR" -type d -exec touch {}/__init__.py \; 2>/dev/null
    
    # Asegurar que PYTHONPATH incluya nuestra aplicación
    echo 'export PYTHONPATH="$PYTHONPATH:'"$INSTALL_DIR"'/src"' >> "$HOME/.bashrc"
fi

# Actualizar caché de aplicaciones de escritorio
echo -e "${YELLOW}Actualizando caché de aplicaciones...${NC}"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo -e "${GREEN}¡Instalación completada!${NC}"
echo -e "Puedes iniciar la aplicación desde el menú de aplicaciones o ejecutando: capturador-audio-video"
echo -e "${YELLOW}Si encuentras problemas, prueba ejecutar desde la terminal:${NC}"
echo -e "cd $INSTALL_DIR && python3 grabar_pantalla.py"