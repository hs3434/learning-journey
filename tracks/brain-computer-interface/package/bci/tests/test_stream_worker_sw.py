"""StreamWorker + SlidingWindow integration tests."""
import numpy as np
import pytest


class TestStreamWorkerSlidingWindow:
    def test_worker_has_sliding_window_attribute(self):
        from bci.gui.worker import StreamWorker
        # Use a mock source to avoid file I/O
        from bci.source import SessionSource
        # Just test instantiation with a dummy path
        sw = StreamWorker("/nonexistent.fif", chunk_duration=0.1)
        assert hasattr(sw, "sliding_window")
        assert sw.sliding_window is None  # default: not configured

    def test_set_sliding_window_stores_config(self):
        from bci.gui.worker import StreamWorker
        from bci.streaming import SlidingWindow
        sw = StreamWorker("/nonexistent.fif", chunk_duration=0.1)
        swin = SlidingWindow(n_channels=64, window_size=1000, decision_interval=25)
        sw.set_sliding_window(swin)
        assert sw.sliding_window is swin
