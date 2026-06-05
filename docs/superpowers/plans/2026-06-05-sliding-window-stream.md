# SlidingWindow Stream 模式适配 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 stream 模式下，让任何 decoder（特别是需要大窗口的 Transformer）能通过 SlidingWindow 实时解码。

**Architecture:** 新增 `bci/streaming/sliding_window.py` 纯 Python 模块（参考 spec 610-690 行），StreamWorker 接入 SlidingWindow 替代当前的"每 chunk 预测一次"。GUI 加 window_size / decision_interval 控件。Mock / LSL / BrainFlow 数据源**不在 v1.1 范围**——复用现有 `SessionSource`（文件回放）。

**Tech Stack:** Python ≥ 3.11, numpy, PyQt6, PyTorch（已有）

---

## 背景与现状

`stream_tab.py` + `StreamWorker` 已在工作，但当前实现：
```python
# worker.py:171
X = chunk[None, :, :]  # window = chunk (0.1s ≈ 16 samples)
proba = self._model.predict_proba(X)[0]
```
对 Transformer（n_times ≥ 1000）完全跑不通。spec 已规定"SlidingWindow 由应用层管理，不属于 decoder"，本计划就是把这个 spec 落实。

参考设计：`docs/superpowers/specs/2026-06-03-transformer-decoder-design.md` 第 610-697 行（"应用层 SlidingWindow 模式"章节）。

---

## 文件结构

### 新增

| 文件 | 行数 | 职责 |
|------|------|------|
| `bci/streaming/__init__.py` | ~5 | 包入口，导出 `SlidingWindow` |
| `bci/streaming/sliding_window.py` | ~120 | 滚动窗口缓冲 + 触发节奏控制（参考 spec 624-690 行） |
| `bci/tests/test_sliding_window.py` | ~150 | 单元测试 |
| `bci/tests/test_stream_worker_sw.py` | ~120 | StreamWorker + SlidingWindow 集成测试 |

### 修改

| 文件 | 改动 |
|------|------|
| `bci/gui/worker.py` | `StreamWorker` 接入 SlidingWindow；新增 `set_sliding_window()` 方法；`_emit_chunk` 改用 SW 触发节奏 |
| `bci/gui/stream_tab.py` | toolbar 加 `window_size`、`decision_interval` 输入框；`_on_start` 把 SW 配置传给 worker |
| `pyproject.toml` | 不变（无新依赖） |

---

## Task 1: SlidingWindow 核心（构造器 + push）

**Files:**
- Create: `tracks/brain-computer-interface/package/bci/streaming/__init__.py`
- Create: `tracks/brain-computer-interface/package/bci/streaming/sliding_window.py`
- Test: `tracks/brain-computer-interface/package/bci/tests/test_sliding_window.py`

- [ ] **Step 1.1: Write the failing test — 构造器校验**

```python
# bci/tests/test_sliding_window.py
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
```

- [ ] **Step 1.2: Run test, verify it fails**

```bash
cd tracks/brain-computer-interface/package
PYTHONPATH=. .venv/bin/python -m pytest bci/tests/test_sliding_window.py -v
```
Expected: `ModuleNotFoundError: No module named 'bci.streaming'`

- [ ] **Step 1.3: Create package skeleton**

Create `bci/streaming/__init__.py`:
```python
"""Streaming utilities — sliding window, sources (future)."""
from bci.streaming.sliding_window import SlidingWindow

__all__ = ["SlidingWindow"]
```

