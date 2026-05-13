# BCI 软件工程师学习计划

> 目标：1-3 个月快速补齐 BCI 软件工程师技能短板
> 背景：生物信息工程师，有 Python 项目经验

## 岗位技能缺口分析

| 技能 | 现状 | 优先级 |
|------|------|--------|
| Python 科学计算（NumPy/SciPy/Pandas） | 有基础 | 🔴 补齐 |
| GUI 开发（Qt） | 薄弱 | 🔴 重点 |
| 信号处理（滤波/FFT/小波） | 薄弱 | 🔴 重点 |
| EEG 处理（MNE-Python） | 零基础 | 🟡 核心 |
| BCI 解码（SSVEP/MI） | 零基础 | 🟡 核心 |
| Pipeline 工程化 | 有概念 | 🟡 加强 |

---

## 学习路线（8 周强化）

```
Week 1-2：Python 科学计算 + GUI 基础
Week 3-4：信号处理 + MNE-Python
Week 5-6：BCI 解码基础 + 可视化
Week 7-8：Pipeline 工程化 + 项目整合
```

---

## Week 1-2：Python 科学计算 + Qt GUI 基础

### Week 1：NumPy/Pandas 进阶

**目标**：熟练使用 NumPy/Pandas 进行数据处理

**每日节奏（3-4h）**：1h 理论 + 1.5h 项目 + 1h 复盘

| Day | 理论 | 实战 |
|-----|------|------|
| 1 | NumPy 数组操作、广播、向量化 | EEG 数据加载与整形 |
| 2 | Pandas DataFrame、GroupBy、merge | 批量处理 CSV/Excel |
| 3 | SciPy 统计、插值、信号基础 | 简单滤波操作 |
| 4 | Matplotlib 可视化、subplot、多图 | EEG 时序图绘制 |
| 5 | 科学计算综合练习 | 读取 EEG 数据并可视化 |
| 周末 | 复盘 | 产出：data-utils |

**Week1 配套项目**：EEG 数据处理工具（骨架）

```python
# projects/bci-data-utils/
# 数据读取、预处理、可视化基础

import numpy as np
import pandas as pd
import mne

class EEGDataLoader:
    """EEG 数据加载器"""

    def __init__(self, filepath):
        self.filepath = filepath
        self.raw = None
        self.data = None
        self.info = None

    def load_raw(self, format='auto'):
        """加载原始数据"""
        self.raw = mne.io.read_raw_xxx(self.filepath, preload=True)
        self.info = self.raw.info
        return self.raw

    def get_data(self, start=0, stop=None, picks='eeg'):
        """获取指定通道数据"""
        if self.raw is None:
            self.load_raw()
        return self.raw.get_data(picks=[picks], start=start, stop=stop)

    def to_dataframe(self):
        """转换为 DataFrame"""
        data = self.get_data()
        channels = self.raw.ch_names
        times = self.raw.times
        return pd.DataFrame(data.T, columns=channels, index=times)
```

---

### Week 2：Qt GUI 开发

**目标**：掌握 Qt for Python (PyQt/PySide)，能开发数据处理界面

**每日节奏**：1h 理论 + 2h 项目 + 1h 复盘

| Day | 理论 | 实战 |
|-----|------|------|
| 1 | Qt 架构、信号槽机制、widget 布局 | 窗口、按钮、标签 |
| 2 | QMainWindow、菜单、工具栏 | 简单 EEG 查看器界面 |
| 3 | QThread 信号处理、进度条 | 加载大数据不卡界面 |
| 4 | Matplotlib + QWidget 集成 | EEG 波形显示组件 |
| 5 | 布局管理、对话框、文件选择 | EEG 数据选择对话框 |
| 周末 | 复盘 | 产出：eeg-viewer |

**Week2 配套项目**：EEG 数据查看器

```python
# projects/eeg-viewer/
# EEG 数据可视化 GUI 工具

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

class EEGViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EEG Viewer")
        self.setup_ui()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Matplotlib canvas for EEG plot
        self.canvas = FigureCanvasQTAgg(plt.figure())
        layout.addWidget(self.canvas)

        # Control buttons
        # ...

class LoadWorker(QThread):
    progress = pyqtSignal(int)
    result = pyqtSignal(np.ndarray)
    error = pyqtSignal(str)

    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath
```

