"""
Week 6 Day 1: Qt GUI Architecture for BCI
==========================================
Qt 架构、信号槽机制、widget 布局

实际 Qt 代码，演示 BCI GUI 的核心组件。
Docker 无显示服务器时可作为模块导入。
"""
from __future__ import annotations
import sys
from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QFileDialog, QProgressBar, QGroupBox,
        QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QSlider
    )
    from PyQt6.QtCore import QThread, pyqtSignal, Qt
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("PyQt6 not available. Running in diagram-only mode.")
    print("Install with: pip install PyQt6")


if GUI_AVAILABLE:
    class Worker(QThread):
        """后台 Worker 线程，执行数据处理"""
        progress = pyqtSignal(int)
        log = pyqtSignal(str)
        finished = pyqtSignal(object)
        error = pyqtSignal(str)

        def __init__(self, pipeline, filepath: str):
            super().__init__()
            self.pipeline = pipeline
            self.filepath = filepath

        def run(self):
            try:
                self.progress.emit(10)
                self.log.emit("Loading data...")

                self.progress.emit(30)
                self.log.emit("Preprocessing...")

                self.progress.emit(60)
                self.log.emit("Creating epochs...")

                self.progress.emit(80)
                self.log.emit("Decoding...")

                self.progress.emit(100)
                self.finished.emit({'accuracy': 0.85, 'n_epochs': 100})

            except Exception as e:
                self.error.emit(str(e))


    class BCIMainWindow(QMainWindow):
        """BCI 数据分析主窗口"""

        def __init__(self):
            super().__init__()
            self.setWindowTitle("BCI Pipeline GUI")
            self.setMinimumSize(1200, 800)
            self.pipeline = None
            self.worker = None
            self.setup_ui()

        def setup_ui(self):
            central = QWidget()
            self.setCentralWidget(central)
            layout = QVBoxLayout(central)

            toolbar_layout = QHBoxLayout()
            self.load_btn = QPushButton("Load EEG File")
            self.load_btn.clicked.connect(self.on_load)
            toolbar_layout.addWidget(self.load_btn)

            self.run_btn = QPushButton("Run Pipeline")
            self.run_btn.clicked.connect(self.on_run)
            self.run_btn.setEnabled(False)
            toolbar_layout.addWidget(self.run_btn)

            self.save_btn = QPushButton("Save Results")
            self.save_btn.clicked.connect(self.on_save)
            self.save_btn.setEnabled(False)
            toolbar_layout.addWidget(self.save_btn)
            toolbar_layout.addStretch()

            self.status_label = QLabel("Ready")
            toolbar_layout.addWidget(self.status_label)
            layout.addLayout(toolbar_layout)

            params_group = QGroupBox("Filter Parameters")
            params_layout = QHBoxLayout()

            self.l_freq = QDoubleSpinBox()
            self.l_freq.setRange(0.1, 10)
            self.l_freq.setValue(0.5)
            self.l_freq.setSuffix(" Hz")
            params_layout.addWidget(QLabel("Lowcut:"))
            params_layout.addWidget(self.l_freq)

            self.h_freq = QDoubleSpinBox()
            self.h_freq.setRange(10, 100)
            self.h_freq.setValue(40)
            self.h_freq.setSuffix(" Hz")
            params_layout.addWidget(QLabel("Highcut:"))
            params_layout.addWidget(self.h_freq)

            self.notch_check = QComboBox()
            self.notch_check.addItems(["50 Hz", "60 Hz", "None"])
            params_layout.addWidget(QLabel("Notch:"))
            params_layout.addWidget(self.notch_check)

            params_layout.addStretch()
            params_group.setLayout(params_layout)
            layout.addWidget(params_group)

            self.channels_group = QGroupBox("Channel Selection")
            channels_layout = QHBoxLayout()
            self.channel_slider = QSlider(Qt.Orientation.Horizontal)
            self.channel_slider.setRange(0, 63)
            self.channel_slider.setValue(32)
            channels_layout.addWidget(QLabel("Display Channel:"))
            channels_layout.addWidget(self.channel_slider)
            channels_layout.addStretch()
            self.channels_group.setLayout(channels_layout)
            layout.addWidget(self.channels_group)

            self.log_area = QTextEdit()
            self.log_area.setReadOnly(True)
            layout.addWidget(self.log_area)

            self.progress = QProgressBar()
            layout.addWidget(self.progress)

        def on_load(self):
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Select EEG File",
                "", "EEG Files (*.edf *.fif *.set);;All Files (*)"
            )
            if filepath:
                self.status_label.setText(f"Loaded: {filepath}")
                self.run_btn.setEnabled(True)
                self.filepath = filepath

        def on_run(self):
            self.worker = Worker(None, self.filepath)
            self.worker.log.connect(self.log_area.append)
            self.worker.progress.connect(self.progress.setValue)
            self.worker.finished.connect(self.on_finished)
            self.worker.start()
            self.run_btn.setEnabled(False)

        def on_finished(self, result):
            if result:
                acc = result.get('accuracy', 0)
                self.status_label.setText(f"Done! Accuracy: {acc:.3f}")
                self.save_btn.setEnabled(True)
            self.run_btn.setEnabled(True)

        def on_save(self):
            filepath, _ = QFileDialog.getSaveFileName(
                self, "Save Results",
                "", "CSV Files (*.csv);;JSON Files (*.json)"
            )
            if filepath:
                self.log_area.append(f"Saved to: {filepath}")


def main():
    """GUI 入口"""
    if not GUI_AVAILABLE:
        print("Error: PyQt6 is required for GUI")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = BCIMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()