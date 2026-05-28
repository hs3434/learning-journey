# Week 6 Day 2: Filter and Visualization Integration

## 核心概念

### 1. 集成架构

```python
class FilterVisualizationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.pipeline = None

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 参数面板
        self.filter_panel = FilterPanel()
        layout.addWidget(self.filter_panel)

        # Matplotlib 画布
        self.canvas = FigureCanvasQTAgg(Figure())
        layout.addWidget(self.canvas)

        # 控制按钮
        self.apply_btn = QPushButton("Apply Filter")
        self.apply_btn.clicked.connect(self.on_apply_filter)
        layout.addWidget(self.apply_btn)

    def on_apply_filter(self):
        params = self.filter_panel.get_params()
        self.pipeline.set_filter_params(params)
        self.pipeline.run()
        self.update_plot()
```

### 2. 交互式滤波

```python
from scipy.signal import butter, filtfilt

class FilterPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout(self)

        self.lowcut = QDoubleSpinBox()
        self.lowcut.setRange(0.1, 100)
        self.lowcut.setValue(0.5)
        layout.addRow("Lowcut:", self.lowcut)

        self.highcut = QDoubleSpinBox()
        self.highcut.setRange(1, 200)
        self.highcut.setValue(40)
        layout.addRow("Highcut:", self.highcut)

    def get_params(self):
        return {
            'lowcut': self.lowcut.value(),
            'highcut': self.highcut.value()
        }
```

### 3. 实时更新

```python
def update_plot(self):
    self.ax.clear()

    # 原始数据
    self.ax.plot(self.raw_data, alpha=0.5, label='Raw')

    # 滤波后数据
    self.ax.plot(self.filtered_data, label='Filtered')

    self.ax.legend()
    self.canvas.draw_idle()  # 增量更新
```

### 4. PSD 对比

```python
from scipy.signal import welch

def plot_psd_comparison(self, raw, filtered):
    freqs1, psd1 = welch(raw, fs=256)
    freqs2, psd2 = welch(filtered, fs=256)

    self.ax.clear()
    self.ax.semilogy(freqs1, psd1, label='Raw')
    self.ax.semilogy(freqs2, psd2, label='Filtered')
    self.ax.legend()
```

## 练习要点

1. 掌握集成 UI 和数据处理
2. 学会交互式参数设置
3. 理解实时更新机制

## 参考资料

- [Matplotlib Qt 集成](https://www.pythongui.com/embedding-matplotlib-graphs-into-your-pyqt-application/)
- [MNE 可视化](https://mne.tools/stable/auto_tutorials/visualization/plot_visualize_raw.html)