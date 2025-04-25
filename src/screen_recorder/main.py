# src/screen_recorder/main.py

import sys
from PySide6.QtWidgets import QApplication

# Importamos la ventana principal desde nuestro módulo gui
# Usamos import relativo porque main.py está dentro del paquete screen_recorder
from .gui import MainWindow
# from . import __version__ # Podríamos importar la versión si la necesitáramos aquí

def run_app() -> None:
    """
    Inicializa y ejecuta la aplicación Qt.
    """
    # Crear la instancia de la aplicación Qt
    # sys.argv permite pasar argumentos de línea de comandos a Qt, si es necesario.
    app = QApplication(sys.argv)

    # Crear e mostrar la ventana principal
    window = MainWindow()
    window.show()

    # Iniciar el bucle de eventos de la aplicación.
    # sys.exit() asegura que el código de salida de la aplicación se devuelva correctamente.
    sys.exit(app.exec())

# --- Bloque de ejecución principal ---
# Este bloque se ejecuta cuando el script es llamado directamente
# o a través de `python -m screen_recorder.main` (si __main__.py lo llama)
# Por ahora, para cumplir con la ejecución directa simple como se pide:
if __name__ == "__main__":
    # print(f"Screen Recorder Version: {__version__}") # Ejemplo si quisiéramos mostrar versión
    run_app()
__version__ = "0.1.0"