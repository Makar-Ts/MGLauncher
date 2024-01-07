# pylint: disable=line-too-long, invalid-name, import-error, multiple-imports, unspecified-encoding, broad-exception-caught, trailing-whitespace, no-name-in-module, unused-import

from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal, Qt, QSize, QEvent
from PyQt5.QtWidgets import QComboBox, QApplication, QStyle, QListWidget, QListWidgetItem, QLabel, QVBoxLayout, QWidget, QPushButton

class AnimatedComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.animation = QPropertyAnimation(self, b"borderLeftWidth")
        self.animation.setDuration(60)  # 0.5s
        self.animation.setStartValue(1)  # 1px
        self.animation.setEndValue(10)  # 10px
        self.animation.setEasingCurve(QEasingCurve.Linear)

        self.installEventFilter(self)
        
        self.currentIndexChanged.connect(self.start_reverse_animation)

    def eventFilter(self, source, event):
        if event.type() == event.HoverEnter:
            self.animation.setDirection(QPropertyAnimation.Forward)
            self.animation.start()
        elif event.type() == event.HoverLeave:
            self.animation.setDirection(QPropertyAnimation.Backward)
            self.animation.start()
        return super().eventFilter(source, event)

    def start_reverse_animation(self):
        self.animation.setDirection(QPropertyAnimation.Backward)
        self.animation.start()

    @pyqtProperty(int)
    def borderWidth(self):
        return self.style().pixelMetric(QStyle.PM_ComboBoxFrameWidth)

    @borderWidth.setter
    def borderLeftWidth(self, value):
        self.setStyleSheet(f"QComboBox {{ border-left: {value}px solid #444; }}")

class CustomWidgetItem(QListWidgetItem, QWidget):
    def __init__(self, text):
        super(CustomWidgetItem, self).__init__()

        self.widget = QLabel(text)
        self.widget.parentWidget = self
        self.widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def enterEvent(self, QEvent):
        print("Enter event")
        self.setSizeHint(QSize(self.sizeHint().width(), self.sizeHint().height() + 50))

    def leaveEvent(self, QEvent):
        self.setSizeHint(self.widget.sizeHint())