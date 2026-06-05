import numpy as np
import pytest
from bci.streaming.sliding_window import SlidingWindow


class TestSlidingWindowConstructor:
    def test_valid_construction(self):
        sw = SlidingWindow(n_channels=4, window_size=1000, decision_interval=25)
        assert sw.n_channels == 4
        assert sw.window_size == 1000
        assert sw.decision_interval == 25

    def test_rejects_decision_interval_zero(self):
        with pytest.raises(ValueError, match="decision_interval"):
            SlidingWindow(n_channels=4, window_size=1000, decision_interval=0)

    def test_rejects_decision_interval_larger_than_window(self):
        with pytest.raises(ValueError, match="decision_interval"):
            SlidingWindow(n_channels=4, window_size=100, decision_interval=200)

    def test_rejects_zero_window_size(self):
        with pytest.raises(ValueError, match="window_size"):
            SlidingWindow(n_channels=4, window_size=0, decision_interval=10)
