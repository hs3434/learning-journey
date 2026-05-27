"""
GUI Module
==========
Qt-based BCI Data Analysis GUI
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Optional, TYPE_CHECKING

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QFileDialog, QProgressBar, QGroupBox,
        QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit
    )
    from PyQt6.QtCore import QThread, pyqtSignal, Qt
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("Warning: PyQt6 not available. GUI features disabled.")


if GUI_AVAILABLE:
    class Worker(QThread):
        """Background worker for pipeline execution"""
        progress = pyqtSignal(int)
        log = pyqtSignal(str)
        finished = pyqtSignal(object)
        error = pyqtSignal(str)

        def __init__(self, pipeline, filepath):
            super().__init__()
            self.pipeline = pipeline
            self.filepath = filepath

        def run(self):
            try:
                self.progress.emit(10)
                self.log.emit("Loading data...")
                self.pipeline.load(self.filepath)
                self.progress.emit(30)

                self.log.emit("Preprocessing...")
                self.pipeline.preprocess()
                self.progress.emit(50)

                self.log.emit("Creating epochs...")
                self.pipeline.create_epochs()
                self.progress.emit(70)

                self.log.emit("Decoding...")
                self.pipeline.decode()
                self.progress.emit(90)

                self.progress.emit(100)
                self.finished.emit(self.pipeline.result)

            except Exception as e:
                self.error.emit(str(e))


    class BCIMainWindow(QMainWindow):
        """BCI Pipeline Main Window"""

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

            toolbar = QHBoxLayout()
            self.load_btn = QPushButton("Load EEG File")
            self.load_btn.clicked.connect(self.on_load)
            toolbar.addWidget(self.load_btn)

            self.run_btn = QPushButton("Run Pipeline")
            self.run_btn.clicked.connect(self.on_run)
            self.run_btn.setEnabled(False)
            toolbar.addWidget(self.run_btn)

            self.save_btn = QPushButton("Save Results")
            self.save_btn.clicked.connect(self.on_save)
            self.save_btn.setEnabled(False)
            toolbar.addWidget(self.save_btn)
            toolbar.addStretch()

            self.status_label = QLabel("Ready")
            toolbar.addWidget(self.status_label)
            layout.addLayout(toolbar)

            params = QGroupBox("Parameters")
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

            params_layout.addStretch()
            params.setLayout(params_layout)
            layout.addWidget(params)

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

        def on_run(self):
            from config import PipelineConfig
            from pipeline import BCIPipeline

            config = PipelineConfig()
            config.filter.l_freq = self.l_freq.value()
            config.filter.h_freq = self.h_freq.value()

            self.pipeline = BCIPipeline(config)
            self.worker = Worker(self.pipeline, "data.edf")
            self.worker.log.connect(self.log_area.append)
            self.worker.progress.connect(self.progress.setValue)
            self.worker.finished.connect(self.on_finished)
            self.worker.start()

        def on_finished(self, result):
            if result and result.accuracy is not None:
                self.status_label.setText(f"Done! Accuracy: {result.accuracy:.3f}")
                self.save_btn.setEnabled(True)

        def on_save(self):
            if self.pipeline:
                self.pipeline.save_results()


def main():
    """GUI entry point"""
    if not GUI_AVAILABLE:
        print("Error: PyQt6 is required for GUI")
        print("Install with: pip install PyQt6")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = BCIMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()