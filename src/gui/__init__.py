# src/screen_recorder/gui/__init__.py

"""
Módulo de la Interfaz Gráfica de Usuario (GUI).

Este archivo __init__.py permite importar clases importantes directamente
desde el paquete 'gui'.
"""

# Hacemos que MainWindow esté disponible al importar 'gui'
from .main_window import MainWindow

# Podríamos añadir aquí otras ventanas o widgets principales si los hubiera
# Ejemplo: from .settings_dialog import SettingsDialog

__all__ = ["MainWindow"] # Define qué se importa con 'from .gui import *' (buena práctica)