"""
Batch Tab — Offline Analysis
============================
Load file → configure params → Run pipeline → view results.
"""
from __future__ import annotations
from typing import Optional, List
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QDoubleSpinBox, QComboBox, QSpinBox, QTextEdit,
    QProgressBar, QFileDialog, QMessageBox,
)
from PyQt6.QtCore import Qt

from bci.config import PipelineConfig, create_default_config
from bci.gui.widgets import EEGWaveformWidget, ResultPanel
from bci.gui.worker import BatchWorker


class BatchTab(QWidget):
    """Offline (batch) analysis tab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filepath: Optional[str] = None
        self._session_runs: List[str] = []
        self._config = create_default_config()
        self._worker: Optional[BatchWorker] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        toolbar = QHBoxLayout()
        self.load_btn = QPushButton("Load EEG File")
        self.load_btn.clicked.connect(self._on_load)
        toolbar.addWidget(self.load_btn)

        self.run_btn = QPushButton("Run Pipeline")
        self.run_btn.clicked.connect(self._on_run)
        self.run_btn.setEnabled(False)
        toolbar.addWidget(self.run_btn)

        self.save_btn = QPushButton("Export Results")
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setEnabled(False)
        toolbar.addWidget(self.save_btn)

        toolbar.addStretch()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888;")
        toolbar.addWidget(self.status_label)
        layout.addLayout(toolbar)

        params = QGroupBox("Parameters")
        params_layout = QHBoxLayout()

        params_layout.addWidget(QLabel("Lowcut:"))
        self.l_freq = QDoubleSpinBox()
        self.l_freq.setRange(0.1, 10)
        self.l_freq.setValue(0.5)
        self.l_freq.setSuffix(" Hz")
        params_layout.addWidget(self.l_freq)

        params_layout.addWidget(QLabel("Highcut:"))
        self.h_freq = QDoubleSpinBox()
        self.h_freq.setRange(10, 100)
        self.h_freq.setValue(40)
        self.h_freq.setSuffix(" Hz")
        params_layout.addWidget(self.h_freq)

        params_layout.addWidget(QLabel("Method:"))
        self.method_cb = QComboBox()
        self.method_cb.addItems(['lda', 'mi', 'ssvep'])
        params_layout.addWidget(self.method_cb)

        params_layout.addWidget(QLabel("CV Folds:"))
        self.cv_folds = QSpinBox()
        self.cv_folds.setRange(2, 10)
        self.cv_folds.setValue(5)
        params_layout.addWidget(self.cv_folds)

        params_layout.addStretch()
        params.setLayout(params_layout)
        layout.addWidget(params)

        content = QHBoxLayout()
        self.waveform_widget = EEGWaveformWidget()
        content.addWidget(self.waveform_widget, stretch=3)

        self.result_panel = ResultPanel()
        content.addWidget(self.result_panel, stretch=1)
        layout.addLayout(content, stretch=1)

        bottom = QHBoxLayout()
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(100)
        self.log_area.setStyleSheet(
            "background-color: #2d2d2d; color: #aaa; font-family: monospace;"
        )
        bottom.addWidget(self.log_area, stretch=3)

        self.progress = QProgressBar()
        bottom.addWidget(self.progress, stretch=1)
        layout.addLayout(bottom)

    def _on_load(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select EEG File", "",
            "EEG Files (*.edf *.fif *.set *.vhdr);;All Files (*)"
        )
        if filepath:
            self._on_file_loaded(filepath)

    def _on_file_loaded(self, filepath: str):
        from bci.source import find_session_runs
        self._filepath = filepath
        runs = find_session_runs(filepath)
        self._session_runs = [str(r) for r in runs]

        if len(self._session_runs) > 1:
            self.status_label.setText(
                f"Session: {Path(filepath).stem} ({len(self._session_runs)} runs)"
            )
        else:
            self.status_label.setText(f"Loaded: {Path(filepath).name}")
        self.run_btn.setEnabled(True)

    def _on_run(self):
        if self._filepath is None:
            return
        self._config.filter.l_freq = self.l_freq.value()
        self._config.filter.h_freq = self.h_freq.value()
        self._config.decode.method = self.method_cb.currentText()
        self._config.decode.cv_folds = self.cv_folds.value()

        self.run_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.log_area.clear()
        self.progress.setValue(0)
        self.status_label.setText("Running pipeline...")

        self._worker = BatchWorker(self._filepath, self._config)
        self._worker.log.connect(self.log_area.append)
        self._worker.progress.connect(self.progress.setValue)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_finished(self, result):
        if result and result.accuracy is not None:
            self.status_label.setText(
                f"Done! Accuracy: {result.accuracy:.3f} "
                f"+/- {result.std:.3f}"
            )
            self.save_btn.setEnabled(True)
            self.result_panel.update_batch(
                accuracy=result.accuracy, confusion=None,
                method=self.method_cb.currentText()
            )
        self.run_btn.setEnabled(True)

    def _on_error(self, msg: str):
        self.log_area.append(f"ERROR: {msg}")
        self.status_label.setText(f"Error: {msg[:50]}")
        self.run_btn.setEnabled(True)
        QMessageBox.warning(self, "Pipeline Error", msg)

    def _on_save(self):
        if self._worker is None:
            return
        from bci.pipeline import BCIPipeline
        pipeline = BCIPipeline(self._config)
        pipeline.run(Path(self._filepath))
        saved = pipeline.save_results()
        self.log_area.append(f"Saved to: {saved}")
        QMessageBox.information(
            self, "Export", f"Results saved to {self._config.output_dir}"
        )
