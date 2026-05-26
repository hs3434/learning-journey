# Week 7 Day 24：文档生成与类型提示

## 1. 为什么 BCI 项目需要文档？

BCI 代码的生命周期：

```
写代码(1天) → 自己用(1周) → 别人用(1月) → 维护迭代(1年)
  ↓              ↓              ↓               ↓
无需文档      简单注释       API 文档      完整文档+教程
```

**文档投资回报率**：
- 写 docstring：5 分钟
- 不写 → 同事问你接口怎么用：5 小时
- 不写 → 半年后自己忘了逻辑：1 天

---

## 2. 类型提示 (Type Hints)

### 2.1 基础类型标注

```python
from typing import Optional, List, Dict, Tuple, Union
import numpy as np
import mne

def bandpass_filter(
    data: np.ndarray,
    l_freq: float,
    h_freq: float,
    fs: int,
    order: int = 4,
) -> np.ndarray:
    """带通滤波

    Args:
        data: EEG 数据，shape (n_channels, n_times)
        l_freq: 高通截止频率 (Hz)
        h_freq: 低通截止频率 (Hz)
        fs: 采样率 (Hz)
        order: 滤波器阶数

    Returns:
        滤波后数据，shape 同输入

    Raises:
        ValueError: l_freq >= h_freq 时
    """
    ...
```

### 2.2 复杂类型

```python
# 可选参数
def load_data(filepath: str, preload: bool = True) -> mne.io.Raw:
    ...

# 联合类型
def classify(
    features: Union[np.ndarray, Dict[str, np.ndarray]],
    method: str = 'lda',
) -> Tuple[float, float]:
    ...

# 泛型
from typing import TypeVar, Generic
T = TypeVar('T')

class DataContainer(Generic[T]):
    def __init__(self, data: T):
        self.data: T = data
```

### 2.3 类型检查 (mypy)

```bash
# 安装
pip install mypy

# 运行类型检查
mypy bci_pipeline/ --ignore-missing-imports

# 发现的问题示例：
# error: Argument 1 to "bandpass_filter" has incompatible type "list";
#        expected "ndarray"
```

---

## 3. Docstring 规范

### 3.1 Google Style（推荐）

```python
def extract_epochs(
    raw: mne.io.Raw,
    events: np.ndarray,
    event_id: Dict[str, int],
    tmin: float = -0.2,
    tmax: float = 0.5,
    baseline: Optional[Tuple[Optional[float], Optional[float]]] = (None, 0),
    reject: Optional[Dict[str, float]] = None,
) -> mne.Epochs:
    """从连续数据中提取事件相关 Epoch。

    根据事件标记切分连续 EEG 数据，提取刺激前后的脑电片段。
    可选基线校正和自动伪迹拒绝。

    Args:
        raw: 预处理后的 MNE Raw 对象。
        events: 事件数组，shape (n_events, 3)，格式 [sample, 0, event_id]。
        event_id: 事件类型映射，如 {'left': 1, 'right': 2}。
        tmin: Epoch 起始时间（相对于事件），单位秒。
        tmax: Epoch 结束时间（相对于事件），单位秒。
        baseline: 基线校正窗口 (start, end)。None 表示不校正。
        reject: 拒绝阈值，如 {'eeg': 100e-6} 表示 100uV。

    Returns:
        mne.Epochs 对象，包含提取的 Epoch 数据。

    Raises:
        ValueError: events 数组格式不正确时。
        RuntimeError: 没有有效 Epoch 时。

    Examples:
        >>> events = np.array([[14400, 0, 1], [28800, 0, 2]])
        >>> event_id = {'left': 1, 'right': 2}
        >>> epochs = extract_epochs(raw, events, event_id)
        >>> print(len(epochs))
        2
    """
    ...
```

### 3.2 类级 Docstring

```python
class Preprocessor:
    """EEG 信号预处理器。

    封装滤波、Notch、重参考、ICA 等预处理操作。
    支持 FIR/IIR 两种滤波方法，可选基线校正。

    Attributes:
        config: 滤波参数配置 (FilterConfig)。
        logger: 模块级日志器。

    Examples:
        >>> config = FilterConfig(l_freq=1.0, h_freq=40.0)
        >>> proc = Preprocessor(config)
        >>> filtered = proc.process(raw)
    """
    
    def __init__(self, config: FilterConfig) -> None:
        self.config = config
        self.logger = logging.getLogger('bci.preprocessor')
```

---

## 4. 自动文档生成 (Sphinx)

### 4.1 项目结构

```
docs/
├── conf.py          # Sphinx 配置
├── index.rst        # 首页
├── api.rst          # API 参考
├── tutorial.rst     # 教程
└── Makefile
```

### 4.2 conf.py 核心配置

```python
# docs/conf.py
project = 'BCI Pipeline'
extensions = [
    'sphinx.ext.autodoc',       # 从 docstring 自动生成
    'sphinx.ext.napoleon',      # Google/NumPy 风格支持
    'sphinx.ext.typehints',     # 类型提示显示
    'sphinx.ext.viewcode',      # 源码链接
]

# 自动从代码提取
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}
```

### 4.3 API 文档页

```rst
.. _api:

API Reference
=============

.. automodule:: bci.preprocessor
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: bci.decoder
   :members:
```

### 4.4 生成文档

```bash
cd docs
make html
# 输出：docs/_build/html/index.html
```

---

## 5. README 模板

```markdown
# BCI Pipeline

A modular BCI (Brain-Computer Interface) data analysis pipeline.

## Quick Start

```python
from bci import BCIPipeline, PipelineConfig

config = PipelineConfig.from_yaml('config.yaml')
pipeline = BCIPipeline(config)
result = pipeline.run('eeg_raw.fif')
print(f"Accuracy: {result.scores['accuracy']:.1%}")
```

## Installation

```bash
pip install -e .
```

## Project Structure

```
bci_pipeline/
├── config.py        # Configuration management
├── loader.py        # Data loading
├── preprocessor.py  # Signal preprocessing
├── epocher.py       # Epoch extraction
├── decoder.py       # Classification
└── pipeline.py      # Main orchestrator
```

## Testing

```bash
pytest tests/ -v --cov=bci
```
```

---

## 6. 总结

| 概念 | 核心要点 |
|------|----------|
| 类型提示 | 函数签名标注输入输出类型 |
| mypy | 静态类型检查，编译期发现错误 |
| Google Style Docstring | Args/Returns/Raises/Examples |
| Sphinx | 自动从 docstring 生成 API 文档 |
| napoleon | 支持 Google/NumPy 风格 |
| README | 项目入口：安装/使用/测试 |
