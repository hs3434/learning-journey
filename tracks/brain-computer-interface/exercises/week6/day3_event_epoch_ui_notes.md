# Week 6 Day 18：事件标记与 Epoch 提取 UI

## 1. 为什么事件标记是 BCI 的关键环节？

BCI 系统的核心逻辑：**刺激 → 脑电响应 → 提取响应片段 → 分类**。

没有事件标记，你有的只是一段连续脑电——不知道哪段是"左手动"，哪段是"右手动"。

```
连续 EEG 数据：~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    ↑        ↑        ↑        ↑
                 事件1     事件2     事件3     事件4
                 "左手"   "右手"   "左手"   "右手"

切分后（Epochs）：
  Epoch 1: [---"左手"响应---]
  Epoch 2: [---"右手"响应---]
  Epoch 3: [---"左手"响应---]
  Epoch 4: [---"右手"响应---]
```

类比：
- 事件标记 = 书签：在一大段文字中标记关键段落的位置
- 没有 bookmark = 一整本书从头翻到尾，不知道哪段重要

---

## 2. MNE 事件系统回顾

### 2.1 Events 数组

MNE 用 N×3 的 numpy 数组表示事件：

```python
import mne
# events[i] = [sample_index, 0, event_id]
# sample_index = 事件发生的采样点
# 0 = 保留字段（MNE 规范）
# event_id = 事件类型编号

events = np.array([
    [14400, 0, 1],   # 采样点14400处，事件类型1（左手）
    [28800, 0, 2],   # 采样点28800处，事件类型2（右手）
    [43200, 0, 1],   # 采样点43200处，事件类型1（左手）
])
```

### 2.2 Event Dict

```python
event_id = {
    'left_hand': 1,
    'right_hand': 2,
    'foot': 3,
}
```

### 2.3 从 Raw 提取事件

```python
# 方法1：从 trigger 通道自动检测
events = mne.find_events(raw, stim_channel='STI 014')

# 方法2：手动创建
events = mne.make_fixed_length_events(raw, duration=2.0, id=1)

# 方法3：从注释创建
events = mne.events_from_annotations(raw)
```

---

## 3. GUI 中的交互式事件标记

### 3.1 事件标记的三种模式

| 模式 | 交互方式 | 适用场景 |
|------|----------|----------|
| 自动检测 | 从 trigger 通道提取 | 实验室标准采集 |
| 手动点击 | 在波形上点击标记 | 回顾性分析、无 trigger 数据 |
| 批量导入 | 从 CSV/TSV 导入 | 外部标记文件 |

### 3.2 手动标记的 Qt 实现

```python
class EventMarkerWidget(FigureCanvasQTAgg):
    """支持点击标记事件的 EEG 波形组件"""
    
    event_added = pyqtSignal(int, int)  # (sample_index, event_id)
    
    def __init__(self):
        self.fig = Figure(figsize=(12, 6))
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        
        # 事件列表
        self.events = []
        self.current_event_id = 1  # 当前标记类型
        
        # 连接鼠标事件
        self.mpl_connect('button_press_event', self._on_click)
    
    def _on_click(self, event):
        """用户点击波形时添加事件标记"""
        if event.inaxes != self.ax:
            return
        if event.button != 1:  # 只响应左键
            return
        
        # 将点击的 x 坐标（时间）转为采样点
        sample = int(event.xdata * self.fs)
        self.events.append([sample, 0, self.current_event_id])
        
        # 在图上画标记线
        self.ax.axvline(event.xdata, color='red', linewidth=1.5, alpha=0.7)
        self.ax.text(event.xdata, self.ax.get_ylim()[1], 
                     f'E{self.current_event_id}',
                     ha='center', va='bottom', fontsize=8, color='red')
        self.draw_idle()
        
        # 发射信号
        self.event_added.emit(sample, self.current_event_id)
```

### 3.3 事件类型选择器

```python
class EventTypeSelector(QWidget):
    """事件类型选择面板"""
    
    event_type_changed = pyqtSignal(int)
    
    def __init__(self, event_dict):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.buttons = {}
        for name, eid in event_dict.items():
            btn = QPushButton(f"{name} (ID={eid})")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, id=eid: self._select(id))
            layout.addWidget(btn)
            self.buttons[eid] = btn
        
        # 默认选中第一个
        first_id = list(event_dict.values())[0]
        self.buttons[first_id].setChecked(True)
    
    def _select(self, event_id):
        for eid, btn in self.buttons.items():
            btn.setChecked(eid == event_id)
        self.event_type_changed.emit(event_id)
```

---

## 4. Epoch 提取 UI

### 4.1 提取参数面板

```python
class EpochControlPanel(QDockWidget):
    """Epoch 提取控制面板"""
    
    epochs_requested = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__("Epoch Settings")
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 时间窗口
        layout.addWidget(QLabel("tmin (s):"))
        self.tmin_spin = QDoubleSpinBox()
        self.tmin_spin.setRange(-5.0, 0.0)
        self.tmin_spin.setValue(-0.2)
        self.tmin_spin.setSingleStep(0.1)
        layout.addWidget(self.tmin_spin)
        
        layout.addWidget(QLabel("tmax (s):"))
        self.tmax_spin = QDoubleSpinBox()
        self.tmax_spin.setRange(0.0, 10.0)
        self.tmax_spin.setValue(0.5)
        self.tmax_spin.setSingleStep(0.1)
        layout.addWidget(self.tmax_spin)
        
        # Baseline
        layout.addWidget(QLabel("Baseline:"))
        self.baseline_check = QCheckBox("Apply baseline correction")
        self.baseline_check.setChecked(True)
        layout.addWidget(self.baseline_check)
        
        # 提取按钮
        self.extract_btn = QPushButton("Extract Epochs")
        self.extract_btn.clicked.connect(self._emit_params)
        layout.addWidget(self.extract_btn)
        
        self.setWidget(widget)
    
    def _emit_params(self):
        self.epochs_requested.emit({
            'tmin': self.tmin_spin.value(),
            'tmax': self.tmax_spin.value(),
            'baseline': (None, 0) if self.baseline_check.isChecked() else None,
        })
```

