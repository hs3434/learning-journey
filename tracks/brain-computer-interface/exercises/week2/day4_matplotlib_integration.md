# Week 2 Day 4: Matplotlib Integration

## 核心概念

### 1. FigureCanvasQTAgg

将 Matplotlib 嵌入 Qt：

```python
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

class EEGPlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.canvas = FigureCanvasQTAgg(Figure(figsize=(10, 6)))
        layout.addWidget(self.canvas)

        self.ax = self.canvas.figure.add_subplot(111)
```

### 2. 实时更新

```python
def update_plot(self):
    self.ax.clear()
    self.ax.plot(self.t, self.data)
    self.canvas.draw()  # 重新绘制
```

### 3. 动画刷新

```python
from PyQt6.QtCore import QTimer

self.timer = QTimer()
self.timer.timeout.connect(self.update_plot)
self.timer.start(100)  # 100ms 刷新
```

## 性能优化

### 减少重绘

```python
# 只在数据变化时重绘
if self.needs_redraw:
    self.canvas.draw_idle()  # 比 draw() 更高效
```

### 数据下采样

```python
def downsample(data, factor):
    return data[::factor]
```

## EEG 绘图组件

```python
class EEGPlotWidget(QWidget):
    def set_data(self, data, fs=256):
        self.data = data
        self.fs = fs
        self.update_plot()

    def update_plot(self):
        # 取部分数据绘制
        chunk = self.data[:self.fs * 5]  # 5秒
        self.ax.plot(np.arange(len(chunk)) / self.fs, chunk)
        self.canvas.draw()
```

## 练习要点

1. 掌握 FigureCanvasQTAgg 嵌入方法
2. 学会使用 QTimer 实现定时刷新
3. 理解 draw_idle vs draw 的区别

## 参考资料

- [Matplotlib Qt 后端](https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_qt_sgskip.html)
- [Qt Matplotlib 集成](https://www.pythongui.com/embedding-matplotlib-graphs-into-your-pyqt-application/)