---

## Week 3-4：信号处理 + MNE-Python

### Week 3：信号处理基础

**目标**：理解滤波、FFT/STFT、小波分析，能处理 EEG 信号

**每日节奏**：1.5h 理论 + 1.5h 项目 + 1h 复盘

| Day | 理论 | 实战 |
|-----|------|------|
| 1 | 时域分析：均值、方差、RMS、峰值 | 计算 EEG 统计指标 |
| 2 | 频域分析：FFT、功率谱密度 | 绘制 EEG 频谱图 |
| 3 | 滤波：IIR/FIR、带通/ notch 滤波 | 去除 50Hz 工频干扰 |
| 4 | STFT 时频分析、频谱图 | 事件相关频谱分析 |
| 5 | 小波分析、去伪迹 | ICA 去除眼动伪迹 |
| 周末 | 复盘 | 产出：signal-processor |

**Week3 配套项目**：EEG 信号处理器

```python
# projects/signal-processor/
# EEG 滤波、去噪、特征提取

from scipy import signal
import numpy as np

class SignalProcessor:
    """EEG 信号处理器"""

    @staticmethod
    def bandpass_filter(data, lowcut, highcut, fs, order=4):
        """带通滤波"""
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = signal.butter(order, [low, high], btype='band')
        return signal.filtfilt(b, a, data)

    @staticmethod
    def remove_powerline(data, fs, freq=50):
        """去除工频干扰（notch 滤波）"""
        Q = 30  # Quality factor
        w0 = freq / (fs / 2)  # Normalized frequency
        b, a = signal.iirnotch(w0, Q)
        return signal.filtfilt(b, a, data)

    @staticmethod
    def compute_psd(data, fs, nperseg=256):
        """计算功率谱密度"""
        freqs, psd = signal.welch(data, fs, nperseg=nperseg)
        return freqs, psd

    @staticmethod
    def extract_features(data, fs):
        """提取特征：功率谱、峰值频率等"""
        freqs, psd = SignalProcessor.compute_psd(data, fs)

        # Alpha 功率 (8-13 Hz)
        alpha_idx = (freqs >= 8) & (freqs <= 13)
        alpha_power = np.mean(psd[alpha_idx])

        return {
            'alpha_power': alpha_power,
            'peak_freq': freqs[np.argmax(psd)]
        }
```

---

### Week 4：MNE-Python 深入

**目标**：掌握 MNE-Python 进行完整 EEG 分析流程

**每日节奏**：1.5h 理论 + 1.5h 项目 + 1h 复盘

| Day | 理论 | 实战 |
|-----|------|------|
| 1 | MNE 数据结构：Raw/Epochs/Evoked | 加载示例 EEG 数据 |
| 2 | 坏通道处理、重参考、ICA 伪迹去除 | 预处理 EEG 数据 |
| 3 | 事件标记、epoch 切分、trigger 对齐 | 提取事件相关 epoch |
| 4 | 时频分析、ERD/ERS、可视化 | 绘制 ERD/ERS 图 |
| 5 | 解码流程：特征提取 + 分类器 | 简单 MI 分类 |
| 周末 | 复盘 | 产出：mne-pipeline |

**Week4 配套项目**：MNE 分析 Pipeline

```python
# projects/mne-pipeline/
# 完整 EEG 分析流程

import mne
import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import cross_val_score

class MNEPipeline:
    """MNE EEG 分析 Pipeline"""

    def __init__(self, raw):
        self.raw = raw
        self epochs = None
        self.epochs_picked = None

    def preprocess(self, l_freq=0.5, h_freq=40):
        """预处理：滤波、重参考"""
        self.raw.filter(l_freq, h_freq)
        self.raw.set_eeg_reference('average')

    def create_epochs(self, events, tmin=-0.2, tmax=0.5):
        """创建 Epochs"""
        self.epochs = mne.Epochs(
            self.raw, events,
            tmin=tmin, tmax=tmax,
            baseline=(None, 0),
            preload=True
        )

    def pick_channels(self, picks):
        """选择通道"""
        self.epochs_picked = self.epochs.pick(picks)

    def decode(self, labels, method='lda'):
        """简单解码"""
        X = self.epochs_picked.get_data()
        y = labels

        if method == 'lda':
            clf = LinearDiscriminantAnalysis()
            scores = cross_val_score(clf, X, y, cv=5)
            return scores.mean(), scores.std()

        return None, None
```

