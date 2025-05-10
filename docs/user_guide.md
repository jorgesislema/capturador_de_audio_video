# Guía de Usuario - Capturador de Audio y Video

Esta guía describe cómo utilizar la aplicación Capturador de Audio y Video para grabar la pantalla con audio.

## Primeros Pasos

### Instalación

Siga las instrucciones de instalación en el [README.md](../README.md) para instalar la aplicación y sus dependencias.

### Inicio de la Aplicación

Puede iniciar la aplicación de dos formas:

1. Ejecutando el script `grabar_pantalla.py`:
   ```bash
   python grabar_pantalla.py
   ```

2. Como un módulo Python:
   ```bash
   python -m screen_recorder.main
   ```

## Interfaz de Usuario

La interfaz principal incluye:

![Captura de la interfaz](images/interface.png)

1. **Panel de Estado**: Muestra el estado actual y el tiempo de grabación
2. **Indicadores de Audio**: Muestran el estado de los dispositivos de audio
3. **Selector de Carpeta**: Para elegir dónde guardar las grabaciones
4. **Botones de Control**: Para iniciar y detener grabaciones

## Funciones Básicas

### Seleccionar Carpeta de Salida

1. Haga clic en el botón "Carpeta Salida..."
2. Navegue y seleccione la carpeta donde desee guardar sus grabaciones
3. Esta selección se guardará para futuras sesiones

### Iniciar Grabación

1. Haga clic en el botón "Grabar"
2. La aplicación comenzará a grabar inmediatamente
3. El contador de tiempo se activará, indicando la duración de la grabación

### Detener Grabación

1. Haga clic en el botón "Detener"
2. La grabación se procesará y guardará automáticamente
3. Se mostrará un mensaje con la ubicación del archivo guardado

## Configuración de Audio

### Verificación de Dispositivos

Los indicadores de audio muestran:
- **Micrófono**: Estado actual (activado/desactivado) y dispositivo seleccionado
- **Audio Sistema**: Estado del audio del sistema (loopback)

### Habilitar Stereo Mix (Windows)

Para capturar el audio del sistema en Windows:

1. Haga clic derecho en el icono de volumen en la barra de tareas
2. Seleccione "Abrir configuración de sonido"
3. En "Dispositivos de entrada", busque "Stereo Mix" o similar
4. Si no aparece, haga clic derecho en un área vacía y active "Mostrar dispositivos deshabilitados"
5. Habilite "Stereo Mix"

### Configuración de PulseAudio (Linux)

Para captura de audio del sistema en Linux:

1. Instale pavucontrol si no lo tiene:
   ```bash
   sudo apt install pavucontrol
   ```
2. Durante la grabación, abra pavucontrol
3. Vaya a la pestaña "Grabación"
4. Para la entrada de FFmpeg, seleccione "Monitor of [su dispositivo de salida]"

## Resolución de Problemas

### FFmpeg no Encontrado

Si recibe el error "FFmpeg no encontrado":

1. Asegúrese de que FFmpeg esté instalado en su sistema
2. Para comprobar, abra una terminal y ejecute:
   ```bash
   ffmpeg -version
   ```
3. Si no está instalado, siga las instrucciones en [README.md](../README.md)

### Problemas con el Audio

Si no se captura el audio correctamente:

1. **Sin Audio del Micrófono**:
   - Verifique que su micrófono funciona en otras aplicaciones
   - Asegúrese de que no está silenciado en el mezclador del sistema

2. **Sin Audio del Sistema**:
   - Windows: Verifique que "Stereo Mix" está habilitado
   - Linux: Configure correctamente el monitor en PulseAudio
   - Algunas tarjetas de sonido no soportan loopback nativo

### Archivos de Salida Grandes

Para reducir el tamaño de los archivos:

1. Use herramientas de post-procesamiento como Handbrake
2. Considere comprimir solo después de editar para mantener la calidad

## Consejos y Trucos

- **Espacio en Disco**: Asegúrese de tener suficiente espacio libre antes de iniciar grabaciones largas
- **Rendimiento**: Cerrar aplicaciones innecesarias puede mejorar la calidad de la grabación
- **Previsualizaciones**: Use la herramienta integrada en FFmpeg para ver rápidamente sus grabaciones:
  ```bash
  ffplay archivo_grabado.mp4
  ```

## Próximas Características

Estamos trabajando en:
- Grabación de regiones específicas de la pantalla
- Inclusión de webcam como picture-in-picture
- Programación de grabaciones
- Configuración avanzada de calidad

## Soporte

Si encuentra problemas o tiene sugerencias, por favor abra un issue en nuestro repositorio de GitHub.