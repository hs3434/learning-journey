# Week 6 Day 16：Qt GUI 架构与 BCI 数据查看器

## 1. 为什么 BCI 工程师必须会 GUI？

BCI 系统不只是一段算法代码，它是一个**实时交互系统**：

```
用户 → 看到刺激 → 产生脑电 → 信号采集 → 实时处理 → 分类结果 → 反馈显示 → 用户
                                                                    ↑
                                                              这就是 GUI
```

没有 GUI 的 BCI 系统：
- 无法实时监控信号质量（电极脱落？干扰太大？）
- 无法可视化分类结果（用户不知道系统是否在"听"）
- 无法调整参数（滤波频段、分类阈值）
- 无法演示给非技术人员看

### 打个比方

- 算法代码 = 汽车发动机
- GUI = 仪表盘 + 方向盘 + 油门刹车

没有仪表盘，发动机再强你也不知道车速、油量、发动机温度。

---

## 2. Qt 核心概念

### 2.1 Qt 是什么？

Qt 是一个跨平台 C++ GUI 框架，Python 绑定有 PyQt6 / PySide6。

```
选择指南：
  PySide6  → Qt 官方绑定，LGPL 协议，商业友好
  PyQt6    → 第三方绑定，GPL 协议，社区成熟
  两者 API 几乎完全相同，学一个就会另一个
```

### 2.2 四大核心机制

#### (1) 事件循环（Event Loop）

```python
app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()  # ← 事件循环：不断监听鼠标/键盘/定时器事件
```

类比：
- 命令行程序 = 一次性执行，跑完就退出
- GUI 程序 = 餐厅服务员，一直在等客人点菜（事件），直到打烊

#### (2) 信号-槽机制（Signal-Slot）

Qt 最核心的设计模式，实现**对象间松耦合通信**：

```python
# 信号发送者不需要知道接收者是谁
button.clicked.connect(self.on_click)        # 点击按钮 → 调用函数
slider.valueChanged.connect(self.update_plot) # 滑块变化 → 更新图表
timer.timeout.connect(self.refresh_data)     # 定时器触发 → 刷新数据
```

类比：
- 信号 = 广播电台（"有人点菜了！"）
- 槽 = 收音机（接到广播后做对应的事）
- connect = 调频（把收音机调到特定频道）

**BCI 场景的信号-槽连接**：

```
采集线程.new_sample  →  信号处理器.filter()
信号处理器.filtered  →  波形显示.update_plot()
分类器.classified   →  结果面板.show_result()
参数面板.changed    →  信号处理器.update_params()
```

#### (3) 布局系统（Layout）

```python
# 水平布局：左右排列
h_layout = QHBoxLayout()
h_layout.addWidget(left_panel)
h_layout.addWidget(right_panel)

# 垂直布局：上下排列
v_layout = QVBoxLayout()
v_layout.addWidget(toolbar)
v_layout.addWidget(plot_area)
v_layout.addWidget(status_bar)

# 嵌套布局：水平里面套垂直
main_layout = QHBoxLayout()
main_layout.addLayout(left_v_layout, stretch=1)
main_layout.addLayout(right_v_layout, stretch=3)
```

类比 CSS Flexbox：
- QHBoxLayout ≈ `display: flex; flex-direction: row`
- QVBoxLayout ≈ `display: flex; flex-direction: column`
- stretch ≈ `flex: 1` / `flex: 3`

#### (4) MVC 分离（Model-View-Controller）

Qt 的设计天然支持 MVC：
- **Model**：数据层（EEG 原始数据、处理结果）
- **View**：显示层（波形图、拓扑图、状态栏）
- **Controller**：逻辑层（信号处理、分类、参数调整）

```python
class EEGModel:
    """数据模型：管理 EEG 数据和处理状态"""
    def __init__(self):
        self.raw_data = None
        self.filtered_data = None
        self.epochs = None
    
    def load_data(self, filepath): ...
    def apply_filter(self, params): ...

class EEGView(QMainWindow):
    """视图：纯显示，不处理业务逻辑"""
    def __init__(self):
        self.plot_widget = EEGPlotWidget()
        self.control_panel = ControlPanel()
    
    def update_plot(self, data): ...
    def show_status(self, message): ...

class EEGController:
    """控制器：连接 Model 和 View"""
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self._connect_signals()
    
    def _connect_signals(self):
        self.view.control_panel.filter_changed.connect(
            self.on_filter_changed
        )
    
    def on_filter_changed(self, params):
        result = self.model.apply_filter(params)
        self.view.update_plot(result)
```

