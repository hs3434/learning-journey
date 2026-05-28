"""
Week 2 Day 1: Qt Signal-Slot Mechanism
======================================
Qt 架构、信号槽机制、widget 布局

由于 Docker 无显示服务器，此练习展示 Qt 代码结构，
在实际有显示器的环境中可以直接运行。
"""
import sys

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout,
        QPushButton, QLabel, QLineEdit
    )
    from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("PyQt6 not available. Skipping Qt code demo.")
    sys.exit(0)


class Counter(QWidget):
    """演示信号槽的计数器 Widget"""

    count_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._count = 0
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.label = QLabel(f"Count: {self._count}")
        layout.addWidget(self.label)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter jump value")
        layout.addWidget(self.input_field)

        btn_inc = QPushButton("Increment")
        btn_inc.clicked.connect(self.increment)
        layout.addWidget(btn_inc)

        btn_dec = QPushButton("Decrement")
        btn_dec.clicked.connect(self.decrement)
        layout.addWidget(btn_dec)

        btn_reset = QPushButton("Reset")
        btn_reset.clicked.connect(self.reset)
        layout.addWidget(btn_reset)

    def increment(self):
        jump = int(self.input_field.text() or "1")
        self._count += jump
        self.count_changed.emit(self._count)
        self.label.setText(f"Count: {self._count}")

    def decrement(self):
        jump = int(self.input_field.text() or "1")
        self._count -= jump
        self.count_changed.emit(self._count)
        self.label.setText(f"Count: {self._count}")

    def reset(self):
        self._count = 0
        self.count_changed.emit(self._count)
        self.label.setText(f"Count: {self._count}")


class DisplayWindow(QWidget):
    """接收 Counter 信号并显示"""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.history = QLabel("Signal history:")
        layout.addWidget(self.history)
        self.setWindowTitle("Signal Receiver")

    @pyqtSlot(int)
    def on_count_changed(self, value):
        self.history.setText(f"Signal received: count = {value}")


class MainWindow(QMainWindow):
    """主窗口：组合 Counter 和 DisplayWindow"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt Signal-Slot Demo")
        self.setMinimumSize(600, 400)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.counter = Counter()
        self.display = DisplayWindow()

        layout.addWidget(self.counter)
        layout.addWidget(self.display)

        self.counter.count_changed.connect(self.display.on_count_changed)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())