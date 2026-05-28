# Week 7 Day 4: Documentation and Type Hints

## 核心概念

### 1. 类型提示

```python
import numpy as np
from typing import List, Optional, Tuple, Dict

def process_eeg_data(
    data: np.ndarray,
    fs: float,
    lowcut: Optional[float] = None,
    highcut: Optional[float] = None
) -> np.ndarray:
    """处理 EEG 数据"""
    ...
```

### 2. 复杂类型

```python
from dataclasses import dataclass

@dataclass
class FilterConfig:
    lowcut: float = 0.5
    highcut: float = 40.0
    notch_freq: Optional[int] = 50
    order: int = 4

@dataclass
class EpochConfig:
    tmin: float = -0.2
    tmax: float = 0.5
    baseline: Tuple[Optional[float], Optional[float]] = (None, 0)
    reject_threshold: Optional[Dict[str, float]] = None
```

### 3. Docstring 风格

```python
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

    def load(self, filepath: str) -> np.ndarray:
        """
        从文件加载 EEG 数据

        Args:
            filepath: EEG 文件路径

        Returns:
            加载的数据数组
        """
        ...
```

### 4. TypeAlias

```python
from typing import TypeAlias

EEGSamples: TypeAlias = np.ndarray
ChannelNames: TypeAlias = List[str]
EpochsData: TypeAlias = np.ndarray

def compute_stats(epochs: EpochsData) -> Dict[str, float]:
    ...
```

## 文档工具

### Sphinx

```bash
# 安装
pip install sphinx sphinx-rtd-theme

# 初始化
sphinx-quickstart docs

# 构建
sphinx-build docs docs/_build/html
```

### mkdocs

```bash
pip install mkdocs mkdocs-material

# 初始化
mkdocs new my-project

# 本地预览
mkdocs serve
```

## 练习要点

1. 掌握类型提示
2. 学会写 docstring
3. 了解文档工具

## 参考资料

- [Python typing](https://docs.python.org/3/library/typing.html)
- [Sphinx 文档](https://www.sphinx-doc.org/)
- [mkdocs](https://www.mkdocs.org/)