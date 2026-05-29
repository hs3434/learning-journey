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
    QProgressBar, QMessageBox,
)

from bci.config import create_default_config
from bci.gui.widgets import EEGWaveformWidget, ResultPanel
from bci.gui.worker import BatchWorker, LoadWorker
from bci.source import SessionSource


class BatchTab(QWidget):
    """Offline (batch) analysis tab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filepaths: List[str] = []
        self._source: Optional[SessionSource] = None
        self._config = create_default_config()
        self._worker: Optional[BatchWorker] = None
        self._load_worker: Optional[LoadWorker] = None
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

        progress_col = QVBoxLayout()
        self.load_label = QLabel("")
        self.load_label.setStyleSheet("color: #aaa; font-size: 11px;")
        self.load_label.setVisible(False)
        progress_col.addWidget(self.load_label)

        self.load_progress_bar = QProgressBar()
        self.load_progress_bar.setVisible(False)
        self.load_progress_bar.setMaximumHeight(16)
        progress_col.addWidget(self.load_progress_bar)

        self.progress = QProgressBar()
        progress_col.addWidget(self.progress)
        bottom.addLayout(progress_col, stretch=1)
        layout.addLayout(bottom)

    def _on_load(self):
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait()
            self._worker = None
        from bci.gui.session_loader import open_session_files
        filepaths = open_session_files(self)
        if filepaths:
            self._on_files_loaded([str(p) for p in filepaths])

    def _on_files_loaded(self, filepaths: List[str]):
        import re
        self._filepaths = filepaths
        n = len(filepaths)
        if n > 1:
            stem = Path(filepaths[0]).stem
            match = re.match(r'^(.*)R\d+$', stem)
            base = match.group(1) if match else stem
            self.status_label.setText(
                f"Session: {base} ({n} runs)"
            )
        else:
            self.status_label.setText(f"Loaded: {Path(filepaths[0]).name}")

        self._start_loading()

    def _start_loading(self):
        self.run_btn.setEnabled(False)
        self.load_progress_bar.setValue(0)
        self.load_progress_bar.setVisible(True)
        self.load_label.setText("Loading...")
        self.load_label.setVisible(True)

        self._load_worker = LoadWorker(self._filepaths)
        self._load_worker.load_progress.connect(self._on_load_progress)
        self._load_worker.finished.connect(self._on_load_finished)
        self._load_worker.error.connect(self._on_load_error)
        self._load_worker.start()

    def _on_load_finished(self, source):
        self._source = source
        self._load_worker = None
        self.load_progress_bar.setVisible(False)
        self.load_label.setVisible(False)
        self.status_label.setText(
            f"Ready — {source.n_channels} ch, "
            f"{source.total_samples / source.sfreq:.1f}s"
        )
        self.run_btn.setEnabled(True)

    def _on_load_error(self, msg: str):
        self._load_worker = None
        self.load_progress_bar.setVisible(False)
        self.load_label.setVisible(False)
        self.status_label.setText(f"Load error: {msg[:50]}")
        QMessageBox.warning(self, "Load Error", msg)

    def _on_run(self):
        if not self._filepaths:
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

        self._worker = BatchWorker(self._filepaths, self._config)
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

    def _on_load_progress(self, current: int, total: int):
        self.load_label.setText(f"Loading run {current}/{total}...")
        self.load_progress_bar.setMaximum(total)
        self.load_progress_bar.setValue(current)

    def _on_save(self):
        if self._worker is None or not self._filepaths:
            return
        from bci.pipeline import BCIPipeline
        pipeline = BCIPipeline(self._config)
        pipeline.run(Path(self._filepaths[0]))
        saved = pipeline.save_results()
        self.log_area.append(f"Saved to: {saved}")
        QMessageBox.information(
            self, "Export", f"Results saved to {self._config.output_dir}"
        )
