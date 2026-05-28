"""
EEG Waveform Widget
===================
Matplotlib-based scrolling EEG display supporting batch and stream modes.
"""
from __future__ import annotations
import numpy as np
from typing import List, Optional
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class EEGWaveformWidget(FigureCanvasQTAgg):
    """EEG waveform display with batch and streaming modes.

    - plot_batch(): static view of entire dataset
    - update_stream(): append chunk to rolling buffer
    """

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(10, 5), facecolor='#1e1e1e')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#1e1e1e')
        super().__init__(self.fig)
        self.setParent(parent)
        self._buffer = None
        self._ch_names: List[str] = []
        self._sfreq = 256.0
        self._window_samples = 0
        self._yscale = 50.0  # μV spacing between channels

    def plot_batch(self, data: np.ndarray, sfreq: float,
                   ch_names: Optional[List[str]] = None):
        """Plot full dataset (offline batch mode)."""
        self.ax.clear()
        n_ch, n_samples = data.shape
        times = np.arange(n_samples) / sfreq
        for i in range(n_ch):
            self.ax.plot(times, data[i] + i * self._yscale,
                         linewidth=0.3, color='#00ff88')
        self.ax.set_xlabel('Time (s)', color='white')
        self.ax.set_ylabel('Channel', color='white')
        self.ax.tick_params(colors='white')
        self.ax.set_yticks([i * self._yscale for i in range(n_ch)])
        if ch_names:
            self.ax.set_yticklabels(ch_names)
        self.draw_idle()

    def _init_buffer(self, n_channels: int, sfreq: float,
                     ch_names: List[str], window_sec: float = 5.0):
        """Initialize rolling buffer for stream mode."""
        self._sfreq = sfreq
        self._ch_names = ch_names
        self._window_samples = int(window_sec * sfreq)
        self._buffer = np.zeros((n_channels, self._window_samples))
        self._yscale = 50.0

    def update_stream(self, chunk: np.ndarray):
        """Append new chunk to rolling buffer and refresh display."""
        if self._buffer is None:
            raise RuntimeError("Call _init_buffer() before update_stream()")
        n_ch, n_new = chunk.shape
        if n_ch != self._buffer.shape[0]:
            raise ValueError(
                f"Expected {self._buffer.shape[0]} channels, got {n_ch}"
            )
        self._buffer = np.roll(self._buffer, -n_new, axis=1)
        self._buffer[:, -n_new:] = chunk

        self.ax.clear()
        t = np.arange(self._window_samples) / self._sfreq
        for i in range(n_ch):
            self.ax.plot(t, self._buffer[i] + i * self._yscale,
                         linewidth=0.3, color='#00ff88')
        self.ax.set_xlabel('Time (s)', color='white')
        self.ax.tick_params(colors='white')
        self.ax.set_yticks([i * self._yscale for i in range(n_ch)])
        if self._ch_names:
            self.ax.set_yticklabels(self._ch_names)
        self.draw_idle()

    def clear(self):
        """Clear the plot."""
        self.ax.clear()
        self._buffer = None
        self.draw_idle()