Create `bci/streaming/sliding_window.py`:
```python
"""
SlidingWindow — rolling sample buffer with decision-interval triggering.

Application-layer wrapper around any decoder's predict_proba.
Decoder-agnostic: works with LDA / CNN / SSVEP / FBCCA / Transformer.
"""
from __future__ import annotations
import numpy as np


class SlidingWindow:
    """Rolling buffer + ready/consume semantics.

    Usage:
        sw = SlidingWindow(n_channels=64, window_size=1000, decision_interval=25)
        for chunk in eeg_stream:
            sw.push(chunk)
            if sw.ready():
                window = sw.get_window()                 # (n_ch, window_size)
                probs = decoder.predict_proba(window[None])[0]  # (n_classes,)
                act(probs)
                sw.consume()
    """

    def __init__(self, n_channels: int, window_size: int, decision_interval: int):
        if window_size <= 0:
            raise ValueError(f"window_size={window_size} must be positive")
        if decision_interval <= 0:
            raise ValueError(f"decision_interval={decision_interval} must be positive")
        if decision_interval > window_size:
            raise ValueError(
                f"decision_interval={decision_interval} cannot exceed "
                f"window_size={window_size}"
            )
        self.n_channels = n_channels
        self.window_size = window_size
        self.decision_interval = decision_interval
        self._buf = np.zeros((n_channels, window_size), dtype=np.float32)
        self._n_filled = 0
        self._write_pos = 0
        self._since_last = 0

    def push(self, chunk: np.ndarray) -> None:
        """Append chunk. chunk: (n_channels, n_new_samples) or (n_channels,)."""
        if chunk.ndim == 1:
            chunk = chunk[:, None]
        if chunk.shape[0] != self.n_channels:
            raise ValueError(
                f"chunk.shape[0]={chunk.shape[0]} != n_channels={self.n_channels}"
            )
        n_new = chunk.shape[1]
        for i in range(n_new):
            self._buf[:, self._write_pos] = chunk[:, i]
            self._write_pos = (self._write_pos + 1) % self.window_size
        self._n_filled = min(self._n_filled + n_new, self.window_size)
        self._since_last += n_new

    def ready(self) -> bool:
        """True when buffer is full AND decision_interval samples accumulated."""
        return (
            self._n_filled >= self.window_size
            and self._since_last >= self.decision_interval
        )

    def get_window(self) -> np.ndarray:
        """Return (n_channels, window_size) in chronological order."""
        if self._n_filled < self.window_size:
            return self._buf[:, :self._n_filled].copy()
        return np.concatenate(
            [self._buf[:, self._write_pos:], self._buf[:, :self._write_pos]],
            axis=-1,
        ).copy()

    def consume(self) -> None:
        """Reset since_last counter (call after get_window)."""
        self._since_last = 0

    def reset(self) -> None:
        """Clear buffer (new trial / session)."""
        self._buf[:] = 0
        self._n_filled = 0
        self._write_pos = 0
        self._since_last = 0
```

- [ ] **Step 1.4: Run test, verify it passes**

```bash
cd tracks/brain-computer-interface/package
PYTHONPATH=. .venv/bin/python -m pytest bci/tests/test_sliding_window.py::TestSlidingWindowConstructor -v
```
Expected: 4 passed

- [ ] **Step 1.5: Commit**

```bash
git add tracks/brain-computer-interface/package/bci/streaming/ tracks/brain-computer-interface/package/bci/tests/test_sliding_window.py
git commit -m "feat(streaming): add SlidingWindow with constructor validation"
```

---

## Task 2: SlidingWindow 行为（push / ready / get_window / consume / reset）

**Files:**
- Modify: `tracks/brain-computer-interface/package/bci/tests/test_sliding_window.py`

- [ ] **Step 2.1: Write the failing tests**

