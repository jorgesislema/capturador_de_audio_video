#!/usr/bin/env python3
# src/screen_recorder/__main__.py

"""
Punto de entrada cuando se ejecuta como módulo:
python -m screen_recorder
"""

from .main import run_app

if __name__ == "__main__":
    print("Iniciando Capturador de Audio y Video desde el módulo...")
    run_app()