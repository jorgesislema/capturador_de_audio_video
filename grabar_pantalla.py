#!/usr/bin/env python3
# grabar_pantalla.py - Script ejecutable principal para el Capturador de Audio y Video

"""
Capturador de Audio y Video - Script de inicio

Este script sirve como punto de entrada conveniente para iniciar la aplicación
de grabación de pantalla. Ejecuta el módulo principal de la aplicación.
"""

import sys
import os

# Asegurar que el paquete screen_recorder sea accesible
# Esto es útil si se ejecuta el script directamente sin instalar el paquete
src_path = os.path.join(os.path.dirname(__file__), 'src')
if os.path.exists(src_path):
    sys.path.insert(0, src_path)

try:
    from screen_recorder.main import run_app
except ImportError:
    print("Error: No se pudo importar el módulo screen_recorder.")
    print("Asegúrese de que:")
    print("1. Está ejecutando este script desde el directorio raíz del proyecto, o")
    print("2. El proyecto está correctamente instalado en su entorno Python.")
    sys.exit(1)

if __name__ == "__main__":
    print("Iniciando Capturador de Audio y Video...")
    run_app()