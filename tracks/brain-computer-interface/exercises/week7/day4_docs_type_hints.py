"""
Week 7 Day 4: Documentation and Type Hints
===========================================
文档生成、类型提示
添加 docstring 和类型注解
"""
import numpy as np
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass, field
from pathlib import Path

# ============================================================
# 1. 类型提示基础
# ============================================================
print("=" * 60)
print("1. 类型提示基础")
print("=" * 60)

def process_eeg_data(
    data: np.ndarray,
    fs: float,
    lowcut: Optional[float] = None,
    highcut: Optional[float] = None
) -> np.ndarray:
    """
    处理 EEG 数据（带类型提示）

    Args:
        data: EEG 数据，shape (n_channels, n_samples)
        fs: 采样率 (Hz)
        lowcut: 低频截止频率 (Hz)，None 表示不过滤
        highcut: 高频截止频率 (Hz)，None 表示不过滤

    Returns:
        处理后的 EEG 数据

    Raises:
        ValueError: 当 fs <= 0 时
    """
    if fs <= 0:
        raise ValueError(f"采样率必须大于0，当前值: {fs}")

    from scipy.signal import butter, filtfilt

    if lowcut is not None and highcut is not None:
        nyq = fs / 2
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(4, [low, high], btype='band')
        return filtfilt(b, a, data, axis=-1)

    return data


result = process_eeg_data(np.random.randn(16, 2560), fs=256.0, lowcut=0.5, highcut=40)
print(f"处理后 shape: {result.shape}")

# ============================================================
# 2. 复杂类型
# ============================================================
print("\n" + "=" * 60)
print("2. 复杂类型")
print("=" * 60)

@dataclass
class FilterConfig:
    """滤波配置"""
    lowcut: float = 0.5
    highcut: float = 40.0
    notch_freq: Optional[int] = 50
    order: int = 4

@dataclass
class EpochConfig:
    """Epoch 配置"""
    tmin: float = -0.2
    tmax: float = 0.5
    baseline: Tuple[Optional[float], Optional[float]] = (None, 0)
    reject_threshold: Optional[Dict[str, float]] = field(default_factory=lambda: {'eeg': 150e-6})

def create_pipeline_config(
    filter_params: FilterConfig,
    epoch_params: Optional[EpochConfig] = None,
    channels: Optional[List[str]] = None
) -> Dict[str, object]:
    """创建 pipeline 配置字典"""
    config = {
        'filter': filter_params,
        'epoch': epoch_params or EpochConfig(),
        'channels': channels
    }
    return config

config = create_pipeline_config(FilterConfig())
print(f"Config type: {type(config)}")
print(f"Filter lowcut: {config['filter'].lowcut}")

# ============================================================
# 3. Docstring 风格
# ============================================================
print("\n" + "=" * 60)
print("3. Docstring 风格")
print("=" * 60)

class EEGProcessor:
    """
    EEG 数据处理器

    支持时域和频域分析，可进行滤波、特征提取等操作。

    Attributes:
        fs: 采样率
        data: 当前加载的数据

    Example:
        >>> processor = EEGProcessor(fs=256)
        >>> processor.load('data.fif')
        >>> filtered = processor.filter(lowcut=0.5, highcut=40)
    """

    def __init__(self, fs: float) -> None:
        """
        初始化 EEG 处理器

        Args:
            fs: 采样率 (Hz)
        """
        self.fs = fs
        self.data: Optional[np.ndarray] = None

    def load(self, filepath: Path) -> np.ndarray:
        """
        从文件加载 EEG 数据

        Args:
            filepath: EEG 文件路径

        Returns:
            加载的数据数组
        """
        import mne
        raw = mne.io.read_raw_fif(filepath, preload=True, verbose=False)
        self.data = raw.get_data()
        return self.data

    def filter(self, lowcut: float, highcut: float) -> np.ndarray:
        """应用带通滤波"""
        if self.data is None:
            raise ValueError("请先加载数据")
        return process_eeg_data(self.data, self.fs, lowcut, highcut)


processor = EEGProcessor(fs=256)
print(f"EEGProcessor docstring:\n{processor.__doc__}")

# ============================================================
# 4. 类型别名与 Protocol
# ============================================================
print("\n" + "=" * 60)
print("4. 类型别名")
print("=" * 60)

EEGSamples = np.ndarray
ChannelNames = List[str]
EpochsData = np.ndarray

def compute_epoch_stats(epochs: EpochsData) -> Dict[str, float]:
    """计算 epoch 统计量"""
    return {
        'mean': float(np.mean(epochs)),
        'std': float(np.std(epochs)),
        'min': float(np.min(epochs)),
        'max': float(np.max(epochs))
    }

epochs_sample = np.random.randn(100, 16, 200)
stats = compute_epoch_stats(epochs_sample)
print(f"Epoch stats: {stats}")

print("\n✅ Day 4 完成!")