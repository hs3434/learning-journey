# Week 2 Day 5: Dialogs and File Handling

## 核心概念

### 1. 文件对话框

```python
from PyQt6.QtWidgets import QFileDialog

# 打开文件
filepath, selected_filter = QFileDialog.getOpenFileName(
    self,
    "Open EEG File",
    "",
    "EEG Files (*.fif *.edf *.bdf);;All Files (*)"
)

# 保存文件
filepath, selected_filter = QFileDialog.getSaveFileName(
    self,
    "Save Results",
    "",
    "CSV Files (*.csv);;JSON Files (*.json)"
)
```

### 2. 自定义对话框

```python
class FilterParamsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filter Parameters")
        self.setup_ui()

    def get_params(self):
        return {
            'lowcut': self.lowcut.value(),
            'highcut': self.highcut.value(),
            'order': self.order.value()
        }
```

### 3. 消息框

```python
from PyQt6.QtWidgets import QMessageBox

# 信息框
QMessageBox.information(self, "Title", "Message")

# 警告框
QMessageBox.warning(self, "Title", "Warning message")

# 错误框
QMessageBox.critical(self, "Title", "Error message")

# 确认框
reply = QMessageBox.question(self, "Confirm", "Continue?")
if reply == QMessageBox.StandardButton.Yes:
    pass
```

### 4. 布局管理

```python
# 表单布局
layout = QFormLayout()
layout.addRow("Lowcut:", self.lowcut)
layout.addRow("Highcut:", self.highcut)

# 水平/垂直布局
hbox = QHBoxLayout()
hbox.addWidget(widget1)
hbox.addStretch()
hbox.addWidget(widget2)
```

## EEG 应用场景

### 1. 参数设置对话框

```python
class FilterDialog(QDialog):
    def __init__(self):
        super().__init__()
        layout = QFormLayout()

        self.lowcut = QDoubleSpinBox()
        self.lowcut.setRange(0.1, 100)
        self.lowcut.setValue(0.5)
        self.lowcut.setSuffix(" Hz")

        layout.addRow("Lowcut:", self.lowcut)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        layout.addRow(buttons)

        self.setLayout(layout)
```

### 2. 文件过滤器

```python
filters = "EEG Files (*.fif *.edf *.bdf);;MNE Files (*.fif);;All Files (*)"
```

## 练习要点

1. 熟练使用文件对话框
2. 学会创建自定义对话框
3. 掌握各种消息框的使用

## 参考资料

- [Qt 文件对话框](https://doc.qt.io/qt-6/qfiledialog.html)
- [Qt 对话框](https://doc.qt.io/qt-6/qdialog.html)