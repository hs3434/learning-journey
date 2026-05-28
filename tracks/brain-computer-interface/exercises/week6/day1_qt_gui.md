# Week 6 Day 1: Qt GUI Architecture

## 核心概念

### 1. MVC 架构

```python
class BCIModel:
    """数据模型"""
    def __init__(self):
        self.raw = None
        self.epochs = None
        self.params = {}

class BCIView:
    """视图"""
    def update_plot(self, data):
        self.ax.plot(data)
        self.canvas.draw()

class BCIController:
    """控制器"""
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def process(self):
        self.model.filter()
        self.view.update_plot(self.model.get_data())
```

### 2. Qt 组件层次

```python
QMainWindow (主窗口)
├── QMenuBar (菜单栏)
├── QToolBar (工具栏)
├── QStatusBar (状态栏)
├── Central Widget (中心部件)
│   ├── EEGPlotWidget
│   └── SpectrumWidget
└── QDockWidget (停靠部件)
    ├── FilterPanel
    └── EpochPanel
```

### 3. 信号槽连接

```python
# Model → View
self.model.data_changed.connect(self.view.update)

# Controller → Model
self.controller.load_request.connect(self.model.load)

# Controller → View
self.controller.status_update.connect(self.view.show_status)
```

### 4. 线程模型

```python
# UI 线程：只更新界面
# Worker 线程：处理数据

class Worker(QThread):
    progress = pyqtSignal(int)
    result = pyqtSignal(object)

    def run(self):
        # 后台处理
        for i in range(100):
            self.progress.emit(i)
            # 处理...
        self.result.emit(result)
```

## 练习要点

1. 理解 MVC 架构模式
2. 掌握 Qt 组件层次
3. 学会线程间通信

## 参考资料

- [Qt 架构](https://doc.qt.io/qt-6/qtwidgets-mainwindow.html)
- [Qt 线程](https://doc.qt.io/qt-6/qthread.html)