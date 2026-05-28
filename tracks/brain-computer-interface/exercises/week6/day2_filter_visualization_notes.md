# Week 6 Day 17：滤波与可视化组件集成

## 1. 今天的目标

Day 16 搭了 GUI 架构骨架（信号-槽、MVC、线程模型），今天要把 **信号处理核心** 和 **可视化组件** 真正集成进去：

```
Day 16 架构（"骨架"）         Day 17 集成（"装上发动机和仪表盘"）
┌──────────────┐              ┌──────────────────────────────────┐
│  空壳 GUI     │    ──→      │  滤波引擎 + PSD + 时频图 +       │
│  按钮无功能    │              │  交互式参数调节 + 实时更新        │
└──────────────┘              └──────────────────────────────────┘
```

---

## 2. 滤波组件集成

### 2.1 从 Script 到 Component 的关键变化

Week 3 的滤波是脚本式：

```python
# Week 3 风格：一次性脚本
data = np.loadtxt('eeg.csv')
filtered = butter_bandpass(data, 1, 40, fs=256)
plt.plot(filtered)
plt.show()
```

GUI 中需要变成**组件化**：

```python
# Week 6 风格：可复用组件
class FilterEngine:
    """滤波引擎：封装所有滤波逻辑，GUI 通过它交互"""
    
    def __init__(self):
        self.raw = None           # MNE Raw 对象
        self.filtered = None      # 滤波后数据
        self.notch_applied = False
        self.filter_params = FilterParams()  # 当前参数
    
    def set_data(self, raw):
        """设置待处理数据"""
        self.raw = raw
        self.filtered = None
    
    def apply_bandpass(self, l_freq, h_freq, order=4):
        """带通滤波"""
        self.filter_params.l_freq = l_freq
        self.filter_params.h_freq = h_freq
        self.filtered = self.raw.copy().filter(
            l_freq, h_freq, method='fir', fir_design='firwin'
        )
        return self.filtered
    
    def apply_notch(self, freqs=(50, 100), notch_widths=1):
        """Notch 滤波（去工频干扰）"""
        self.filtered = self.raw.copy().notch_filter(
            freqs, notch_widths=notch_widths
        )
        self.notch_applied = True
        return self.filtered
    
    def get_psd(self, fmin=0.5, fmax=100):
        """获取功率谱密度"""
        src = self.filtered if self.filtered else self.raw
        return src.compute_psd(fmin=fmin, fmax=fmax)
```

**核心区别**：

| 脚本式 | 组件式 |
|--------|--------|
| 数据是函数参数 | 数据是对象属性 |
| 参数硬编码 | 参数可动态修改 |
| 结果直接画图 | 结果返回给 View 层 |
| 无状态 | 有状态（记住上次操作） |

### 2.2 打个比方

- 脚本式 = 手动挡汽车：每次换挡都要自己操作离合
- 组件式 = 自动挡：你只管踩油门（调参数），内部自动处理

### 2.3 滤波参数的数据类

```python
from dataclasses import dataclass
from typing import Optional, Tuple, List

@dataclass
class FilterParams:
    """滤波参数配置"""
    l_freq: float = 1.0           # 高通截止频率
    h_freq: float = 40.0          # 低通截止频率
    notch_freqs: Tuple[float, ...] = (50.0, 100.0)  # 工频干扰频率
    notch_widths: float = 1.0     # Notch 滤波宽度
    method: str = 'fir'           # 'fir' 或 'iir'
    order: int = 4                # IIR 滤波阶数
    
    @property
    def is_valid(self):
        """参数合法性检查"""
        return (0 < self.l_freq < self.h_freq and 
                self.h_freq <= 500)  # Nyquist 以下
```

**为什么用 dataclass？**
1. **类型安全**：IDE 能自动补全，错误参数编译期发现
2. **默认值**：新用户不调参也能用合理默认值
3. **序列化**：可直接保存为 JSON，下次启动恢复参数

---

## 3. 可视化组件集成

### 3.1 三层可视化架构

```
┌─────────────────────────────────────────┐
│          BCI Visualization Layer         │
├─────────────────────────────────────────┤
│  Layer 3: Dashboard (主窗口)              │
│  ┌──时域图──┐ ┌──频域图──┐ ┌──拓扑图──┐  │
│  │ EEG raw  │ │ PSD plot │ │ Topomap  │  │
│  └──────────┘ └──────────┘ └──────────┘  │
├─────────────────────────────────────────┤
│  Layer 2: Plot Widgets (可复用组件)       │
│  EEGPlotWidget  PSDWidget  TopoWidget    │
├─────────────────────────────────────────┤
│  Layer 1: Canvas (Matplotlib + Qt)       │
│  FigureCanvasQTAgg → Figure → Axes      │
└─────────────────────────────────────────┘
```

