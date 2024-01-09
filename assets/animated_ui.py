# pylint: disable=line-too-long, invalid-name, import-error, multiple-imports, unspecified-encoding, broad-exception-caught, trailing-whitespace, no-name-in-module, unused-import

from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal, Qt, QSize, QEvent
from PyQt5.QtWidgets import QComboBox, QApplication, QStyle, QListWidget, QListWidgetItem, QLabel, QVBoxLayout, QWidget, QPushButton, QDialog

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

class PopupWindow(QDialog):
    def __init__(self):
        super(PopupWindow, self).__init__()
        
    def setup(self, title, message):
        self.setWindowTitle(title)
        self.resize(200, 60)

        # add a label with the message
        self.label = QLabel(message, self)
        self.label.move(20, 20)
        self.label.setFixedSize(QSize(160, 40))
        
        self.resize(self.label.fontMetrics().boundingRect(self.label.text()).width()+40, 60)

        # add a button to close the window
        self.button = QPushButton('Ok', self)
        self.button.move(120, 60)
        self.button.clicked.connect(self.close)

        # set layout
        self.self_layout = QVBoxLayout()
        self.self_layout.addWidget(self.label)
        self.self_layout.addWidget(self.button)
        self.setLayout(self.self_layout)
    
    def update(self, title, message):
        self.setWindowTitle(title)
        self.label.setText(message)
        
        size = self.label.fontMetrics().boundingRect(self.label.text()).width()
        
        self.label.setFixedSize(QSize(size, 40))
        self.resize(size+40, 60)
        
        self.show()
    
    def close(self):
        self.hide()