### 4.2 Epoch 可视化

```python
class EpochPlotWidget(FigureCanvasQTAgg):
    """Epoch 显示组件：ERP 叠加 + 平均"""
    
    def __init__(self):
        self.fig = Figure(figsize=(12, 6))
        super().__init__(self.fig)
    
    def plot_epochs(self, epochs, channel='Cz'):
        """叠加显示所有 Epoch + 平均 ERP"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        data = epochs.get_data()  # (n_epochs, n_channels, n_times)
        ch_idx = epochs.ch_names.index(channel)
        times = epochs.times
        
        # 单个 Epoch（灰色半透明）
        for i in range(data.shape[0]):
            ax.plot(times, data[i, ch_idx], color='gray', 
                    alpha=0.2, linewidth=0.3)
        
        # 平均 ERP（粗红线）
        avg = data[:, ch_idx, :].mean(axis=0)
        ax.plot(times, avg, color='red', linewidth=2, label=f'ERP ({channel})')
        
        ax.axvline(0, color='black', linestyle='--', alpha=0.5)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Amplitude (uV)')
        ax.set_title(f'Epochs: {data.shape[0]} trials, Channel: {channel}')
        ax.legend()
        self.draw_idle()
```

---

## 5. 数据流：从标记到 Epoch

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  Event       │     │  Epoch       │     │  Epoch         │
│  Marking     │────→│  Extraction  │────→│  Visualization │
│  (手动/自动)  │     │  (MNE)       │     │  (叠加+平均)    │
└─────────────┘     └──────────────┘     └────────────────┘
      │                     │
      ▼                     ▼
  events array         epochs object
  (N×3 numpy)          (MNE Epochs)
```

### 5.1 信号-槽连接

```python
# 事件标记 → 自动更新事件计数
self.event_marker.event_added.connect(self._update_event_count)

# 提取请求 → 后台线程处理
self.epoch_panel.epochs_requested.connect(self._start_epoch_extraction)

# 提取完成 → 更新所有可视化
self.epoch_worker.finished.connect(self._on_epochs_ready)
self.epoch_worker.finished.connect(self.erp_plot.plot_epochs)
self.epoch_worker.finished.connect(self.topo_plot.update_topomap)
```

---

## 6. Baseline 校正的意义

### 6.1 为什么需要 Baseline？

Epoch 的 tmin 通常为负值（如 -0.2s），这段是刺激前的"基线"。

Baseline 校正 = **减去基线均值**，让每个 Epoch 都从"0"开始：

$$x_{corrected}(t) = x(t) - \bar{x}_{baseline}$$

其中 $\bar{x}_{baseline}$ 是刺激前时间窗的均值。

### 6.2 打个比方

- 没有 baseline = 考试不扣基础分，每个人起点不同（有人提前学了，有人没有）
- 有 baseline = 每个人从同一起跑线出发，只看"变化量"

### 6.3 GUI 中的 Baseline 控制

```python
# 通常 baseline = (None, 0) 即刺激前整段
# 也可以自定义：(tmin, 0) 或 (-0.1, 0)

# 某些场景不做 baseline：
# - SSVEP（稳态响应，不关心瞬态变化）
# - 频域分析（功率谱本身是相对值）
```

---

## 7. 拒绝坏 Epoch（Artifact Rejection）

### 7.1 峰值阈值法

```python
# 振幅超过 ±100uV 的 epoch 自动排除
epochs = mne.Epochs(raw, events, event_id,
                    tmin=-0.2, tmax=0.5,
                    baseline=(None, 0),
                    reject=dict(eeg=100e-6),  # 100 uV
                    preload=True)
```

### 7.2 GUI 交互式拒绝

```python
class EpochRejectWidget(QWidget):
    """交互式坏 Epoch 拒绝"""
    
    def __init__(self):
        self.reject_threshold = 100e-6  # 100 uV
        self.rejected_indices = set()
    
    def auto_detect(self, epochs):
        """自动检测超出阈值的 epoch"""
        data = epochs.get_data()
        peak_to_peak = data.max(axis=2) - data.min(axis=2)
        bad = np.any(peak_to_peak > self.reject_threshold, axis=1)
        self.rejected_indices = set(np.where(bad)[0])
        return self.rejected_indices
    
    def manual_reject(self, epoch_idx):
        """手动标记坏 epoch"""
        self.rejected_indices.add(epoch_idx)
    
    def get_good_epochs(self, epochs):
        """返回好的 epoch"""
        good = [i for i in range(len(epochs)) 
                if i not in self.rejected_indices]
        return epochs[good]
```

---

## 8. 总结

| 概念 | 核心要点 |
|------|----------|
| 事件标记 | N×3 数组，(sample, 0, event_id) |
| 三种标记模式 | 自动检测 / 手动点击 / 批量导入 |
| Epoch 提取 | tmin/tmax/baseline 三个核心参数 |
| Baseline 校正 | 减去刺激前均值，消除基线差异 |
| 坏 Epoch 拒绝 | 峰值阈值法 + 交互式手动拒绝 |
| 信号-槽连接 | 标记→提取→可视化，全链路自动更新 |