### 3.2 各组件的职责

| 组件 | 输入 | 输出 | 更新触发 |
|------|------|------|----------|
| EEGPlotWidget | Raw/filtered data | 时域波形图 | 数据加载、滤波 |
| PSDWidget | Raw/filtered data | 功率谱密度 | 数据加载、滤波 |
| TopoWidget | Evoked + info | 头皮电位分布图 | Epoch 平均后 |
| TFRWidget | Epochs | 时频热力图 | Epoch 创建后 |

### 3.3 关键设计模式：观察者模式

当用户调整滤波参数时，**所有相关图表都要更新**。用 Qt 信号-槽实现观察者：

```python
class VisualizationManager:
    """可视化管理器：协调所有图表组件的更新"""
    
    data_updated = pyqtSignal(object)  # 数据变化时广播
    
    def __init__(self):
        self.eeg_plot = EEGPlotWidget()
        self.psd_plot = PSDWidget()
        self.topo_plot = TopoWidget()
        
        # 所有组件监听同一信号
        self.data_updated.connect(self.eeg_plot.on_data_changed)
        self.data_updated.connect(self.psd_plot.on_data_changed)
        self.data_updated.connect(self.topo_plot.on_data_changed)
    
    def update_all(self, data):
        """一次信号发射，所有图表同步更新"""
        self.data_updated.emit(data)
```

类比：
- 观察者模式 = 微信群通知：管理员发一条消息，所有群成员都能收到
- 没有观察者 = 打电话逐个通知：漏一个就没人更新

### 3.4 PSD 组件实现

```python
class PSDWidget(FigureCanvasQTAgg):
    """功率谱密度显示组件"""
    
    def __init__(self):
        self.fig = Figure(figsize=(8, 4))
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
    
    def on_data_changed(self, raw):
        """数据更新回调"""
        self.plot_psd(raw)
    
    def plot_psd(self, raw, fmin=0.5, fmax=100):
        self.ax.clear()
        psd = raw.compute_psd(fmin=fmin, fmax=fmax)
        psd.plot(axes=self.ax, show=False)
        self.ax.set_title('Power Spectral Density')
        self.draw_idle()
```

---

## 4. 交互式参数调节

### 4.1 实时预览 vs 应用后更新

两种交互策略：

| 策略 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 实时预览 | 所见即所得 | 每次滑动都计算，可能卡顿 | 轻量操作（缩放、选通道） |
| 应用后更新 | 不卡，可控 | 需要点"应用"按钮 | 重计算（滤波、ICA） |

**BCI GUI 推荐：混合策略**
- 滑块调参时：只更新**参数显示文本**（不重计算）
- 松开滑块/点应用：才真正**执行滤波 + 更新图表**

```python
class FilterControlPanel(QWidget):
    """滤波参数面板（混合策略）"""
    
    filter_requested = pyqtSignal(dict)  # 用户点"应用"才发射
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # 低频滑块 — 滑动时只更新标签
        self.l_freq_label = QLabel("Low: 1.0 Hz")
        self.l_freq_slider = QSlider(Qt.Orientation.Horizontal)
        self.l_freq_slider.setRange(1, 50)
        self.l_freq_slider.setValue(1)
        self.l_freq_slider.valueChanged.connect(
            lambda v: self.l_freq_label.setText(f"Low: {v} Hz")
        )
        
        # 高频滑块
        self.h_freq_label = QLabel("High: 40.0 Hz")
        self.h_freq_slider = QSlider(Qt.Orientation.Horizontal)
        self.h_freq_slider.setRange(10, 100)
        self.h_freq_slider.setValue(40)
        self.h_freq_slider.valueChanged.connect(
            lambda v: self.h_freq_label.setText(f"High: {v} Hz")
        )
        
        # "应用"按钮 — 点击才真正触发滤波
        apply_btn = QPushButton("Apply Filter")
        apply_btn.clicked.connect(self._on_apply)
        
        layout.addWidget(self.l_freq_label)
        layout.addWidget(self.l_freq_slider)
        layout.addWidget(self.h_freq_label)
        layout.addWidget(self.h_freq_slider)
        layout.addWidget(apply_btn)
    
    def _on_apply(self):
        self.filter_requested.emit({
            'l_freq': float(self.l_freq_slider.value()),
            'h_freq': float(self.h_freq_slider.value()),
        })
```

