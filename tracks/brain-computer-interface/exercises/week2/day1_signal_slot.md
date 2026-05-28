# Week 2 Day 1: Qt Signal-Slot Mechanism

## 核心概念

### 1. 信号槽机制

Qt 的核心特性是信号槽机制，实现对象间的松耦合通信：

```python
from PyQt6.QtCore import pyqtSignal, pyqtSlot

class Counter(QWidget):
    count_changed = pyqtSignal(int)  # 定义信号

    def increment(self):
        self._count += 1
        self.count_changed.emit(self._count)  # 发射信号
```

### 2. 信号槽连接

```python
# 连接信号到槽
counter.count_changed.connect(self.on_count_changed)

# 断开连接
counter.count_changed.disconnect(self.on_count_changed)
```

### 3. 内置信号

```python
# QPushButton
button.clicked.connect handler)

# QLineEdit
text_changed = pyqtSignal(str)
editingFinished = pyqtSignal()
```

### 4. 自定义信号

```python
class Worker(QThread):
    progress = pyqtSignal(int)
    result = pyqtSignal(object)
    error = pyqtSignal(str)
```

## 信号槽规则

| 规则 | 说明 |
|------|------|
| 信号可以连接到槽或信号 | `sender.signal.connect(receiver.slot)` |
| 一个信号可以连接多个槽 | 所有槽都会被调用 |
| 多个信号可以连接同一个槽 | 按触发顺序调用 |
| 信号可以带有参数 | 参数类型必须匹配 |

## 示例：计数器 Widget

```python
class Counter(QWidget):
    count_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._count = 0
        self.setup_ui()

    def increment(self):
        self._count += 1
        self.count_changed.emit(self._count)
```

## 练习要点

1. 理解信号槽的松耦合特性
2. 掌握自定义信号的写法
3. 学会连接和断开信号槽

## 参考资料

- [Qt 信号槽文档](https://doc.qt.io/qt-6/signalsandslots.html)
- [PyQt6 信号槽教程](https://www.pythongui.com/using-qthreads-to-prevent-app-freezing/)