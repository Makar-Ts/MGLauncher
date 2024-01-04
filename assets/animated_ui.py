from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtWidgets import QComboBox, QApplication, QStyle

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