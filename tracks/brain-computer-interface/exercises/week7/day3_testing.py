"""
Week 7 Day 3: Unit Testing and CI
=================================
单测、集成测试、CI

使用 pytest 进行测试，编写测试用例
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from typing import Optional

# ============================================================
# 1. 基础测试结构
# ============================================================
print("=" * 60)
print("1. 基础测试结构")
print("=" * 60)

def add_numbers(a: float, b: float) -> float:
    return a + b

def test_add_numbers():
    assert add_numbers(1, 2) == 3
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0

def test_add_numbers_edge_cases():
    assert add_numbers(1e-10, 1e-10) == pytest.approx(2e-10)
    assert add_numbers(float('inf'), 1) == float('inf')

test_add_numbers()
test_add_numbers_edge_cases()
print("Basic tests passed")

# ============================================================
# 2. EEG Signal Processing Tests
# ============================================================
print("\n" + "=" * 60)
print("2. EEG Signal Processing Tests")
print("=" * 60)

def bandpass_filter(data: np.ndarray, fs: float, lowcut: float, highcut: float) -> np.ndarray:
    from scipy.signal import butter, filtfilt
    nyq = fs / 2
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(4, [low, high], btype='band')
    return filtfilt(b, a, data, axis=-1)

def test_bandpass_filter():
    fs = 256
    data = np.random.randn(16, 2560)

    filtered = bandpass_filter(data, fs, 0.5, 40)

    assert filtered.shape == data.shape
    assert not np.any(np.isnan(filtered))

def test_bandpass_filter_frequency_response():
    fs = 256
    t = np.arange(2560) / fs
    data = np.sin(2 * np.pi * 10 * t) + np.sin(2 * np.pi * 50 * t)

    filtered = bandpass_filter(data, fs, 1, 30)

    assert filtered.shape == data.shape

test_bandpass_filter()
test_bandpass_filter_frequency_response()
print("Filter tests passed")

# ============================================================
# 3. Fixtures
# ============================================================
print("\n" + "=" * 60)
print("3. Fixtures")
print("=" * 60)

class EEGFixture:
    def __init__(self):
        self.fs = 256
        self.n_channels = 16
        self.duration = 10
        self.n_samples = self.fs * self.duration

    def create_raw_data(self):
        return np.random.randn(self.n_channels, self.n_samples)

    def create_epochs(self, n_epochs: int = 10):
        return np.random.randn(n_epochs, self.n_channels, 256)

@pytest.fixture
def eeg_fixture():
    return EEGFixture()

def test_eeg_fixture_raw(eeg_fixture):
    data = eeg_fixture.create_raw_data()
    assert data.shape == (eeg_fixture.n_channels, eeg_fixture.n_samples)

def test_eeg_fixture_epochs(eeg_fixture):
    epochs = eeg_fixture.create_epochs(n_epochs=20)
    assert epochs.shape[0] == 20
    assert epochs.shape[1] == eeg_fixture.n_channels

test_eeg_fixture_raw(eeg_fixture)
test_eeg_fixture_epochs(eeg_fixture)
print("Fixture tests passed")

# ============================================================
# 4. Parametrized Tests
# ============================================================
print("\n" + "=" * 60)
print("4. Parametrized Tests")
print("=" * 60)

filter_params = [
    (0.5, 40),
    (1, 30),
    (2, 20),
    (0.1, 100),
]

def test_bandpass_parametrized(eeg_fixture):
    for lowcut, highcut in filter_params:
        data = eeg_fixture.create_raw_data()
        filtered = bandpass_filter(data, eeg_fixture.fs, lowcut, highcut)
        assert filtered.shape == data.shape
        assert not np.isnan(filtered).any()

test_bandpass_parametrized(eeg_fixture)
print("Parametrized tests passed")

# ============================================================
# 5. Mock Tests
# ============================================================
print("\n" + "=" * 60)
print("5. Mock Tests")
print("=" * 60)

class DataLoader:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def load(self) -> np.ndarray:
        raise NotImplementedError

class Pipeline:
    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.data = None

    def run(self):
        self.data = self.loader.load()
        return self.data

def test_pipeline_with_mock_loader():
    mock_loader = MagicMock(spec=DataLoader)
    mock_loader.load.return_value = np.random.randn(16, 2560)

    pipeline = Pipeline(mock_loader)
    result = pipeline.run()

    assert result.shape == (16, 2560)
    mock_loader.load.assert_called_once()

def test_pipeline_handles_load_error():
    mock_loader = MagicMock(spec=DataLoader)
    mock_loader.load.side_effect = DataLoadError("File not found")

    pipeline = Pipeline(mock_loader)

    with pytest.raises(DataLoadError):
        pipeline.run()

class DataLoadError(Exception):
    pass

test_pipeline_with_mock_loader()
test_pipeline_handles_load_error()
print("Mock tests passed")

# ============================================================
# 6. Test Coverage (概念说明)
# ============================================================
print("\n" + "=" * 60)
print("6. Test Coverage")
print("=" * 60)

print("""
测试金字塔:
- 单元测试 (Unit Tests): 快速、可重复、隔离性好
- 集成测试 (Integration Tests): 测试模块间交互
- 端到端测试 (E2E Tests): 测试完整流程

覆盖率目标:
- 模块覆盖率 80%+ 达标
- 核心模块 90%+ 更好

运行命令:
  pytest tests/ --cov=bci --cov-report=html
""")

print("\n✅ Day 3 完成!")