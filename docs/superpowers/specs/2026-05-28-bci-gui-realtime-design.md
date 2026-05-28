# BCI Signal Viewer — 实时交互 GUI 重构设计

**日期**: 2026-05-28
**目标**: 将现有 batch pipeline GUI 重构为双模式（离线分析 + 实时查看）的信号分析系统，满足面试 demo 需求。

## 1. 设计动机

当前 GUI (`bci/gui/__init__.py`) 是单一批量处理模式：Load → Run Pipeline → 显示 accuracy。缺乏实时交互能力，无法展示 BCI 工程系统的核心特性。

岗位要求明确需要：
- 实时监控信号质量（电极脱落、干扰）
- 可视化处理结果（波形、频谱、分类反馈）
- 可调参数（滤波频段、分类阈值）
- 科研 pipeline → 工程系统转化

## 2. 用户交互设计

### 2.1 模式切换

主窗口顶部 **QTabWidget** 两个 Tab：

| Tab | 名称 | 用途 |
|-----|------|------|
| Tab 1 | 离线分析 | 加载文件 → 配置参数 → 一次性 Run → 查看报告 → 导出 |
| Tab 2 | 实时查看 | 加载文件 → 配置参数 → 模拟流播放 → 实时观察波形/频谱/分类 |

每个 Tab **独立持有**全部 Widget 实例（不复用同一个实例，避免切换时状态丢失）。

### 2.2 离线分析 Tab 布局

```
┌─────────────────────────────────────────────────────────────┐
│  [Load] [Run] [Export]              Status: Ready           │
├──────────┬──────────────────────┬───────────────────────────┤
│  参数    │  EEG 波形总览        │  解码结果                 │
│  Lowcut  │  (全通道 × 全时长)   │  Accuracy: 85.3%          │
│  Highcut │                      │  混淆矩阵                 │
│  Method  │                      │  每折 CV 分数             │
│  CV fold │                      │                           │
│  [Reset] │                      │                           │
├──────────┴──────────────────────┴───────────────────────────┤
│  频谱图  │  拓扑地形图  │  处理日志                          │
├─────────────────────────────────────────────────────────────┤
│  状态栏: ch=64 | sfreq=256Hz | filter=1-40 | method=LDA     │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 实时查看 Tab 布局

```
┌─────────────────────────────────────────────────────────────┐
│  [▶ Start] [⏸ Pause] [⏹ Stop]   Speed: [════] [1.00×]  ⟳ Loop │
│                                              滑块   输入框    │
├──────────┬──────────────────────────────┬───────────────────┤
│  实时参数│  滚动 EEG 波形 (5s 窗口)     │  实时频谱 + 分类  │
│  Lowcut  │  ~~~~~~~~~~~~~               │  ▲ PSD            │
│  Highcut │  ~~~~~~~~~~~~~ ← 持续滚动    │  预测: LEFT ←     │
│  Notch   │  ~~~~~~~~~~~~~               │                   │
│  通道选择 │                              │                   │
├──────────┴──────────────────────────────┴───────────────────┤
│  通道列表  │  事件标记（刺激/响应时间线）  │  实时日志       │
├─────────────────────────────────────────────────────────────┤
│  状态栏: Source=file.edf | chunk=100ms | causal | fps=28    │
└─────────────────────────────────────────────────────────────┘
```

倍速控制：**无极滑杆 (0.25x ~ 100x) + 旁边 QDoubleSpinBox 输入框**，拖动滑杆自动同步输入框的值，手动输入也同步滑杆。

### 2.4 StreamSource 播放行为

| 特性 | 规格 |
|------|------|
| 数据源 | 从已加载文件分块读取（chunk_duration 默认 100ms） |
| 速度控制 | 无极滑杆 0.25x ~ 100x + 数值输入框，1x = 原始采样率 |
| EOF 行为 | 默认停止 + 工具栏 "⟳ Loop" 复选框，勾选后循环播放 |
| Seek | 暂停时拖动进度条跳转到任意位置 |
| 播放控制 | Start / Pause / Stop 按钮 |

## 3. 模块架构

### 3.1 新增/变更模块一览

```
bci/
├── source/                         # 新增
│   ├── __init__.py
│   ├── base.py                     #   DataSource 抽象基类
│   ├── file_source.py              #   FileSource
│   └── stream_source.py            #   StreamSource (QObject)
├── processor/                      # 新增
│   ├── __init__.py
│   ├── offline.py                  #   OfflineProcessor
│   └── online.py                   #   OnlineProcessor
├── decoder/                        # 变更（新增 predict 方法）
│   └── __init__.py
├── gui/                            # 重构
│   ├── __init__.py
│   ├── main_window.py              #   BCIMainWindow (QTabWidget)
│   ├── batch_tab.py                #   BatchTab (QWidget)
│   ├── stream_tab.py               #   StreamTab (QWidget)
│   ├── worker.py                   #   BatchWorker + StreamWorker
│   └── widgets/                    #
│       ├── __init__.py             #
│       ├── waveform.py             #   EEGWaveformWidget
│       ├── spectrum.py             #   SpectrumWidget
│       ├── topomap.py              #   TopomapWidget
│       └── result_panel.py         #   ResultPanel
├── pipeline/                       # 不动
├── loader/                         # 不动
├── epocher/                        # 不动
├── config/                         # 不动（可能新增 StreamConfig）
├── tests/                          # 新增 source/processor/widgets 测试
├── main.py                         # 不动
└── __init__.py                     # 不动
```

### 3.2 新增模块详细设计

#### 3.2.1 `source/` — 数据源抽象层

```python
class DataSource(ABC):
    """统一数据源接口"""

    @abstractmethod
    def open(self) -> None: ...

    @abstractmethod
    def read_chunk(self, n_samples: int) -> np.ndarray | None:
        """读取 n_samples 个样本，EOF 返回 None"""

    @abstractmethod
    def seek(self, sample_idx: int) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @property
    @abstractmethod
    def sfreq(self) -> float: ...

    @property
    @abstractmethod
    def n_channels(self) -> int: ...

    @property
    def total_samples(self) -> int | None:
        """batch 模式有值，stream 可为 None"""
        return None

    @property
    def is_stream(self) -> bool:
        return False