Append to `test_sliding_window.py`:
```python
class TestSlidingWindowBehavior:
    def test_not_ready_until_buffer_full(self):
        sw = SlidingWindow(n_channels=2, window_size=100, decision_interval=25)
        sw.push(np.zeros((2, 50), dtype=np.float32))
        assert not sw.ready()
        sw.push(np.zeros((2, 50), dtype=np.float32))
        assert sw.ready()

    def test_ready_requires_decision_interval(self):
        sw = SlidingWindow(n_channels=2, window_size=100, decision_interval=50)
        # Fill buffer with exactly window_size samples
        sw.push(np.zeros((2, 100), dtype=np.float32))
        # since_last = 100, decision_interval = 50 → should be ready
        assert sw.ready()
        # After consume, since_last = 0, but still filled → not ready
        sw.consume()
        assert not sw.ready()

    def test_get_window_returns_chronological_order(self):
        sw = SlidingWindow(n_channels=1, window_size=5, decision_interval=1)
        # Push 5 samples: [10, 20, 30, 40, 50] (with wrap-around)
        sw.push(np.array([[10, 20, 30, 40, 50]], dtype=np.float32))
        window = sw.get_window()
        np.testing.assert_array_equal(window, [[10, 20, 30, 40, 50]])

    def test_get_window_handles_wrap_around(self):
        sw = SlidingWindow(n_channels=1, window_size=5, decision_interval=1)
        # Fill: [1, 2, 3, 4, 5]
        sw.push(np.array([[1, 2, 3, 4, 5]], dtype=np.float32))
        # Push 3 more (overwrite oldest): [4, 5, 6, 7, 8]
        sw.push(np.array([[6, 7, 8]], dtype=np.float32))
        window = sw.get_window()
        np.testing.assert_array_equal(window, [[4, 5, 6, 7, 8]])

    def test_get_window_before_full_returns_partial(self):
        sw = SlidingWindow(n_channels=1, window_size=10, decision_interval=5)
        sw.push(np.array([[1, 2, 3]], dtype=np.float32))
        window = sw.get_window()
        assert window.shape == (1, 3)
        np.testing.assert_array_equal(window, [[1, 2, 3]])

    def test_reset_clears_buffer(self):
        sw = SlidingWindow(n_channels=1, window_size=5, decision_interval=1)
        sw.push(np.array([[1, 2, 3, 4, 5]], dtype=np.float32))
        sw.reset()
        assert not sw.ready()
        assert sw.get_window().shape == (1, 0)

    def test_push_rejects_wrong_n_channels(self):
        sw = SlidingWindow(n_channels=4, window_size=10, decision_interval=1)
        with pytest.raises(ValueError, match="n_channels"):
            sw.push(np.zeros((2, 5), dtype=np.float32))

    def test_push_accepts_1d_chunk(self):
        sw = SlidingWindow(n_channels=3, window_size=10, decision_interval=1)
        sw.push(np.array([1, 2, 3], dtype=np.float32))
        assert sw._n_filled == 1
```

- [ ] **Step 2.2: Run tests, verify they pass**

```bash
cd tracks/brain-computer-interface/package
PYTHONPATH=. .venv/bin/python -m pytest bci/tests/test_sliding_window.py::TestSlidingWindowBehavior -v
```
Expected: 8 passed（step 1.3 的实现已经覆盖所有行为，无需新代码）

- [ ] **Step 2.3: Commit**

```bash
git add tracks/brain-computer-interface/package/bci/tests/test_sliding_window.py
git commit -m "test(streaming): cover SlidingWindow push/ready/get_window/consume/reset"
```

---

## Task 3: StreamWorker 接入 SlidingWindow（set_sliding_window 方法）

**Files:**
- Modify: `tracks/brain-computer-interface/package/bci/gui/worker.py`
- Test: `tracks/brain-computer-interface/package/bci/tests/test_stream_worker_sw.py`

- [ ] **Step 3.1: Write the failing test**

Create `bci/tests/test_stream_worker_sw.py`:
```python
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
```

- [ ] **Step 3.2: Run tests, verify they fail**

```bash
cd tracks/brain-computer-interface/package
PYTHONPATH=. .venv/bin/python -m pytest bci/tests/test_stream_worker_sw.py -v
```
Expected: `AttributeError: 'StreamWorker' object has no attribute 'sliding_window'`

- [ ] **Step 3.3: Add sliding_window attribute and setter to StreamWorker**

Modify `bci/gui/worker.py`, in `StreamWorker.__init__` (around line 117), add:
```python
        self._timer: Optional[QTimer] = None
        self._filter_enabled = True
        self._l_freq = 0.5
        self._h_freq = 40.0
        self._speed = 1.0
        self._online_proc = None
        self._chunk_samples = 0
        self._chunk_duration = chunk_duration
        self.sliding_window = None  # optional SlidingWindow for windowed prediction
```

Add new method after `load_model` (around line 213):
```python
    def set_sliding_window(self, sw) -> None:
        """Configure a SlidingWindow for windowed online prediction.

        When set, _emit_chunk pushes chunks into sw and only calls
        predict_proba when sw.ready() is True (instead of per-chunk).
        """
        self.sliding_window = sw
```

- [ ] **Step 3.4: Run tests, verify they pass**

```bash
cd tracks/brain-computer-interface/package
PYTHONPATH=. .venv/bin/python -m pytest bci/tests/test_stream_worker_sw.py -v
```
Expected: 2 passed

- [ ] **Step 3.5: Commit**

```bash
git add tracks/brain-computer-interface/package/bci/gui/worker.py tracks/brain-computer-interface/package/bci/tests/test_stream_worker_sw.py
git commit -m "feat(gui): StreamWorker accepts optional SlidingWindow"
```

