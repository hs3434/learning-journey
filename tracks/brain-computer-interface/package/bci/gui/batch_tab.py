"""
Batch Tab — Offline Analysis
============================
Load file → configure per-step params → Run pipeline → view results.

Step strip navigates between param pages.
"""
from __future__ import annotations
from typing import Optional, List
from pathlib import Path
import numpy as np

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QDoubleSpinBox, QComboBox, QSpinBox, QTextEdit,
    QProgressBar, QMessageBox, QStackedWidget, QFrame,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from bci.config import create_default_config
from bci.gui.widgets import (EEGWaveformWidget, ResultPanel, EEGInfoPanel,
                              StepStrip, StepStatus)
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
        self._pipeline: object = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # ---- toolbar ----
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

        # ---- info panel ----
        self.info_panel = EEGInfoPanel()
        layout.addWidget(self.info_panel)

        # ---- step strip ----
        self.step_strip = StepStrip()
        self.step_strip.step_clicked.connect(self._on_step_clicked)
        self.step_strip.rerun_clicked.connect(self._on_run)
        layout.addWidget(self.step_strip)

        # ---- stacked step pages ----
        self._pages = QStackedWidget()
        self._pages.addWidget(self._make_preprocess_page())
        self._pages.addWidget(self._make_epoch_page())
        self._pages.addWidget(self._make_decode_page())
        layout.addWidget(self._pages)

        # ---- main content (results area) ----
        content = QHBoxLayout()
        self.waveform_widget = EEGWaveformWidget()
        content.addWidget(self.waveform_widget, stretch=3)

        self.result_panel = ResultPanel()
        content.addWidget(self.result_panel, stretch=1)
        layout.addLayout(content, stretch=1)

        # ---- bottom ----
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

    # ---- step pages ----

    def _make_preprocess_page(self) -> QFrame:
        page = QFrame()
        lay = QHBoxLayout(page)
        lay.setContentsMargins(0, 4, 0, 4)

        grp = QGroupBox("Filter Parameters")
        glay = QHBoxLayout()
        glay.addWidget(QLabel("Lowcut:"))
        self.l_freq = QDoubleSpinBox()
        self.l_freq.setRange(0.1, 10)
        self.l_freq.setValue(0.5)
        self.l_freq.setSuffix(" Hz")
        glay.addWidget(self.l_freq)
        glay.addWidget(QLabel("Highcut:"))
        self.h_freq = QDoubleSpinBox()
        self.h_freq.setRange(10, 100)
        self.h_freq.setValue(40)
        self.h_freq.setSuffix(" Hz")
        glay.addWidget(self.h_freq)
        glay.addStretch()
        grp.setLayout(glay)
        lay.addWidget(grp)

        chart = self._make_mini_chart()
        self._preprocess_chart = chart
        lay.addWidget(chart, stretch=1)
        return page

    def _make_epoch_page(self) -> QFrame:
        page = QFrame()
        lay = QHBoxLayout(page)
        lay.setContentsMargins(0, 4, 0, 4)

        grp = QGroupBox("Epoch Parameters")
        glay = QHBoxLayout()
        glay.addWidget(QLabel("tmin:"))
        self.epoch_tmin = QDoubleSpinBox()
        self.epoch_tmin.setRange(-1.0, 0)
        self.epoch_tmin.setValue(-0.2)
        self.epoch_tmin.setSuffix(" s")
        glay.addWidget(self.epoch_tmin)
        glay.addWidget(QLabel("tmax:"))
        self.epoch_tmax = QDoubleSpinBox()
        self.epoch_tmax.setRange(0.1, 2.0)
        self.epoch_tmax.setValue(0.5)
        self.epoch_tmax.setSuffix(" s")
        glay.addWidget(self.epoch_tmax)
        glay.addWidget(QLabel("Reject:"))
        self.reject_spin = QDoubleSpinBox()
        self.reject_spin.setRange(50, 2000)
        self.reject_spin.setValue(300)
        self.reject_spin.setSuffix(" μV")
        glay.addWidget(self.reject_spin)
        glay.addStretch()
        grp.setLayout(glay)
        lay.addWidget(grp)

        chart = self._make_mini_chart()
        self._epoch_chart = chart
        lay.addWidget(chart, stretch=1)
        return page

    def _make_decode_page(self) -> QFrame:
        page = QFrame()
        lay = QHBoxLayout(page)
        lay.setContentsMargins(0, 4, 0, 4)

        grp = QGroupBox("Decode Parameters")
        glay = QHBoxLayout()
        glay.addWidget(QLabel("Method:"))
        self.method_cb = QComboBox()
        self.method_cb.addItems(['lda', 'ssvep', 'fbcca', 'cnn'])
        glay.addWidget(self.method_cb)
        glay.addWidget(QLabel("CV Folds:"))
        self.cv_folds = QSpinBox()
        self.cv_folds.setRange(2, 10)
        self.cv_folds.setValue(5)
        glay.addWidget(self.cv_folds)
        glay.addStretch()
        grp.setLayout(glay)
        lay.addWidget(grp)

        chart = self._make_mini_chart()
        self._decode_chart = chart
        lay.addWidget(chart, stretch=1)
        return page

    @staticmethod
    def _make_mini_chart() -> FigureCanvasQTAgg:
        fig = Figure(figsize=(4, 1.2), facecolor='#1e1e1e')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1e1e1e')
        ax.tick_params(colors='white', labelsize=6)
        for spine in ax.spines.values():
            spine.set_color('#444')
        canvas = FigureCanvasQTAgg(fig)
        canvas.setMaximumHeight(120)
        return canvas

    # ---- step switching ----

    def _on_step_clicked(self, idx: int):
        self._pages.setCurrentIndex(idx)
        self._refresh_step_view(idx)

    def _refresh_step_view(self, idx: int):
        if idx == 0:
            self._draw_preprocess_chart()
        elif idx == 1:
            self._draw_epoch_chart()
        elif idx == 2:
            self._draw_decode_chart()

    def _draw_preprocess_chart(self):
        ax = self._preprocess_chart.figure.axes[0]
        ax.clear()
        ax.set_facecolor('#1e1e1e')
        try:
            source = self._source
            if source is None or not source._data_list:
                ax.text(0.5, 0.5, "No data loaded", transform=ax.transAxes,
                        ha='center', va='center', color='#555')
            else:
                d = source._data_list[0]
                n_ch = min(8, d.shape[0])
                t = np.arange(min(500, d.shape[1])) / source.sfreq
                for i in range(n_ch):
                    ax.plot(t, d[i, :len(t)] * 1e6 + i * 50,
                            linewidth=0.3, color='#00ff88')
                ax.set_title(f"Raw — first {n_ch} ch", color='white', fontsize=8)
        except Exception:
            pass
        self._preprocess_chart.draw_idle()

    def _draw_epoch_chart(self):
        ax = self._epoch_chart.figure.axes[0]
        ax.clear()
        ax.set_facecolor('#1e1e1e')
        try:
            epochs = self._pipeline.epochs if self._pipeline else None
            if epochs is None:
                ax.text(0.5, 0.5, "Run pipeline to see epochs",
                        transform=ax.transAxes, ha='center', va='center',
                        color='#555')
            else:
                evoked = epochs.average()
                t = evoked.times
                d = evoked.data * 1e6
                n_ch = min(8, d.shape[0])
                for i in range(n_ch):
                    ax.plot(t, d[i] + i * 20, linewidth=0.3, color='#00ff88')
                ax.set_title(f"ERP average — {len(epochs)} epochs",
                             color='white', fontsize=8)
        except Exception:
            pass
        self._epoch_chart.draw_idle()

    def _draw_decode_chart(self):
        pass  # result_panel handles decode viz

    def _show_raw_preview(self):
        try:
            source = self._source
            n_ch = min(8, source.n_channels)
            ch_names = [f'Ch {i}' for i in range(n_ch)]
            if source._data_list:
                d = source._data_list[0]
                n_ch = min(8, d.shape[0])
                self.waveform_widget.plot_batch(d[:n_ch], source.sfreq,
                                                 ch_names[:n_ch])
        except Exception:
            pass

    def _show_epoch_preview(self):
        try:
            epochs = self._pipeline.epochs if self._pipeline else None
            if epochs is None:
                return
            evoked = epochs.average()
            data = evoked.data[np.newaxis, :]
            ch_names = evoked.ch_names[:8]
            self.waveform_widget.plot_batch(data, evoked.info['sfreq'], ch_names)
        except Exception:
            pass

    # ---- load flow ----

    def _on_load(self):
        self._stop_workers()
        from bci.gui.session_loader import open_session_files
        filepaths = open_session_files(self)
        if filepaths:
            self._on_files_loaded([str(p) for p in filepaths])

    def _stop_workers(self):
        for w in (self._worker, self._load_worker):
            if w is not None and w.isRunning():
                w.quit()
                w.wait()
        self._worker = None
        self._load_worker = None
        self.info_panel.clear()

    def shutdown(self):
        self._stop_workers()

    def _on_files_loaded(self, filepaths: List[str]):
        import re
        self._filepaths = filepaths
        n = len(filepaths)
        if n > 1:
            stem = Path(filepaths[0]).stem
            match = re.match(r'^(.*)R\d+$', stem)
            base = match.group(1) if match else stem
            self.status_label.setText(f"Session: {base} ({n} runs)")
        else:
            self.status_label.setText(f"Loaded: {Path(filepaths[0]).name}")
        self._start_loading()

    def _start_loading(self):
        self.run_btn.setEnabled(False)
        self.load_progress_bar.setValue(0)
        self.load_progress_bar.setVisible(True)
        self.load_label.setText("Loading...")
        self.load_label.setVisible(True)
        self.step_strip.set_all_pending()

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
        self.info_panel.show_batch(source)
        self.status_label.setText(
            f"Ready — {source.n_channels} ch, "
            f"{source.total_samples / source.sfreq:.1f}s"
        )
        self._pages.setCurrentIndex(0)
        self.step_strip.set_active(0)
        self._draw_preprocess_chart()
        self.run_btn.setEnabled(True)

    def _on_load_error(self, msg: str):
        self._load_worker = None
        self.load_progress_bar.setVisible(False)
        self.load_label.setVisible(False)
        self.status_label.setText(f"Load error: {msg[:50]}")
        QMessageBox.warning(self, "Load Error", msg)

    def _on_load_progress(self, current: int, total: int):
        self.load_label.setText(f"Loading run {current}/{total}...")
        self.load_progress_bar.setMaximum(total)
        self.load_progress_bar.setValue(current)

    # ---- run flow ----

    def _on_run(self):
        if not self._filepaths:
            return
        self._config.filter.l_freq = self.l_freq.value()
        self._config.filter.h_freq = self.h_freq.value()
        self._config.epoch.tmin = self.epoch_tmin.value()
        self._config.epoch.tmax = self.epoch_tmax.value()
        self._config.epoch.reject_threshold = {'eeg': self.reject_spin.value() * 1e-6}
        self._config.decode.method = self.method_cb.currentText()
        self._config.decode.cv_folds = self.cv_folds.value()

        self._pipeline = None
        self.run_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.log_area.clear()
        self.progress.setValue(0)
        self.status_label.setText("Running pipeline...")
        self.step_strip.set_all_pending()
        self.step_strip.set_status(0, StepStatus.RUNNING)
        self._pages.setCurrentIndex(0)

        self._worker = BatchWorker(self._filepaths, self._config)
        self._worker.log.connect(self.log_area.append)
        self._worker.progress.connect(self._on_pipeline_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_pipeline_progress(self, val: int):
        self.progress.setValue(val)
        if val >= 50:
            self.step_strip.set_status(0, StepStatus.DONE)
            self.step_strip.set_status(1, StepStatus.RUNNING)
            self._pages.setCurrentIndex(1)
        if val >= 70:
            self.step_strip.set_status(1, StepStatus.DONE)
            self.step_strip.set_status(2, StepStatus.RUNNING)
            self._pages.setCurrentIndex(2)
            self._draw_epoch_chart()

    def _on_finished(self, result, pipeline):
        self._pipeline = pipeline
        self.step_strip.set_status(0, StepStatus.DONE)
        self.step_strip.set_status(1, StepStatus.DONE)
        self.step_strip.set_status(2, StepStatus.DONE)
        self._pages.setCurrentIndex(2)

        if result and result.accuracy is not None:
            self.status_label.setText(
                f"Done! Accuracy: {result.accuracy:.3f} "
                f"+/- {result.std:.3f}"
            )
            self.save_btn.setEnabled(True)
            self.result_panel.update_batch(
                accuracy=result.accuracy, std=result.std,
                cv_scores=result.cv_scores,
                method=self.method_cb.currentText()
            )
            # show ERP preview in waveform
            self._draw_epoch_chart()
            self._show_epoch_preview()
        self.run_btn.setEnabled(True)

    def _on_error(self, msg: str):
        cur = self.step_strip._active_idx
        self.step_strip.mark_error(max(0, cur))
        self.log_area.append(f"ERROR: {msg}")
        self.status_label.setText(f"Error: {msg[:50]}")
        self.run_btn.setEnabled(True)
        QMessageBox.warning(self, "Pipeline Error", msg)

    # ---- preview helpers ----

    def _show_epoch_preview(self):
        try:
            epochs = self._pipeline.epochs
            if epochs is None:
                return
            evoked = epochs.average()
            data = evoked.data[np.newaxis, :]
            ch_names = evoked.ch_names[:8]
            self.waveform_widget.plot_batch(data, evoked.info['sfreq'], ch_names)
        except Exception:
            pass

    # ---- save ----

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
