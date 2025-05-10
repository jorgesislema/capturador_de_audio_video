#!/usr/bin/env python3
# src/screen_recorder/platform/common.py

"""
Funcionalidades comunes para todas las plataformas.
Este módulo contiene código que es independiente del sistema operativo.
"""

import sys
import platform
from typing import Dict, Any, Optional, List, Tuple

class PlatformInfo:
    """Clase para obtener información sobre la plataforma actual."""
    
    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """
        Obtiene información básica sobre el sistema.
        
        Returns:
            Dict[str, str]: Diccionario con información del sistema.
        """
        info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
        }
        
        # Información específica por plataforma
        if platform.system() == "Windows":
            info["win_edition"] = platform.win32_edition() if hasattr(platform, "win32_edition") else "Unknown"
        elif platform.system() == "Darwin":  # macOS
            info["mac_ver"] = ".".join(platform.mac_ver()[0].split(".")[:2])
        elif platform.system() == "Linux":
            try:
                import distro
                info["distro"] = distro.name(pretty=True)
            except ImportError:
                try:
                    with open("/etc/os-release") as f:
                        for line in f:
                            if line.startswith("PRETTY_NAME="):
                                info["distro"] = line.split("=")[1].strip().strip('"')
                                break
                except (FileNotFoundError, IOError):
                    info["distro"] = "Unknown Linux Distribution"
        
        return info
    
    @staticmethod
    def is_windows() -> bool:
        """Comprueba si el sistema es Windows."""
        return platform.system() == "Windows"
    
    @staticmethod
    def is_macos() -> bool:
        """Comprueba si el sistema es macOS."""
        return platform.system() == "Darwin"
    
    @staticmethod
    def is_linux() -> bool:
        """Comprueba si el sistema es Linux."""
        return platform.system() == "Linux"
    
    @staticmethod
    def get_screen_size() -> Tuple[int, int]:
        """
        Obtiene el tamaño de la pantalla principal.
        
        Returns:
            Tuple[int, int]: Ancho y alto de la pantalla en píxeles.
        """
        try:
            # Usamos Qt si está disponible
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import QRect
            
            # Necesitamos una instancia de QApplication para esto
            app = QApplication.instance()
            if not app:
                # Crear una instancia temporal
                app = QApplication([])
            
            screen = app.primaryScreen()
            geometry = screen.geometry()
            return geometry.width(), geometry.height()
        except ImportError:
            # Fallback: devolver valores comunes
            print("Advertencia: No se pudo detectar el tamaño de pantalla. Usando valores predeterminados.")
            return 1920, 1080

def get_platform_module():
    """
    Importa dinámicamente el módulo específico de la plataforma.
    
    Returns:
        module: Módulo específico para la plataforma actual.
    """
    system = platform.system().lower()
    
    if system == "windows":
        from . import windows
        return windows
    elif system == "linux":
        from . import linux
        return linux
    elif system == "darwin":  # macOS
        # Actualmente no tenemos un módulo específico para macOS
        # Podríamos crear uno en el futuro
        from . import linux  # Usar linux como fallback temporal
        print("Advertencia: Soporte específico para macOS no implementado. Usando módulo de Linux.")
        return linux
    else:
        print(f"Advertencia: Plataforma no soportada: {system}")
        from . import linux  # Usar linux como fallback para plataformas desconocidas
        return linux

if __name__ == "__main__":
    # Código de prueba
    print("Información del Sistema:")
    for key, value in PlatformInfo.get_system_info().items():
        print(f"  {key}: {value}")
    
    print(f"\nTamaño de pantalla: {PlatformInfo.get_screen_size()}")
    
    print(f"\nDetección de plataforma:")
    print(f"  Windows: {PlatformInfo.is_windows()}")
    print(f"  macOS: {PlatformInfo.is_macos()}")
    print(f"  Linux: {PlatformInfo.is_linux()}")