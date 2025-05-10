#!/bin/bash
# Script para ejecutar el Capturador de Audio y Video
# Versión actualizada: Mayo 2025

# Ruta absoluta al directorio del proyecto
PROYECTO_DIR="/home/anarquia/Documentos/PROGRAMAS/capturador_de_audio_video"

# Cambiar al directorio del proyecto
cd "$PROYECTO_DIR"

# Ejecutar la aplicación con Python
python3 grabar_pantalla.py

# En caso de error, mostrar mensaje
if [ $? -ne 0 ]; then
    echo "Error al ejecutar el Capturador de Audio y Video"
    echo "Directorio actual: $(pwd)"
    echo "Verificando si existe el archivo: $(ls -la grabar_pantalla.py 2>/dev/null || echo 'No existe')"
    echo ""
    echo "Presiona Enter para cerrar esta ventana..."
    read
fi