---

## 3. BCI 数据查看器架构

### 3.1 整体布局

```
┌──────────────────────────────────────────────────────┐
│  菜单栏: 文件 | 编辑 | 视图 | 工具 | 帮助              │
├──────────┬───────────────────────────────────────────┤
│          │  工具栏: 加载 | 滤波 | Epoch | 解码 | 设置   │
│  控制    ├───────────────────────────────────────────┤
│  面板    │                                           │
│          │           EEG 波形显示区                    │
│  ────    │        (Matplotlib Canvas)                │
│  滤波    │                                           │
│  参数    ├───────────────────────────────────────────┤
│          │           频谱/拓扑图区                     │
│  ────    │                                           │
│  Epoch   ├───────────────────────────────────────────┤
│  参数    │  结果区: 分类准确率 | ITR | 混淆矩阵         │
│          │                                           │
├──────────┴───────────────────────────────────────────┤
│  状态栏: 数据状态 | 采样率 | 通道数 | 处理进度          │
└──────────────────────────────────────────────────────┘
```

### 3.2 核心组件

| 组件 | Qt 类 | 功能 |
|------|-------|------|
| 主窗口 | QMainWindow | 菜单栏 + 工具栏 + 状态栏 |
| 波形显示 | FigureCanvasQTAgg | Matplotlib 嵌入 Qt |
| 控制面板 | QDockWidget | 可拖拽的参数面板 |
| 数据加载 | QFileDialog | 选择 EEG 数据文件 |
| 进度条 | QProgressDialog | 长时间处理的进度反馈 |
| 实时刷新 | QTimer | 定时触发数据更新 |
| 后台处理 | QThread | 避免 UI 卡顿 |

### 3.3 线程模型 — BCI GUI 的生死线

GUI 卡顿 = 用户体验灾难。BCI 的信号处理通常耗时（滤波、ICA、分类），**绝不能在主线程执行**。

```
主线程 (UI Thread):
  │  接收用户操作 → 更新界面 → 响应信号
  │  ❌ 绝不做耗时计算！
  │
  ├─── 工作线程 1 (DataLoader):
  │      加载 EEG 文件 → 发射 data_loaded 信号
  │
  ├─── 工作线程 2 (Processor):
  │      滤波/ICA → 发射 processing_done 信号
  │
  └─── 工作线程 3 (Classifier):
         解码分类 → 发射 classification_done 信号
```

```python
from PyQt6.QtCore import QThread, pyqtSignal

class ProcessingWorker(QThread):
    """后台处理线程"""
    progress = pyqtSignal(int)      # 进度信号
    finished = pyqtSignal(object)   # 完成信号
    error = pyqtSignal(str)         # 错误信号
    
    def __init__(self, raw, params):
        super().__init__()
        self.raw = raw
        self.params = params
    
    def run(self):
        try:
            # 耗时操作在子线程执行
            result = self.raw.copy().filter(**self.params)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# 使用
worker = ProcessingWorker(raw, {'l_freq': 1, 'h_freq': 40})
worker.progress.connect(progress_bar.setValue)
worker.finished.connect(self.on_processing_done)
worker.error.connect(self.on_error)
worker.start()  # ← 不阻塞主线程！
```

---

## 4. Matplotlib + Qt 集成

### 4.1 嵌入方式

```python
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

class EEGPlotWidget(FigureCanvasQTAgg):
    """Matplotlib 画布嵌入 Qt 窗口"""
    
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(12, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
    
    def plot_eeg(self, data, channels, fs):
        self.ax.clear()
        t = np.arange(data.shape[1]) / fs
        for i, ch in enumerate(channels):
            self.ax.plot(t, data[i] + i * 50, linewidth=0.5)
        self.ax.set_xlabel('Time (s)')
        self.draw()  # ← 触发 Qt 重绘
```

### 4.2 实时数据流更新