### 4.2 Notch 滤波开关

工频干扰（50Hz/60Hz）是固定频率，适合做开关而非滑块：

```python
# Checkbox 更直观
self.notch_check = QCheckBox("Remove 50Hz powerline")
self.notch_check.stateChanged.connect(self._on_notch_toggle)
```

---

## 5. 数据流管道

### 5.1 完整处理链

```
Raw Data → [Bandpass Filter] → [Notch Filter] → Filtered Data
    │                                                  │
    ├──→ EEG Plot (原始)                    ──→ EEG Plot (滤波后)
    └──→ PSD Plot (原始频谱)                 ──→ PSD Plot (滤波后频谱)
                                                    │
                                            [Epoch Extraction]
                                                    │
                                                    └──→ Topomap / TFR
```

### 5.2 管道状态机

```python
from enum import Enum, auto

class PipelineState(Enum):
    """处理管道状态"""
    EMPTY = auto()        # 无数据
    LOADED = auto()       # 已加载原始数据
    FILTERED = auto()     # 已滤波
    EPOCHED = auto()      # 已提取 Epoch
    DECODED = auto()      # 已解码
```

每个状态决定了哪些操作可用、哪些图表可显示：

```python
def update_ui_state(self):
    """根据管道状态启用/禁用控件"""
    state = self.pipeline.state
    
    self.load_btn.setEnabled(state != PipelineState.EMPTY or True)  # 始终可加载
    self.filter_btn.setEnabled(state.value >= PipelineState.LOADED.value)
    self.epoch_btn.setEnabled(state.value >= PipelineState.FILTERED.value)
    self.decode_btn.setEnabled(state.value >= PipelineState.EPOCHED.value)
```

类比：
- 状态机 = 游戏关卡：你必须先通过第一关（加载数据），才能进入第二关（滤波）
- 跳关 = 没有数据就点滤波 → 按钮灰色不可点击

---

## 6. 性能优化要点

### 6.1 降采样显示

EEG 数据可能有几十万个采样点，全部绘制极慢：

```python
def plot_eeg_downsampled(self, data, fs, target_points=2000):
    """降采样后绘制"""
    n_samples = data.shape[1]
    step = max(1, n_samples // target_points)
    data_ds = data[:, ::step]
    t_ds = np.arange(data_ds.shape[1]) / (fs / step)
    
    for i in range(data_ds.shape[0]):
        self.ax.plot(t_ds, data_ds[i] + i * offset, linewidth=0.3)
```

- 原始 600kHz × 60ch = 3600 万个点 → 降采样到 2000 × 60 = 12 万个点
- 渲染时间从 **5 秒** 降到 **0.1 秒**
- **数据不变**，只是显示密度降低（就像 Google Maps 缩小后不显示每条小路）

### 6.2 信号-槽防抖（Debounce）

用户快速拖动滑块时，不要每个中间值都触发更新：

```python
from PyQt6.QtCore import QTimer

class DebouncedSignal:
    """防抖：停止操作 300ms 后才发射信号"""
    
    def __init__(self, timeout=300):
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(timeout)
    
    def trigger(self, callback):
        """重置计时器"""
        self.timer.stop()
        self.timer.timeout.connect(callback)
        self.timer.start()
```

### 6.3 缓存策略

```python
class FilterCache:
    """滤波结果缓存：相同参数不重复计算"""
    
    def __init__(self):
        self._cache = {}
    
    def get_or_compute(self, raw, params):
        key = (id(raw), params.l_freq, params.h_freq, params.method)
        if key not in self._cache:
            self._cache[key] = raw.copy().filter(params.l_freq, params.h_freq)
        return self._cache[key]
```

---

## 7. 总结

| 概念 | 核心要点 |
|------|----------|
| 组件化滤波 | 数据类封装参数，引擎类封装逻辑 |
| 三层可视化 | Canvas → Widget → Dashboard |
| 观察者模式 | 一个信号广播，多个组件响应 |
| 混合交互 | 滑块只更新标签，点"应用"才计算 |
| 状态机 | 处理管道进度决定 UI 可用性 |
| 降采样显示 | 渲染快 50 倍，视觉无损 |
| 防抖 | 避免中间值触发无效更新 |

**下一步（Day 18）**：事件标记与 Epoch 提取 UI — 让用户能在波形上标记事件，交互式提取 Epoch。