```

**FileSource**：封装 mne.io.Raw，全量加载，可任意 seek。`read_chunk(n)` 不移动内部指针（batch 场景不需要流式语义）。

**StreamSource(QObject)**：
- 初始化时预加载文件 + 获取 data 数组
- QTimer 驱动，按 speed 倍率计算实际推送间隔
- 信号 `chunk_ready(np.ndarray)` 发射新数据块
- 信号 `finished()` 文件播放完毕
- 信号 `progress(int)` 当前播放位置百分比
- `read_chunk(n)` 直接从内部指针读取，供非 Qt 调用（如 CLI 测试）
- 支持 `set_speed(float)` 动态调速
- 支持 `set_loop(bool)` 控制是否循环
- `reset()` 重置到文件开头

#### 3.2.2 `processor/` — 离线/在线处理器

```python
class OfflineProcessor:
    """离线批处理：追求精度"""
    def bandpass(self, data, sfreq, l_freq, h_freq) -> np.ndarray:
        # scipy.signal.filtfilt (前向+反向，零相位)
    def notch(self, data, sfreq, freqs) -> np.ndarray:
        # filtfilt 陷波
    def apply_ica(self, data) -> np.ndarray:
        # 全量 ICA
    def normalize(self, data) -> np.ndarray:
        # 全数据集 mean/std

class OnlineProcessor:
    """在线实时处理：严格因果，低延迟"""
    def __init__(self, sfreq, n_channels):
        self._buffer = ...  # 维持内部状态（滤波器状态、滑动窗口统计）

    def bandpass(self, chunk, l_freq, h_freq) -> np.ndarray:
        # scipy.signal.lfilter (仅前向，因果)，维持滤波器 zi 状态
    def notch(self, chunk, freqs) -> np.ndarray:
        # lfilter 陷波，维持状态
    def remove_artifact(self, chunk, threshold) -> np.ndarray:
        # 阈值剔除（不能 peek 未来数据）
    def normalize(self, chunk) -> np.ndarray:
        # 滑动窗口指数加权均值/方差
```

#### 3.2.3 `gui/widgets/` — 可视化组件

每个 Widget 是独立的 `QWidget` 子类，内嵌 `FigureCanvasQTAgg`，接收数据、更新绘图。

| Widget | 接口 | 功能 |
|--------|------|------|
| `EEGWaveformWidget` | `update(data, sfreq, channels)` — 更新波形 | batch 模式全量绘制；stream 模式 scroll buffer + draw_idle() |
| `SpectrumWidget` | `update(data, sfreq)` — 更新 PSD | 显示当前窗口的功率谱密度 |
| `TopomapWidget` | `update(data, positions)` — 更新拓扑图 | 头皮电位分布（需要 channel positions） |
| `ResultPanel` | `update(result: DecodeResult | str)` | batch 模式显示 accuracy + 混淆矩阵；stream 模式显示实时预测标签 |

#### 3.2.4 `gui/worker.py` — 线程模型

```python
class BatchWorker(QThread):
    """离线分析后台线程（现有 Worker 的增强版，修复 hardcode filepath）"""
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(PipelineResult)
    error = pyqtSignal(str)

