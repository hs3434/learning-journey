# Week 6 Day 3: Event Marking and Epoch Extraction UI

## 核心概念

### 1. 事件标记界面

```python
class EventMarkerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.events = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 事件列表
        self.event_list = QListWidget()
        layout.addWidget(self.event_list)

        # 添加事件按钮
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Event")
        self.add_btn.clicked.connect(self.add_event)
        btn_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_event)
        btn_layout.addWidget(self.remove_btn)

        layout.addLayout(btn_layout)

    def add_event(self):
        event = {
            'time': self.current_time,
            'label': self.label_input.text(),
            'value': self.value_spin.value()
        }
        self.events.append(event)
        self.update_list()
```

### 2. Epoch 提取控制

```python
class EpochControlPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout(self)

        self.tmin = QDoubleSpinBox()
        self.tmin.setRange(-1, 0)
        self.tmin.setValue(-0.2)
        self.tmin.setSuffix(" s")
        layout.addRow("Start:", self.tmin)

        self.tmax = QDoubleSpinBox()
        self.tmax.setRange(0, 2)
        self.tmax.setValue(0.5)
        self.tmax.setSuffix(" s")
        layout.addRow("End:", self.tmax)

        self.baseline_start = QDoubleSpinBox()
        self.baseline_start.setValue(-0.2)
        layout.addRow("Baseline Start:", self.baseline_start)

        self.baseline_end = QDoubleSpinBox()
        self.baseline_end.setValue(0)
        layout.addRow("Baseline End:", self.baseline_end)

    def get_epoch_params(self):
        return {
            'tmin': self.tmin.value(),
            'tmax': self.tmax.value(),
            'baseline': (self.baseline_start.value(), self.baseline_end.value())
        }
```

### 3. 可视化事件

```python
def plot_events_on_raw(self):
    self.ax.clear()
    self.ax.plot(self.raw.times, self.raw.get_data()[0] * 1e6, linewidth=0.5)

    for event in self.events:
        t = event['time']
        self.ax.axvline(t, color='red', linestyle='--', alpha=0.7)
        self.ax.text(t, self.ax.get_ylim()[1], event['label'],
                    rotation=45, fontsize=8)

    self.canvas.draw()
```

### 4. Epoch 可视化

```python
def plot_epochs_overlay(self, epochs):
    self.ax.clear()

    for i, epoch in enumerate(epochs[:10]):  # 前10个
        self.ax.plot(epochs.times * 1000, epoch[0] * 1e6,
                    alpha=0.3, linewidth=0.5)

    # 平均
    evoked = epochs.average()
    self.ax.plot(epochs.times * 1000, evoked.data[0] * 1e6,
                color='red', linewidth=2, label='Average')

    self.ax.axvline(0, color='black', linestyle='--')
    self.ax.set_xlabel('Time (ms)')
    self.ax.set_ylabel('Amplitude (μV)')
    self.ax.legend()
```

## 练习要点

1. 掌握事件标记 UI
2. 学会 epoch 参数控制
3. 理解 epoch 可视化

## 参考资料

- [MNE Epochs](https://mne.tools/stable/generated/mne.Epochs.html)
- [Qt 列表控件](https://doc.qt.io/qt-6/qlistwidget.html)