```python
class RealtimeEEGPlot:
    """滚动式实时 EEG 显示"""
    
    def __init__(self, canvas, n_channels, fs, window_sec=5):
        self.canvas = canvas
        self.n_channels = n_channels
        self.fs = fs
        self.window_samples = int(window_sec * fs)
        self.buffer = np.zeros((n_channels, self.window_samples))
    
    def update(self, new_sample):
        """每次收到新数据调用"""
        # 滚动缓冲区：丢弃最旧的，追加最新的
        self.buffer = np.roll(self.buffer, -1, axis=1)
        self.buffer[:, -1] = new_sample
        
        # 更新绘图
        self.canvas.ax.clear()
        t = np.arange(self.window_samples) / self.fs
        for ch in range(self.n_channels):
            self.canvas.ax.plot(t, self.buffer[ch] + ch * 50, linewidth=0.3)
        self.canvas.draw_idle()  # ← draw_idle 比 draw 更高效
```

**注意**：`draw_idle()` vs `draw()`
- `draw()` = 立即重绘（可能阻塞）
- `draw_idle()` = 标记为"需要重绘"，等事件循环空闲时再画（推荐）

### 4.3 性能优化技巧

| 问题 | 解决方案 |
|------|---------|
| 画布闪烁 | 用 `blitting` 技术（只更新变化区域） |
| 数据量大 | 降采样显示（显示 1/10 的点，全量数据保留在内存） |
| 更新太频繁 | 用 QTimer 控制 FPS（不超过 30fps） |
| 内存泄漏 | 及时 `ax.clear()`，避免重复创建 Artist 对象 |

---

## 5. 完整 BCI 查看器代码骨架

```python
import sys
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QDockWidget, QSlider, QLabel, QPushButton,
    QFileDialog, QProgressBar, QStatusBar, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class EEGModel:
    """数据模型"""
    def __init__(self):
        self.raw = None
        self.filtered = None
        self.epochs = None
    
    def load(self, filepath):
        import mne
        self.raw = mne.io.read_raw(filepath, preload=True)
        return self.raw
    
    def filter(self, l_freq, h_freq):
        self.filtered = self.raw.copy().filter(l_freq, h_freq)
        return self.filtered
    
    def epoch(self, events, tmin, tmax):
        self.epochs = mne.Epochs(self.filtered, events,
                                  tmin=tmin, tmax=tmax,
                                  baseline=(None, 0), preload=True)
        return self.epochs


class LoadWorker(QThread):
    """数据加载线程"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath
    
    def run(self):
        try:
            import mne
            raw = mne.io.read_raw(self.filepath, preload=True)
            self.finished.emit(raw)
        except Exception as e:
            self.error.emit(str(e))


class FilterWorker(QThread):
    """滤波处理线程"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, raw, l_freq, h_freq):
        super().__init__()
        self.raw = raw
        self.l_freq = l_freq
        self.h_freq = h_freq
    
    def run(self):
        try:
            filtered = self.raw.copy().filter(self.l_freq, self.h_freq)
            self.finished.emit(filtered)
        except Exception as e:
            self.error.emit(str(e))


class EEGPlotWidget(FigureCanvasQTAgg):
    """EEG 波形显示组件"""
    
    def __init__(self):
        self.fig = Figure(figsize=(12, 6), facecolor='#1e1e1e')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#1e1e1e')
        super().__init__(self.fig)
    
    def plot_raw(self, raw):
        data, times = raw[:, :]
        self.ax.clear()
        n_ch = data.shape[0]
        for i in range(n_ch):
            self.ax.plot(times, data[i] + i * 100, linewidth=0.3,
                        color='#00ff88')
        self.ax.set_xlabel('Time (s)', color='white')
        self.ax.tick_params(colors='white')
        self.draw_idle()


class ControlPanel(QDockWidget):
    """参数控制面板"""
    filter_changed = pyqtSignal(float, float)
    
    def __init__(self):
        super().__init__("Controls")
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea |
                            Qt.DockWidgetArea.RightDockWidgetArea)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 滤波参数
        layout.addWidget(QLabel("Low Freq (Hz):"))
        self.l_freq_slider = QSlider(Qt.Orientation.Horizontal)
        self.l_freq_slider.setRange(1, 50)
        self.l_freq_slider.setValue(1)
        layout.addWidget(self.l_freq_slider)
        
        layout.addWidget(QLabel("High Freq (Hz):"))
        self.h_freq_slider = QSlider(Qt.Orientation.Horizontal)
        self.h_freq_slider.setRange(10, 100)
        self.h_freq_slider.setValue(40)
        layout.addWidget(self.h_freq_slider)
        
        # 应用按钮
        self.apply_btn = QPushButton("Apply Filter")
        layout.addWidget(self.apply_btn)
        
        self.setWidget(widget)
        
        # 连接信号
        self.apply_btn.clicked.connect(self._emit_filter_params)
    
    def _emit_filter_params(self):
        self.filter_changed.emit(
            float(self.l_freq_slider.value()),
            float(self.h_freq_slider.value())
        )


class BCIViewer(QMainWindow):
    """BCI 数据查看器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BCI Data Viewer")
        self.setGeometry(100, 100, 1200, 800)
        self.model = EEGModel()
        self._setup_ui()
    
    def _setup_ui(self):
        # 中心区域：波形图
        self.plot_widget = EEGPlotWidget()
        self.setCentralWidget(self.plot_widget)
        
        # 左侧：控制面板
        self.control_panel = ControlPanel()
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea,
                          self.control_panel)
        
        # 状态栏
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready — Load EEG data to begin")
        
        # 连接信号
        self.control_panel.filter_changed.connect(self._on_filter)
    
    def load_data(self, filepath):
        self.status.showMessage(f"Loading {filepath}...")
        self.worker = LoadWorker(filepath)
        self.worker.finished.connect(self._on_data_loaded)
        self.worker.error.connect(self._on_error)
        self.worker.start()
    
    def _on_data_loaded(self, raw):
        self.model.raw = raw
        self.plot_widget.plot_raw(raw)
        self.status.showMessage(
            f"Loaded: {len(raw.ch_names)} channels, "
            f"{raw.times[-1]:.1f}s @ {raw.info['sfreq']}Hz"
        )
    
    def _on_filter(self, l_freq, h_freq):
        if self.model.raw is None:
            return
        self.status.showMessage(f"Filtering {l_freq}-{h_freq} Hz...")
        self.filter_worker = FilterWorker(self.model.raw, l_freq, h_freq)
        self.filter_worker.finished.connect(self._on_filter_done)
        self.filter_worker.error.connect(self._on_error)
        self.filter_worker.start()
    
    def _on_filter_done(self, filtered):
        self.model.filtered = filtered
        self.plot_widget.plot_raw(filtered)
        self.status.showMessage("Filter applied")
    
    def _on_error(self, msg):
        self.status.showMessage(f"Error: {msg}")


# 运行方式（需要显示服务器）：
# app = QApplication(sys.argv)
# viewer = BCIViewer()
# viewer.load_data("sample_eeg.fif")
# viewer.show()
# app.exec()
```