class StreamWorker(QThread):
    """实时流处理线程：连接 StreamSource → OnlineProcessor → GUI"""
    chunk_processed = pyqtSignal(np.ndarray)  # 处理后的 chunk 给波形刷新
    spectrum_updated = pyqtSignal(np.ndarray, np.ndarray)  # freqs, psd
    classification = pyqtSignal(str)  # 实时分类结果
    error = pyqtSignal(str)
```

### 3.3 复用关系

```
FileSource ──→ OfflineProcessor ──→ GUI Widgets (Batch 实例)
StreamSource ─→ OnlineProcessor ──→ GUI Widgets (Stream 实例)

共享：WaveformWidget / SpectrumWidget / TopomapWidget 类定义
不共享：Widget 实例、Processor 实例
```

### 3.4 已知 Bug 修复

- **`gui/__init__.py` 第 146 行 hardcode `"data.edf"`**：`on_run()` 中硬编码了文件路径，未使用 `on_load()` 选择的文件。重构时 `BatchWorker` 接收 `filepath` 参数解决。

### 3.5 不变模块

以下模块保持不变，不纳入本次重构范围：
- `loader/` — 数据加载
- `epocher/` — 事件检测和 epoch 提取
- `pipeline/` — 离线 batch 编排（BCIPipeline），Stream 模式不走 pipeline
- `config/` — 配置 dataclass，不新增 StreamConfig（Stream 模式直接使用现有 FilterConfig）
- `main.py` — CLI/GUI 入口点

## 4. 数据流

### 4.1 批量离线

```
[Load btn] → QFileDialog → FileSource.open(file)
→ 用户调参 (filter params)
→ [Run btn] → BatchWorker.start()
  → BCIPipeline.run(file)
    → Loader → Preprocessor(filtfilt+ICA) → Epocher → Decoder(CV)
  → finished(PipelineResult)
→ WaveformWidget.update(data) / ResultPanel.update(result)
→ [Export btn] → pipeline.save_results()
```

### 4.2 实时流

```
[Load btn] → QFileDialog → StreamSource.open(file)
→ 用户调参 (filter/speed/loop)
→ [▶ Start]
  → StreamSource 内部 QTimer.start()
  → QTimer.timeout → chunk_ready(np.ndarray) 信号发射原始 chunk
  → OnlineProcessor 接收 chunk:
      → lfilter(l_freq, h_freq) — 因果滤波，维持 zi 状态
      → notch(50Hz) — 维持状态
      → 阈值剔除 — 基于当前窗口的 amplitude 阈值
      → 滑动窗口归一化
  → 处理后 chunk 返回给 StreamTab:
      → EEGWaveformWidget.update(chunk) — 滚动 buffer + draw_idle()
      → SpectrumWidget.update(chunk) — 当前窗口 PSD
      → ResultPanel (可选分类预测标签)
→ [⏸ Pause] → QTimer.stop(), StreamSource 保持内部指针，OnlineProcessor 保持滤波器状态
→ [⏹ Stop] → QTimer.stop(), StreamSource.reset(), OnlineProcessor.reset_state()
→ Seek 时 → StreamSource.seek(pos) + OnlineProcessor.reset_state() + Widget 清空 buffer
```

## 5. 错误处理

- **PyQt6 不可用**：保留现有 `GUI_AVAILABLE` 检测，import 失败时 graceful degrade，CLI 模式不受影响
- **文件加载失败**：QMessageBox 弹窗提示，不崩溃
- **处理线程异常**：worker.error 信号由主窗口捕获，状态栏显示错误信息
- **StreamSource EOF**：正常停止 + 状态栏提示，不抛异常
- **无效参数（l_freq > h_freq）**：参数面板内联校验，Run 按钮在参数无效时灰色不可点击

## 6. 测试策略

- **source/ 单测**：FileSource 读取测试、StreamSource 分块/seek/speed 测试
- **processor/ 单测**：filtfilt vs lfilter 对比、滑动窗口统计验证
- **widgets/ 单测**：用 pytest-qt 测试 Widget 创建和数据更新
- **集成测试**：完整 batch 流、完整 stream 流（用模拟数据）
- **保留现有测试**：`bci/tests/` 不动，新增文件独立

## 7. 实现优先级

| 阶段 | 内容 | 理由 |
|------|------|------|
| 1 | `source/` (base + FileSource + StreamSource) | 数据源是整个系统的地基 |
| 2 | `processor/` (OfflineProcessor + OnlineProcessor) | 处理逻辑独立，可脱离 GUI 测试 |
| 3 | `gui/widgets/` (4 个可视化组件) | 纯视图层，不依赖 pipeline |
| 4 | `gui/worker.py` (BatchWorker + StreamWorker) | 线程模型，连接 source/processor/widgets |
| 5 | `gui/batch_tab.py` + `gui/stream_tab.py` | 面板组装 |
| 6 | `gui/main_window.py` | 主窗口 Tab 组装 |
| 7 | 测试 + 文档 | 覆盖所有新模块 |