---

## Week 5-6：BCI 解码基础 + 可视化

### Week 5：BCI 范式与解码方法

**目标**：理解 SSVEP、MI 等 BCI 范式及解码框架

**每日节奏**：1.5h 理论 + 1.5h 项目 + 1h 复盘

| Day | 理论 | 实战 |
|-----|------|------|
| 1 | BCI 系统架构、信号采集、协议 | 理解 BCI 工作流程 |
| 2 | SSVEP 原理、频域分析、CCA/FBCCA | SSVEP 目标检测 |
| 3 | 运动想象（MI）、ERD/ERS 模式 | MI 特征提取 |
| 4 | 事件相关电位（P300）| P300 分类 |
| 5 | 深度学习在 BCI 中的应用 | PyTorch 简单分类器 |
| 周末 | 复盘 | 产出：bci-decoder |

**Week5 配套项目**：BCI 解码工具

```python
# projects/bci-decoder/
# SSVEP/MI 解码实现

import numpy as np
from scipy.signal import correlate

class SSVEPDetector:
    """SSVEP 检测器"""

    def __init__(self, freqs, fs):
        self.freqs = freqs
        self.fs = fs
        self.n_harmonics = 5

    def generate_template(self, freq):
        """生成参考信号模板"""
        t = np.arange(0, 1, 1/self.fs)
        template = np.zeros((self.n_harmonics, len(t)))
        for h in range(1, self.n_harmonics + 1):
            template[h-1] = np.sin(2 * np.pi * h * freq * t)
        return template

    def cca_score(self, data, freq):
        """计算 CCA 分数"""
        X = data.T  # (n_samples, n_channels)
        Y = self.generate_template(freq)  # (n_harmonics, n_samples)

        # CCA
        C = np.cov(X)
        Cxy = np.dot(X, Y.T)
        Cyy = np.cov(Y)

        try:
            r = np.linalg.solve(Cyy, Cxy.T)
            R = np.cov(np.dot(X, r))
            eigenvalues = np.linalg.eigvalsh(R)
            return np.max(eigenvalues)
        except:
            return 0

    def detect(self, data):
        """检测 SSVEP 目标"""
        scores = []
        for freq in self.freqs:
            score = self.cca_score(data, freq)
            scores.append(score)
        return np.argmax(scores), scores
```

---

### Week 6：GUI 整合与可视化

**目标**：将 Week 2-5 的内容整合到完整 GUI 工具中

**每日节奏**：1h 理论 + 2.5h 项目 + 0.5h 复盘

| Day | 任务 |
|-----|------|
| 1 | EEG 查看器 + 信号处理整合 |
| 2 | 滤波、可视化组件集成 |
| 3 | 事件标记、epoch 提取 UI |
| 4 | 解码结果显示、频谱图 |
| 5 | 数据导出、报告生成 |
| 周末 | 复盘 + 测试 |

**Week6 配套项目**：BCI 数据分析 GUI（完整工具）

```python
# projects/bci-gui/
# 完整 BCI 数据分析 GUI

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import QTimer
import numpy as np
import matplotlib.pyplot as plt
from mne.viz import plot_raw

class BCIGUI(QMainWindow):
    """BCI 数据分析主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BCI Data Analysis Tool")
        self.pipeline = None
        self.setup_ui()

    def setup_ui(self):
        # 主布局
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # 工具栏
        toolbar = self.addToolBar("Main")

        # 左侧：原始数据视图
        # 右侧：处理后数据 + 解码结果
        # 底部：控制面板（滤波参数、epoch 设置等）

    def load_data(self, filepath):
        """加载 EEG 数据"""
        self.pipeline = MNEPipeline(filepath)

    def apply_filter(self):
        """应用滤波"""
        params = self.get_filter_params()
        self.pipeline.filter(**params)

    def extract_epochs(self):
        """提取 Epochs"""
        events = self.get_events()
        self.pipeline.create_epochs(events)

    def decode(self):
        """解码并显示结果"""
        labels = self.get_labels()
        acc, std = self.pipeline.decode(labels)
        self.show_result(acc, std)
```

