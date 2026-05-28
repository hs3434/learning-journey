"""
Week 2 Day 3: QThread Worker Pattern
=====================================
QThread 信号处理、进度条

后台处理数据，避免阻塞 UI 线程
"""
import sys
import time
import numpy as np

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout,
        QPushButton, QLabel, QProgressBar, QTextEdit
    )
    from PyQt6.QtCore import QThread, pyqtSignal, QTimer
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("PyQt6 not available. Skipping Qt code demo.")
    sys.exit(0)


class DataProcessorWorker(QThread):
    """后台数据处理 Worker"""

    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    result = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, data, params):
        super().__init__()
        self.data = data
        self.params = params

    def run(self):
        """执行后台处理"""
        try:
            self.log.emit("Starting preprocessing...")
            self.progress.emit(10)

            filtered = self.apply_filter()
            self.progress.emit(40)
            self.log.emit("Filter applied")

            epochs = self.create_epochs()
            self.progress.emit(70)
            self.log.emit(f"Created {len(epochs)} epochs")

            features = self.extract_features(epochs)
            self.progress.emit(90)
            self.log.emit("Features extracted")

            result = {
                'accuracy': 0.85,
                'n_epochs': len(epochs),
                'n_features': len(features)
            }
            self.result.emit(result)
            self.progress.emit(100)

        except Exception as e:
            self.error.emit(str(e))

    def apply_filter(self):
        """模拟滤波处理"""
        time.sleep(0.5)
        from scipy.signal import butter, filtfilt
        fs = self.params.get('fs', 256)
        low = self.params.get('lowcut', 0.5) / (fs / 2)
        high = self.params.get('highcut', 40) / (fs / 2)
        b, a = butter(4, [low, high], btype='band')
        return filtfilt(b, a, self.data, axis=-1)

    def create_epochs(self):
        """模拟 epoch 创建"""
        time.sleep(0.3)
        n_epochs = 100
        return [np.random.randn(100) for _ in range(n_epochs)]

    def extract_features(self, epochs):
        """模拟特征提取"""
        time.sleep(0.2)
        return np.random.randn(len(epochs), 20)


class MainWindow(QMainWindow):
    """主窗口：包含 Worker 和进度显示"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("QThread Worker Demo")
        self.worker = None
        self.setup_ui()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.start_btn = QPushButton("Start Processing")
        self.start_btn.clicked.connect(self.start_processing)
        layout.addWidget(self.start_btn)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)

        self.result_label = QLabel("Result: -")
        layout.addWidget(self.result_label)

    def start_processing(self):
        """启动后台处理"""
        if self.worker is not None and self.worker.isRunning():
            return

        self.log_area.clear()
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(False)

        data = np.random.randn(16, 25600)
        params = {'fs': 256, 'lowcut': 0.5, 'highcut': 40}

        self.worker = DataProcessorWorker(data, params)
        self.worker.progress.connect(self.on_progress)
        self.worker.log.connect(self.on_log)
        self.worker.result.connect(self.on_result)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_progress(self, value):
        self.progress_bar.setValue(value)

    def on_log(self, message):
        self.log_area.append(message)

    def on_result(self, result):
        self.result_label.setText(f"Result: {result}")

    def on_error(self, message):
        self.log_area.append(f"<span style='color:red'>Error: {message}</span>")

    def on_finished(self):
        self.start_btn.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())