---

## 6. Qt 开发常见坑

| 坑 | 症状 | 解决 |
|----|------|------|
| 主线程做耗时操作 | UI 卡死/无响应 | 用 QThread |
| 跨线程操作 UI | 随机崩溃 | 只用信号-槽更新 UI |
| 忘记 `draw_idle()` | 画布不刷新 | 修改数据后调用 `draw_idle()` |
| 内存泄漏 | 程序越用越慢 | 及时 `ax.clear()`，不要反复 `add_subplot()` |
| 定时器精度差 | 动画不流畅 | QTimer 精度约 10-20ms，不要期望 1ms |
| 信号循环连接 | 无限递归 | 断开旧连接再重连：`signal.disconnect()` |

---

## 7. 本章小结

| 概念 | 要点 | BCI 应用 |
|------|------|---------|
| 事件循环 | GUI 的心脏，持续监听事件 | 实时响应数据流 |
| 信号-槽 | 对象间松耦合通信 | 数据处理→显示更新→用户反馈 |
| MVC | 数据/显示/逻辑分离 | Model=EEG数据, View=波形图, Controller=处理流程 |
| QThread | 后台处理避免 UI 卡顿 | 滤波/ICA/分类在子线程执行 |
| Matplotlib 集成 | FigureCanvasQTAgg 嵌入 Qt | EEG 波形实时显示 |
| 性能优化 | blitting + 降采样 + FPS 控制 | 30fps 流畅实时显示 |

---

## 参考文献

- PyQt6 文档: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- Qt Signal-Slot 机制: https://doc.qt.io/qt-6/signalsandslots.html
- Matplotlib Qt 后端: https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_qt_sgskip.html
- Schirrmeister, R.T. et al. (2017). BrainDecoder: GUI for BCI. *Frontiers in Neuroinformatics*.
