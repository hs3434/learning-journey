# Week 2 Day 2: QMainWindow, Menu, Toolbar

## 核心概念

### 1. QMainWindow 结构

```python
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BCI Viewer")
        self.setup_ui()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
```

### 2. 菜单栏

```python
menubar = self.menuBar()

file_menu = menubar.addMenu("File")
file_menu.addAction("Open", self.on_open)
file_menu.addSeparator()
file_menu.addAction("Exit", self.close)
```

### 3. 工具栏

```python
toolbar = self.addToolBar("Main")
toolbar.addAction("Open", self.on_open)
toolbar.addAction("Save", self.on_save)
```

### 4. 状态栏

```python
self.statusBar().showMessage("Ready", 3000)  # 3秒后消失
```

### 5. Action 创建

```python
from PyQt6.QtGui import QAction, QKeySequence

open_action = QAction("Open", self)
open_action.setShortcut(QKeySequence.StandardKey.Open)
open_action.triggered.connect(self.on_open_file)
```

## BCI 应用布局示例

```python
def setup_ui(self):
    central = QWidget()
    self.setCentralWidget(central)
    layout = QVBoxLayout(central)

    # 工具栏
    toolbar = self.addToolBar("File")
    toolbar.addAction(self.action_open)

    # 主区域：左右分栏
    splitter = QSplitter()
    splitter.addWidget(self.control_panel)   # 左侧控制面板
    splitter.addWidget(self.plot_area)       # 右侧绘图区
    layout.addWidget(splitter)

    # 状态栏
    self.statusBar().showMessage("Ready")
```

## 练习要点

1. 掌握 QMainWindow 的标准结构
2. 熟练创建菜单和工具栏
3. 学会使用 QKeySequence 设置快捷键

## 参考资料

- [Qt Main Window](https://doc.qt.io/qt-6/qmainwindow.html)
- [Qt 菜单和工具栏](https://doc.qt.io/qt-6/qmenu.html)