capturador_de_audio_video/
├── docs/                    # Documentación del proyecto
│   ├── architecture.md      # Documentación de arquitectura
│   ├── development_setup.md # Configuración para desarrollo
│   └── user_guide.md        # Guía de usuario
├── packaging/               # Scripts de empaquetado
│   └── linux/
│       └── build.sh         # Script de construcción para Linux
├── src/                     # Código fuente principal
│   └── screen_recorder/     # Paquete principal de la aplicación
│       ├── core/            # Lógica principal y backend
│       ├── gui/             # Interfaz gráfica de usuario
│       ├── platform/        # Código específico por plataforma
│       └── utils/           # Utilidades generales
├── tests/                   # Pruebas automatizadas
│   ├── core/                # Pruebas para los componentes core
│   ├── gui/                 # Pruebas para la interfaz gráfica
│   └── utils/               # Pruebas para las utilidades
├── grabar_pantalla.py       # Script ejecutable principal
├── pyproject.toml           # Configuración del proyecto
└── README.md                # Documentación básica