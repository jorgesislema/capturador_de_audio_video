# src/screen_recorder/gui/area_selection.py

"""
Componente para seleccionar un área específica de la pantalla para captura.
"""

from PySide6.QtWidgets import QDialog, QApplication
from PySide6.QtGui import QPainter, QColor, QPixmap
from PySide6.QtCore import Qt, QPoint, QRect

class AreaSelectionDialog(QDialog):
    """Diálogo mejorado para seleccionar un área de la pantalla para captura."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        
        # Cubrir toda la pantalla disponible
        available_geometry = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(available_geometry)
        
        # Capturar la pantalla completa para mostrar como fondo
        self.screen_pixmap = QApplication.primaryScreen().grabWindow(0)
        
        # Variables para seguimiento de selección
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.is_selecting = False
        self.selection_rect = QRect()
        
        # Mensaje de instrucción
        self.instruction_text = "Haz clic y arrastra para seleccionar el área a capturar"
        self.dimension_text = "Dimensiones: 0 × 0"
        self.cancel_text = "Presiona ESC para cancelar"
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.end_point = self.start_point
            self.is_selecting = True
            self.update()
    
    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_point = event.pos()
            # Actualizar texto de dimensiones
            select_rect = QRect(self.start_point, self.end_point).normalized()
            self.dimension_text = f"Dimensiones: {select_rect.width()} × {select_rect.height()}"
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.end_point = event.pos()
            self.is_selecting = False
            self.selection_rect = QRect(self.start_point, self.end_point).normalized()
            # Si la selección es demasiado pequeña, no la aceptamos
            if self.selection_rect.width() > 10 and self.selection_rect.height() > 10:
                self.accept()
            else:
                # Reiniciar para una nueva selección
                self.dimension_text = "Dimensiones: 0 × 0"
                self.update()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
    
    def paintEvent(self, event):
        """Dibuja la interfaz de selección de área con la captura de pantalla de fondo."""
        painter = QPainter(self)
        
        # Dibujar la captura de pantalla como fondo
        painter.drawPixmap(self.rect(), self.screen_pixmap)
        
        # Aplicar una capa semi-transparente sobre toda la pantalla
        overlay_color = QColor(0, 0, 0, 128)  # RGBA: negro semi-transparente
        painter.fillRect(self.rect(), overlay_color)
        
        # Mostrar el área seleccionada (transparente)
        if self.is_selecting or not self.selection_rect.isEmpty():
            select_rect = QRect(self.start_point, self.end_point).normalized()
            
            # Mostrar la parte de la captura original en la selección
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.drawPixmap(select_rect, self.screen_pixmap, select_rect)
            
            # Dibujar un borde alrededor de la selección
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(QColor(255, 255, 255, 200))  # Blanco semi-transparente
            painter.drawRect(select_rect)
        
        # Dibujar instrucciones y dimensiones
        painter.setPen(QColor(255, 255, 255, 255))
        painter.drawText(10, 30, self.instruction_text)
        painter.drawText(10, 60, self.dimension_text)
        painter.drawText(10, 90, self.cancel_text)
    
    def get_selection(self):
        """Retorna el rectángulo de selección."""
        return self.selection_rect
    
    @staticmethod
    def get_area_selection():
        """Método estático para mostrar el diálogo y obtener la selección."""
        dialog = AreaSelectionDialog()
        if dialog.exec() == QDialog.Accepted:
            return dialog.get_selection()
        return None