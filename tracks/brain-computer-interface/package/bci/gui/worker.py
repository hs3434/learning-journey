"""
Worker Threads
==============
Background workers for batch processing and real-time streaming.
"""
from __future__ import annotations
from typing import Optional
import numpy as np
from pathlib import Path
from scipy.signal import welch

from PyQt6.QtCore import QThread, QObject, pyqtSignal, QTimer

from bci.config import PipelineConfig
from bci.source import StreamSource


class BatchWorker(QThread):
    """Background pipeline execution worker (offline batch mode).

    Fixes the hardcoded "data.edf" bug from the original GUI — filepath
    is now a constructor parameter.
    """
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, filepath: str, config: PipelineConfig):
        super().__init__()
        self.filepath = str(filepath)
        self.config = config

    def run(self):
        try:
            from bci.pipeline import BCIPipeline
            self.progress.emit(10)
            self.log.emit(f"Loading: {self.filepath}")

            pipeline = BCIPipeline(self.config)
            pipeline.load(Path(self.filepath))
            self.progress.emit(30)
            self.log.emit("Preprocessing...")

            pipeline.preprocess()
            self.progress.emit(50)
            self.log.emit("Creating epochs...")

            pipeline.create_epochs()
            self.progress.emit(70)
            self.log.emit("Decoding...")

            pipeline.decode()
            self.progress.emit(100)
            self.log.emit("Pipeline complete")

            self.finished.emit(pipeline.result)
        except Exception as e:
            self.error.emit(str(e))


class StreamWorker(QObject):
    """Real-time streaming worker.

    Connects a StreamSource to an OnlineProcessor and emits
    processed chunks via Qt signals for GUI display.
    """
    chunk_processed = pyqtSignal(np.ndarray)
    spectrum_updated = pyqtSignal(np.ndarray, np.ndarray)
    error = pyqtSignal(str)
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, filepath: str | Path,
                 chunk_duration: float = 0.1):
        super().__init__()
        self.source = StreamSource(filepath, chunk_duration)
        self._timer: Optional[QTimer] = None
        self._filter_enabled = True
        self._l_freq = 0.5
        self._h_freq = 40.0
        self._speed = 1.0
        self._online_proc = None
        self._chunk_samples = 0

    def start(self):
        """Start streaming data from file."""
        self.source.open()
        self._chunk_samples = int(self.source.sfreq * self.source.chunk_duration)
        self._online_proc = __import__('bci.processor.online',
                                       fromlist=['OnlineProcessor']).OnlineProcessor(
            sfreq=self.source.sfreq, n_channels=self.source.n_channels
        )

        interval_ms = int(self.source.chunk_duration * 1000 / max(0.01, self._speed))
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._emit_chunk)
        self._timer.start(max(1, interval_ms))

    def stop(self):
        """Stop streaming."""
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        self.source.close()
        self.finished.emit()

    def _emit_chunk(self):
        """Read chunk from source, process, emit signals."""
        if self.source is None or self._chunk_samples == 0:
            return
        chunk = self.source.read_chunk(self._chunk_samples)
        if chunk is None:
            self.stop()
            return

        if self._filter_enabled and self._online_proc is not None:
            chunk = self._online_proc.bandpass(chunk, self._l_freq, self._h_freq)

        self.chunk_processed.emit(chunk)

        freqs, psd = welch(chunk[0], self.source.sfreq,
                           nperseg=min(128, chunk.shape[1]))
        self.spectrum_updated.emit(freqs, psd)
        self.progress.emit(self.source.progress)

    def set_filter(self, l_freq: float, h_freq: float):
        self._l_freq = l_freq
        self._h_freq = h_freq

    def set_filter_enabled(self, enabled: bool):
        self._filter_enabled = enabled

    def set_speed(self, speed: float):
        self._speed = max(0.01, speed)
        self.source.set_speed(speed)

    @property
    def speed(self) -> float:
        return self.source._speed

    def seek(self, sample_idx: int):
        self.source.seek(sample_idx)

    def reset(self):
        self.source.reset()
        if self._online_proc is not None:
            self._online_proc.reset_state()

    def set_loop(self, enabled: bool):
        self.source.set_loop(enabled)
