"""
EEG Viewer - Qt GUI Application
EEG 数据查看器主程序
"""

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog
from PyQt6.QtCore import QThread, pyqtSignal
import sys
import numpy as np


class LoadWorker(QThread):
    """后台加载 EEG 数据的 Worker"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath

    def run(self):
        try:
            self.progress.emit(10)
            # TODO: 使用 MNE 加载数据
            # import mne
            # self.raw = mne.io.read_raw_xxx(self.filepath, preload=True)
            self.progress.emit(100)
            self.finished.emit(None)  # TODO: 返回 raw 对象
        except Exception as e:
            self.error.emit(str(e))


class EEGViewerWindow(QMainWindow):
    """EEG 查看器主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EEG Viewer")
        self.setMinimumSize(1200, 800)
        self.raw = None
        self.setup_ui()

    def setup_ui(self):
        """初始化 UI"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 标签
        self.status_label = QLabel("No data loaded")
        layout.addWidget(self.status_label)

        # 按钮
        self.load_btn = QPushButton("Load EEG File")
        self.load_btn.clicked.connect(self.on_load_clicked)
        layout.addWidget(self.load_btn)

        # TODO: 添加 Matplotlib 画布用于显示 EEG

    def on_load_clicked(self):
        """处理加载按钮点击"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select EEG File",
            "",
            "EEG Files (*.edf *.fif *.set);;All Files (*)"
        )

        if filepath:
            self.status_label.setText(f"Loading: {filepath}")
            self.load_worker = LoadWorker(filepath)
            self.load_worker.finished.connect(self.on_data_loaded)
            self.load_worker.error.connect(self.on_load_error)
            self.load_worker.start()

    def on_data_loaded(self, raw):
        """数据加载完成"""
        self.raw = raw
        self.status_label.setText(f"Loaded: {len(self.raw.ch_names)} channels")

    def on_load_error(self, error_msg):
        """加载出错"""
        self.status_label.setText(f"Error: {error_msg}")


def main():
    app = QApplication(sys.argv)
    window = EEGViewerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()