---

## Task 4: StreamWorker._emit_chunk 使用 SlidingWindow 触发预测

**Files:**
- Modify: `tracks/brain-computer-interface/package/bci/gui/worker.py`
- Modify: `tracks/brain-computer-interface/package/bci/tests/test_stream_worker_sw.py`

- [ ] **Step 4.1: Write the failing test**

Append to `test_stream_worker_sw.py`:
```python
class TestStreamWorkerEmitChunkWithSW:
    """Test that _emit_chunk uses SlidingWindow when configured."""

    def test_emit_chunk_uses_sliding_window_when_ready(self, monkeypatch):
        from bci.gui.worker import StreamWorker
        from bci.streaming import SlidingWindow

        # Build worker with a fake source
        sw = StreamWorker("/nonexistent.fif", chunk_duration=0.1)
        # Replace source.read_chunk with a deterministic stub
        chunk = np.ones((4, 16), dtype=np.float32)  # 4ch × 16 samples
        monkeypatch.setattr(sw.source, "read_chunk", lambda n: chunk)
        monkeypatch.setattr(sw.source, "n_channels", 4)
        monkeypatch.setattr(sw.source, "sfreq", 160.0)
        monkeypatch.setattr(sw.source, "chunk_duration", 0.1)

        # Configure SW that becomes ready after one push
        swin = SlidingWindow(n_channels=4, window_size=16, decision_interval=16)
        sw.set_sliding_window(swin)

        # Mock model
        class FakeModel:
            classes_ = np.array([0, 1])
            def predict_proba(self, X):
                # Record the shape that was passed
                self.last_X_shape = X.shape
                return np.array([[0.3, 0.7]])
        fake_model = FakeModel()
        sw._model = fake_model
        sw._label_names = ["L", "R"]

        # Capture prediction emission
        predictions = []
        sw.prediction.connect(lambda lbl, conf: predictions.append((lbl, conf)))

        # Emit one chunk → SW becomes ready → predict_proba called
        sw._emit_chunk()
        assert fake_model.last_X_shape == (1, 4, 16)
        assert len(predictions) == 1
        assert predictions[0] == ("R", 0.7)
        # SW should be consumed (since_last reset)
        assert swin._since_last == 0

    def test_emit_chunk_skips_prediction_when_not_ready(self, monkeypatch):
        from bci.gui.worker import StreamWorker
        from bci.streaming import SlidingWindow

        sw = StreamWorker("/nonexistent.fif", chunk_duration=0.1)
        chunk = np.ones((4, 16), dtype=np.float32)
        monkeypatch.setattr(sw.source, "read_chunk", lambda n: chunk)
        monkeypatch.setattr(sw.source, "n_channels", 4)
        monkeypatch.setattr(sw.source, "sfreq", 160.0)
        monkeypatch.setattr(sw.source, "chunk_duration", 0.1)

        # SW requires window_size=100 → not ready after one 16-sample chunk
        swin = SlidingWindow(n_channels=4, window_size=100, decision_interval=25)
        sw.set_sliding_window(swin)

        class FakeModel:
            predict_called = False
            def predict_proba(self, X):
                self.predict_called = True
                return np.array([[0.5, 0.5]])
            classes_ = np.array([0, 1])
        fake = FakeModel()
        sw._model = fake

        predictions = []
        sw.prediction.connect(lambda lbl, conf: predictions.append((lbl, conf)))
        sw._emit_chunk()
        assert not fake.predict_called
        assert len(predictions) == 0

    def test_emit_chunk_falls_back_to_per_chunk_without_sw(self, monkeypatch):
        """Backward compat: no SW → predict on chunk directly (existing behavior)."""
        from bci.gui.worker import StreamWorker

        sw = StreamWorker("/nonexistent.fif", chunk_duration=0.1)
        chunk = np.ones((4, 16), dtype=np.float32)
        monkeypatch.setattr(sw.source, "read_chunk", lambda n: chunk)
        monkeypatch.setattr(sw.source, "n_channels", 4)
        monkeypatch.setattr(sw.source, "sfreq", 160.0)
        monkeypatch.setattr(sw.source, "chunk_duration", 0.1)

        class FakeModel:
            last_X_shape = None
            def predict_proba(self, X):
                self.last_X_shape = X.shape
                return np.array([[0.5, 0.5]])
            classes_ = np.array([0, 1])
        fake = FakeModel()
        sw._model = fake
        sw._label_names = ["L", "R"]

        predictions = []
        sw.prediction.connect(lambda lbl, conf: predictions.append((lbl, conf)))
        sw._emit_chunk()
        assert fake.last_X_shape == (1, 4, 16)  # direct chunk prediction
        assert len(predictions) == 1
```

