"""
Week 2 Day 5: Dialogs and File Handling
=======================================
布局管理、对话框、文件选择

综合练习：文件选择对话框、参数设置对话框、布局管理
"""
import sys

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout,
        QHBoxLayout, QPushButton, QLabel, QLineEdit,
        QFileDialog, QMessageBox, QDialog, QGroupBox,
        QFormLayout, QDialogButtonBox, QCheckBox,
        QSpinBox, QDoubleSpinBox, QComboBox
    )
    from PyQt6.QtCore import Qt
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("PyQt6 not available. Skipping Qt code demo.")
    sys.exit(0)


class FilterParamsDialog(QDialog):
    """滤波参数设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filter Parameters")
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.lowcut = QDoubleSpinBox()
        self.lowcut.setRange(0.1, 100)
        self.lowcut.setValue(0.5)
        self.lowcut.setSuffix(" Hz")
        layout.addRow("Lowcut:", self.lowcut)

        self.highcut = QDoubleSpinBox()
        self.highcut.setRange(1, 200)
        self.highcut.setValue(40)
        self.highcut.setSuffix(" Hz")
        layout.addRow("Highcut:", self.highcut)

        self.order = QSpinBox()
        self.order.setRange(1, 10)
        self.order.setValue(4)
        layout.addRow("Filter Order:", self.order)

        self.notch_enable = QCheckBox("Enable Notch Filter")
        self.notch_enable.setChecked(True)
        layout.addRow("", self.notch_enable)

        self.notch_freq = QComboBox()
        self.notch_freq.addItems(["50 Hz", "60 Hz"])
        self.notch_freq.setCurrentText("50 Hz")
        layout.addRow("Notch Frequency:", self.notch_freq)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_params(self):
        return {
            'lowcut': self.lowcut.value(),
            'highcut': self.highcut.value(),
            'order': self.order.value(),
            'notch_enable': self.notch_enable.isChecked(),
            'notch_freq': int(self.notch_freq.currentText().split()[0])
        }


class MainWindow(QMainWindow):
    """主窗口：演示各种对话框"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dialogs Demo")
        self.setup_ui()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        buttons = [
            ("Open EEG File", self.on_open_file),
            ("Save Results", self.on_save_results),
            ("Filter Parameters", self.on_filter_params),
            ("About", self.on_about),
            ("Warning", self.on_warning),
            ("Error", self.on_error),
            ("Question", self.on_question),
        ]

        for text, slot in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        self.statusLabel = QLabel("Ready")
        layout.addWidget(self.statusLabel)

    def on_open_file(self):
        filepath, selected_filter = QFileDialog.getOpenFileName(
            self,
            "Open EEG File",
            "",
            "EEG Files (*.fif *.edf *.bdf);;All Files (*)"
        )
        if filepath:
            self.statusLabel.setText(f"Opened: {filepath}")

    def on_save_results(self):
        filepath, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            "",
            "CSV Files (*.csv);;JSON Files (*.json);;All Files (*)"
        )
        if filepath:
            self.statusLabel.setText(f"Saving to: {filepath}")

    def on_filter_params(self):
        dialog = FilterParamsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            params = dialog.get_params()
            self.statusLabel.setText(
                f"Filter: {params['lowcut']}-{params['highcut']} Hz, "
                f"order={params['order']}"
            )

    def on_about(self):
        QMessageBox.about(
            self,
            "About",
            "BCI EEG Viewer v0.1\n\nA demo application."
        )

    def on_warning(self):
        QMessageBox.warning(
            self,
            "Warning",
            "This is a warning message."
        )

    def on_error(self):
        QMessageBox.critical(
            self,
            "Error",
            "An error occurred!"
        )

    def on_question(self):
        reply = QMessageBox.question(
            self,
            "Question",
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.statusLabel.setText("User chose: Yes")
        else:
            self.statusLabel.setText("User chose: No")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())