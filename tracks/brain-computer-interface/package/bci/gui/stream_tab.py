"""
Stream Tab — Real-Time Viewing
==============================
Simulated live feed from file with playback controls.
"""
from __future__ import annotations
from typing import Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QDoubleSpinBox, QSlider, QCheckBox, QTextEdit,
    QProgressBar, QFileDialog, QMessageBox,
)
from PyQt6.QtCore import Qt

from bci.gui.widgets import (
    EEGWaveformWidget, SpectrumWidget, TopomapWidget, ResultPanel
)
from bci.gui.worker import StreamWorker


class StreamTab(QWidget):
    """Real-time streaming analysis tab.

    Speed control: slider (25-10000 → 0.25x-100x) + input box (0.25-100).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filepath: Optional[str] = None
        self._worker: Optional[StreamWorker] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        toolbar = QHBoxLayout()
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.clicked.connect(self._on_start)
        self.start_btn.setEnabled(False)
        toolbar.addWidget(self.start_btn)

        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self._on_pause)
        self.pause_btn.setEnabled(False)
        toolbar.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self._on_stop)
        self.stop_btn.setEnabled(False)
        toolbar.addWidget(self.stop_btn)

        toolbar.addSpacing(20)
        toolbar.addWidget(QLabel("Speed:"))

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(25, 10000)  # 0.25x to 100x (×100)
        self.speed_slider.setValue(100)  # 1x
        self.speed_slider.setMaximumWidth(150)
        self.speed_slider.valueChanged.connect(self._on_speed_slider_changed)
        toolbar.addWidget(self.speed_slider)

        self.speed_input = QDoubleSpinBox()
        self.speed_input.setRange(0.25, 100.0)
        self.speed_input.setValue(1.0)
        self.speed_input.setDecimals(2)
        self.speed_input.setSuffix("x")
        self.speed_input.valueChanged.connect(self._on_speed_input_changed)
        toolbar.addWidget(self.speed_input)

        self.loop_cb = QCheckBox("Loop")
        self.loop_cb.setChecked(False)
        toolbar.addWidget(self.loop_cb)

        toolbar.addStretch()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888;")
        toolbar.addWidget(self.status_label)
        layout.addLayout(toolbar)

        params = QGroupBox("Filter")
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
        params_layout.addStretch()
        params.setLayout(params_layout)
        layout.addWidget(params)

        content = QHBoxLayout()
        left_panel = QVBoxLayout()

        self.waveform_widget = EEGWaveformWidget()
        left_panel.addWidget(self.waveform_widget, stretch=3)

        bottom_row = QHBoxLayout()
        self.spectrum_widget = SpectrumWidget()
        bottom_row.addWidget(self.spectrum_widget)

        self.topomap_widget = TopomapWidget()
        bottom_row.addWidget(self.topomap_widget)
        left_panel.addLayout(bottom_row, stretch=1)

        content.addLayout(left_panel, stretch=3)

        right_panel = QVBoxLayout()
        self.result_panel = ResultPanel()
        right_panel.addWidget(self.result_panel, stretch=1)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet(
            "background-color: #2d2d2d; color: #aaa; font-family: monospace;"
        )
        right_panel.addWidget(self.log_area, stretch=1)
        content.addLayout(right_panel, stretch=1)
        layout.addLayout(content, stretch=1)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)

    def _on_load(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select EEG File", "",
            "EEG Files (*.edf *.fif *.set *.vhdr);;All Files (*)"
        )
        if filepath:
            self._on_file_loaded(filepath)

    def _on_file_loaded(self, filepath: str):
        self._filepath = filepath
        self.status_label.setText(f"Loaded: {Path(filepath).name}")
        self.start_btn.setEnabled(True)

    def _on_start(self):
        if self._filepath is None:
            return
        if self._worker is not None:
            return

        self.status_label.setText("Streaming...")
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)

        self._worker = StreamWorker(self._filepath, chunk_duration=0.1)
        self._worker.set_speed(self.speed_input.value())
        self._worker.set_filter(self.l_freq.value(), self.h_freq.value())
        self._worker.set_loop(self.loop_cb.isChecked())
        self._worker.source.open()

        n_ch = self._worker.source.n_channels
        sfreq = self._worker.source.sfreq
        ch_names = [f'Ch {i}' for i in range(n_ch)]
        self.waveform_widget._init_buffer(n_ch, sfreq, ch_names)

        self._worker.chunk_processed.connect(self._on_chunk)
        self._worker.finished.connect(self._on_stream_finished)
        self._worker.error.connect(self._on_error)
        self._worker.progress.connect(self.progress.setValue)
        self._worker.start()

    def _on_pause(self):
        if self._worker is not None:
            self._worker.stop()
            self.pause_btn.setEnabled(False)
            self.start_btn.setEnabled(True)
            self.start_btn.setText("▶ Resume")
            self.status_label.setText("Paused")

    def _on_stop(self):
        if self._worker is not None:
            self._worker.stop()
            self._worker = None
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.start_btn.setEnabled(True)
            self.start_btn.setText("▶ Start")
            self.status_label.setText("Stopped")
            self.progress.setValue(0)
            self.waveform_widget.clear()

    def _on_chunk(self, chunk):
        self.waveform_widget.update_stream(chunk)

    def _on_stream_finished(self):
        self.status_label.setText("Playback complete")
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        self.start_btn.setText("▶ Start")
        self._worker = None

    def _on_error(self, msg: str):
        self.log_area.append(f"ERROR: {msg}")
        self.status_label.setText(f"Error: {msg[:50]}")
        QMessageBox.warning(self, "Stream Error", msg)

    def _on_speed_slider_changed(self, value: int):
        speed = value / 100.0
        self.speed_input.blockSignals(True)
        self.speed_input.setValue(speed)
        self.speed_input.blockSignals(False)
        if self._worker is not None:
            self._worker.set_speed(speed)

    def _on_speed_input_changed(self, value: float):
        self.speed_slider.blockSignals(True)
        self.speed_slider.setValue(int(value * 100))
        self.speed_slider.blockSignals(False)
        if self._worker is not None:
            self._worker.set_speed(value)
