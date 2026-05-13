"""
BCI Data Analysis GUI
完整的 BCI 数据分析图形界面工具

整合：数据加载、信号处理、BCI 解码、可视化
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QFileDialog, QMessageBox, QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
import sys
import numpy as np


class BCIMainWindow(QMainWindow):
    """BCI 数据分析主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BCI Data Analysis Tool")
        self.setMinimumSize(1400, 900)

        # 数据和 pipeline
        self.raw = None
        self.epochs = None
        self.config = {}

        self.setup_ui()
        self.setup_menu()

    def setup_ui(self):
        """初始化 UI"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # ===== 工具栏 =====
        toolbar_layout = QHBoxLayout()

        self.load_btn = QPushButton("Load EEG")
        self.load_btn.clicked.connect(self.load_eeg)
        toolbar_layout.addWidget(self.load_btn)

        self.preprocess_btn = QPushButton("Preprocess")
        self.preprocess_btn.clicked.connect(self.run_preprocessing)
        self.preprocess_btn.setEnabled(False)
        toolbar_layout.addWidget(self.preprocess_btn)

        self.decode_btn = QPushButton("Decode")
        self.decode_btn.clicked.connect(self.run_decode)
        self.decode_btn.setEnabled(False)
        toolbar_layout.addWidget(self.decode_btn)

        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        toolbar_layout.addWidget(self.export_btn)

        toolbar_layout.addStretch()
        self.status_label = QLabel("Ready")
        toolbar_layout.addWidget(self.status_label)

        main_layout.addLayout(toolbar_layout)

        # ===== 参数设置 =====
        params_group = QGroupBox("Parameters")
        params_layout = QHBoxLayout()

        # 滤波参数
        self.lowcut_spin = QDoubleSpinBox()
        self.lowcut_spin.setRange(0.1, 100)
        self.lowcut_spin.setValue(0.5)
        self.lowcut_spin.setSuffix(" Hz")
        params_layout.addWidget(QLabel("Lowcut:"))
        params_layout.addWidget(self.lowcut_spin)

        self.highcut_spin = QDoubleSpinBox()
        self.highcut_spin.setRange(1, 200)
        self.highcut_spin.setValue(40)
        self.highcut_spin.setSuffix(" Hz")
        params_layout.addWidget(QLabel("Highcut:"))
        params_layout.addWidget(self.highcut_spin)

        # Notch
        self.notch_check = QComboBox()
        self.notch_check.addItems(["50Hz", "60Hz", "None"])
        params_layout.addWidget(QLabel("Notch:"))
        params_layout.addWidget(self.notch_check)

        # 通道数
        self.n_channels_spin = QSpinBox()
        self.n_channels_spin.setRange(1, 128)
        self.n_channels_spin.setValue(64)
        params_layout.addWidget(QLabel("Channels:"))
        params_layout.addWidget(self.n_channels_spin)

        params_layout.addStretch()
        params_group.setLayout(params_layout)
        main_layout.addWidget(params_group)

        # ===== 主显示区 =====
        display_layout = QHBoxLayout()

        # 左侧：原始数据
        left_group = QGroupBox("Raw Data")
        left_layout = QVBoxLayout()
        self.raw_label = QLabel("No data")
        left_layout.addWidget(self.raw_label)
        left_group.setLayout(left_layout)
        display_layout.addWidget(left_group, 1)

        # 中间：处理后数据
        mid_group = QGroupBox("Processed")
        mid_layout = QVBoxLayout()
        self.processed_label = QLabel("No data")
        mid_layout.addWidget(self.processed_label)
        mid_group.setLayout(mid_layout)
        display_layout.addWidget(mid_group, 1)

        # 右侧：解码结果
        right_group = QGroupBox("Decoded")
        right_layout = QVBoxLayout()
        self.decode_label = QLabel("No result")
        right_layout.addWidget(self.decode_label)
        right_group.setLayout(right_layout)
        display_layout.addWidget(right_group, 1)

        main_layout.addLayout(display_layout, 1)

        # ===== 进度条 =====
        self.progress = QProgressBar()
        main_layout.addWidget(self.progress)

    def setup_menu(self):
        """初始化菜单"""
        menubar = self.menuBar()

        # File
        file_menu = menubar.addMenu("File")
        open_action = QAction("Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.load_eeg)
        file_menu.addAction(open_action)

        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View
        view_menu = menubar.addMenu("View")
        zoom_in = QAction("Zoom In", self)
        zoom_in.triggered.connect(lambda: print("Zoom in"))
        view_menu.addAction(zoom_in)

    def load_eeg(self):
        """加载 EEG 文件"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select EEG File",
            "", "EEG Files (*.edf *.fif *.set);;All Files (*)"
        )

        if filepath:
            self.status_label.setText(f"Loading: {filepath}")
            self.progress.setRange(0, 100)
            self.progress.setValue(50)

            # TODO: 使用 MNE 加载
            # self.raw = mne.io.read_raw_xxx(filepath, preload=True)

            self.progress.setValue(100)
            self.raw_label.setText(f"Loaded: {filepath}")
            self.status_label.setText("Ready")
            self.preprocess_btn.setEnabled(True)

    def run_preprocessing(self):
        """运行预处理"""
        if self.raw is None:
            return

        self.status_label.setText("Preprocessing...")
        # TODO: 滤波、重参考、ICA 等

        self.processed_label.setText("Preprocessed")
        self.decode_btn.setEnabled(True)
        self.status_label.setText("Ready")

    def run_decode(self):
        """运行解码"""
        self.status_label.setText("Decoding...")
        # TODO: SSVEP/MI 解码

        self.decode_label.setText("Decoded: target 0")
        self.export_btn.setEnabled(True)
        self.status_label.setText("Ready")

    def export_results(self):
        """导出结果"""
        self.status_label.setText("Exporting...")
        # TODO: 导出 CSV/JSON

        self.status_label.setText("Ready")


def main():
    app = QApplication(sys.argv)
    window = BCIMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()