---

## Week 7-8：Pipeline 工程化 + 项目整合

### Week 7：Pipeline 工程化

**目标**：将科研代码工程化，提高稳定性与复用性

**每日节奏**：1h 理论 + 2h 项目 + 1h 复盘

| Day | 理论 | 实战 |
|-----|------|------|
| 1 | 模块化设计、配置管理 | 重构 Week 1-6 代码 |
| 2 | 日志系统、异常处理 | 添加日志与错误处理 |
| 3 | 单测、集成测试、CI | 编写测试用例 |
| 4 | 文档生成、类型提示 | 添加 docstring 和类型 |
| 5 | 打包、分发、虚拟环境 | 打包为可安装工具 |
| 周末 | 复盘 | 产出：bci-pipeline |

**Week7 配套项目**：工程化 BCI Pipeline

```python
# projects/bci-pipeline/
# 工程化的 BCI 处理 Pipeline

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import logging
from pathlib import Path

@dataclass
class FilterConfig:
    """滤波配置"""
    lowcut: float = 0.5
    highcut: float = 40.0
    notch_freq: Optional[int] = 50
    order: int = 4

@dataclass
class PipelineConfig:
    """Pipeline 配置"""
    filter_params: FilterConfig = field(default_factory=FilterConfig)
    epoch_tmin: float = -0.2
    epoch_tmax: float = 0.5
    baseline: Tuple[Optional[float], Optional[float]] = (None, 0)
    channels: Optional[List[str]] = None

class BCIPipeline:
    """工程化 BCI Pipeline"""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.raw = None

    def load(self, filepath: Path) -> None:
        """加载数据"""
        self.logger.info(f"Loading data from {filepath}")
        self.raw = mne.io.read_raw_xxx(filepath, preload=True)
        self.logger.info(f"Loaded {len(self.raw.ch_names)} channels")

    def preprocess(self) -> None:
        """预处理"""
        self.logger.info("Preprocessing data")
        self.raw.filter(**asdict(self.config.filter_params))

    def create_epochs(self, events) -> None:
        """创建 Epochs"""
        self.epochs = mne.Epochs(
            self.raw, events,
            tmin=self.config.epoch_tmin,
            tmax=self.config.epoch_tmax,
            baseline=self.config.baseline,
            preload=True
        )

    def run(self) -> dict:
        """运行完整 pipeline"""
        results = {}
        for step in ['load', 'preprocess', 'create_epochs', 'decode']:
            try:
                method = getattr(self, step)
                method()
                results[step] = 'success'
            except Exception as e:
                self.logger.error(f"Error in {step}: {e}")
                results[step] = f'failed: {e}'
        return results
```

---

### Week 8：项目整合与面试准备

### 周末目标
整合所有项目，准备面试

**产出**：
1. 完整 BCI 数据分析 GUI 工具（可演示）
2. MNE 分析 Pipeline（代码规范）
3. 信号处理工具库（可复用）

**面试准备**：
- 能讲解完整 BCI 处理流程
- 能现场写 NumPy/SciPy 基础代码
- 能解释滤波、去噪原理

---

## 重要资源

| 资源 | 地址 |
|------|------|
| MNE-Python 文档 | https://mne.tools/stable/ |
| PyQt 教程 | https://www.pythongui.com/ |
| SciPy 信号处理 | https://docs.scipy.org/doc/scipy/tutorial/signal.html |
| BCI 解码论文 | 搜索 SSVEP/MI 相关 IEEE 论文 |

---

## 复盘模板（每周结束填写）

```markdown
## WeekX 复盘
### 完成 vs 计划
-
### 核心问题
-
### 下周调整
-
```