- [ ] **Step 4.2: Run tests, verify they fail**

```bash
cd tracks/brain-computer-interface/package
PYTHONPATH=. .venv/bin/python -m pytest bci/tests/test_stream_worker_sw.py::TestStreamWorkerEmitChunkWithSW -v
```
Expected: 3 failed (because _emit_chunk doesn't use SW yet)

- [ ] **Step 4.3: Modify _emit_chunk to use SlidingWindow when set**

In `bci/gui/worker.py`, replace the `_emit_chunk` method body (lines 155-185):
```python
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

        if self._model is not None:
            try:
                if self.sliding_window is not None:
                    self.sliding_window.push(chunk)
                    if not self.sliding_window.ready():
                        # Also emit spectrum/progress even when not predicting
                        freqs, psd = welch(chunk[0], self.source.sfreq,
                                           nperseg=min(128, chunk.shape[1]))
                        self.spectrum_updated.emit(freqs, psd)
                        self.progress.emit(self.source.progress)
                        return
                    window = self.sliding_window.get_window()
                    X = window[None, :, :]
                    self.sliding_window.consume()
                else:
                    X = chunk[None, :, :]

                proba = self._model.predict_proba(X)[0]
                pred_idx = int(np.argmax(proba))
                label = (self._label_names[pred_idx]
                         if pred_idx < len(self._label_names)
                         else str(pred_idx))
                confidence = float(proba[pred_idx])
                self.prediction.emit(label, confidence)
            except Exception:
                pass

        freqs, psd = welch(chunk[0], self.source.sfreq,
                           nperseg=min(128, chunk.shape[1]))
        self.spectrum_updated.emit(freqs, psd)
        self.progress.emit(self.source.progress)
```

- [ ] **Step 4.4: Run tests, verify they pass**

```bash
cd tracks/brain-computer-interface/package
PYTHONPATH=. .venv/bin/python -m pytest bci/tests/test_stream_worker_sw.py -v
```
Expected: 5 passed（2 来自 Task 3 + 3 来自本任务）

- [ ] **Step 4.5: Commit**

```bash
git add tracks/brain-computer-interface/package/bci/gui/worker.py tracks/brain-computer-interface/package/bci/tests/test_stream_worker_sw.py
git commit -m "feat(gui): _emit_chunk uses SlidingWindow for windowed prediction"
```

---

## Task 5: stream_tab.py UI 控件（window_size + decision_interval）

**Files:**
- Modify: `tracks/brain-computer-interface/package/bci/gui/stream_tab.py`
- Modify: `tracks/brain-computer-interface/package/bci/gui/worker.py` (no — just SW already supports it)
- Test: manual / smoke (no headless test for Qt widgets)

- [ ] **Step 5.1: Add window_size and decision_interval inputs to toolbar**

In `bci/gui/stream_tab.py`, in `_setup_ui` after the `loop_cb` block (around line 92), add a new section before `toolbar.addStretch()`:
```python
        toolbar.addSpacing(20)
        toolbar.addWidget(QLabel("Window:"))
        self.window_size_input = QSpinBox()
        self.window_size_input.setRange(50, 5000)
        self.window_size_input.setValue(1000)
        self.window_size_input.setSuffix(" smp")
        toolbar.addWidget(self.window_size_input)

        toolbar.addWidget(QLabel("Step:"))
        self.decision_interval_input = QSpinBox()
        self.decision_interval_input.setRange(1, 1000)
        self.decision_interval_input.setValue(25)
        self.decision_interval_input.setSuffix(" smp")
        toolbar.addWidget(self.decision_interval_input)
```

Add to imports at top of file:
```python
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QDoubleSpinBox, QSlider, QCheckBox, QTextEdit,
    QProgressBar, QMessageBox, QFileDialog, QSpinBox,
)
```

- [ ] **Step 5.2: Wire SW config in _on_start**

In `bci/gui/stream_tab.py`, in `_on_start` (around line 253), after `self._worker = StreamWorker(...)`, add:
```python
        # Configure SlidingWindow for windowed prediction
        from bci.streaming import SlidingWindow
        n_ch = self._source.n_channels
        swin = SlidingWindow(
            n_channels=n_ch,
            window_size=self.window_size_input.value(),
            decision_interval=self.decision_interval_input.value(),
        )
        self._worker.set_sliding_window(swin)
```

Note: the existing `n_ch = self._source.n_channels` line at 258 is now redundant; remove it.

- [ ] **Step 5.3: Manual smoke test**

```bash
cd tracks/brain-computer-interface/package
PYTHONPATH=. .venv/bin/python -c "from bci.gui.stream_tab import StreamTab; print('imports ok')"
```
Expected: `imports ok` (no QApplication needed for import check)

Then in a venv with PyQt6 (the package has it), launch the GUI:
```bash
PYTHONPATH=. .venv/bin/python -m bci
```
Expected: GUI opens, Stream tab shows Window/Step spinboxes after Loop checkbox. Clicking Start after loading a file should not error.

- [ ] **Step 5.4: Commit**

```bash
git add tracks/brain-computer-interface/package/bci/gui/stream_tab.py
git commit -m "feat(gui): stream tab exposes window_size + decision_interval controls"
```

---

## Task 6: 完整回归 + 文档同步

**Files:**
- Modify: `docs/superpowers/specs/2026-06-03-transformer-decoder-design.md` (remove SlidingWindow "v1 不实现" note since now implemented)
- Modify: `tracks/brain-computer-interface/package/bci/decoder/__init__.py` (docstring only, no code change)

- [ ] **Step 6.1: Run full test suite**

```bash
cd tracks/brain-computer-interface/package
PYTHONPATH=. .venv/bin/python -m pytest bci/tests/ --ignore=bci/tests/test_widgets.py --ignore=bci/tests/test_tabs.py --ignore=bci/tests/test_worker.py -v
```
Expected: all tests pass (33 from before + ~13 new = 46+)

- [ ] **Step 6.2: Update spec — change "v1 不实现" to "v1.1 已实现"**

In `docs/superpowers/specs/2026-06-03-transformer-decoder-design.md`:
- Line 694: Change "（v1 不实现，仅 spec 描述）" to "（v1.1 已实现，见 `bci/streaming/sliding_window.py`）"

- [ ] **Step 6.3: Commit doc sync**

```bash
git add docs/superpowers/specs/2026-06-03-transformer-decoder-design.md
git commit -m "docs(specs): mark SlidingWindow as v1.1 implemented"
```

---

## Self-Review

**1. Spec coverage:**
- ✅ SlidingWindow 类（spec 624-690）→ Task 1+2
- ✅ 接口契约（push/ready/get_window/consume/reset）→ Task 1+2
- ✅ 应用层与 decoder 解耦 → Task 3+4（不修改 decoder）
- ✅ 复用任意 decoder → Task 4 测试覆盖
- ⚠️ 职责划分表（spec 615-621）→ 在 StreamWorker 注释里已隐含
- ⚠️ LSL / BrainFlow → 显式不在范围（用户已确认）

**2. Placeholder scan:** 无"TBD" / "类似 Task N" / "add appropriate error handling"

**3. Type consistency:**
- `SlidingWindow(n_channels, window_size, decision_interval)` 在 Task 1 定义，Task 3-4 复用，签名一致
- `set_sliding_window(sw)` 在 Task 3 定义，Task 4 复用
- `sliding_window` 属性 Task 3 设置为 `None`，Task 4 检查 `is not None`

**4. Backward compat:** Task 4 测试 `test_emit_chunk_falls_back_to_per_chunk_without_sw` 显式验证无 SW 时行为不变。

---

## 完成后

可运行的端到端流式 demo：
1. 用 `batch_tab` 训练一个 TransformerDecoder
2. 保存模型
3. 切到 `stream_tab` 加载同一文件
4. 配置 Window=1000, Step=25（Transformer 推荐）
5. Load Model → Start
6. 看到实时 prediction（每 25 samples 触发一次，约 10Hz @ 250Hz）
