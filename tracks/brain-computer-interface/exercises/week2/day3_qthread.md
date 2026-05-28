# Week 2 Day 3: QThread Worker Pattern

## 为什么需要 QThread？

GUI 线程必须保持响应，不能在其中执行耗时操作（如加载 EEG 数据、运行分类器）。

**正确做法**：在工作线程中执行耗时任务，通过信号通知 UI 线程。

## QThread Worker 模式

```python
from PyQt6.QtCore import QThread, pyqtSignal

class Worker(QThread):
    progress = pyqtSignal(int)
    result = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath

    def run(self):
        try:
            self.progress.emit(10)
            self.log.emit("Loading data...")

            data = self.load_data()

            self.progress.emit(100)
            self.result.emit(data)

        except Exception as e:
            self.error.emit(str(e))
```

## 信号线程安全

`pyqtSignal` 是线程安全的，可以在子线程中发射，UI 线程接收：

```python
# MainWindow
self.worker = Worker(filepath)
self.worker.progress.connect(self.progress_bar.setValue)
self.worker.result.connect(self.on_result_ready)
self.worker.error.connect(self.on_error)
self.worker.start()
```

## 常见错误

| 错误做法 | 正确做法 |
|----------|----------|
| 在子线程直接操作 UI | 通过信号间接更新 UI |
| 不用信号，直接调用 UI 方法 | 使用 `signal.emit()` |
| 在 UI 线程执行耗时操作 | 使用 Worker 线程 |

## 数据传递

通过构造函数传递数据：

```python
class Worker(QThread):
    def __init__(self, data, params):
        super().__init__()
        self.data = data
        self.params = params
```

## 练习要点

1. 理解为什么需要后台线程
2. 掌握 Worker 模式的标准写法
3. 学会通过信号传递结果

## 参考资料

- [Qt 线程文档](https://doc.qt.io/qt-6/qthread.html)
- [Qt 线程安全](https://doc.qt.io/qt-6/threads.html)