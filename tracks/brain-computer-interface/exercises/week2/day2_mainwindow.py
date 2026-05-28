"""
Week 2 Day 2: QMainWindow, Menu, Toolbar
=========================================
QMainWindow、菜单、工具栏

演示完整的 QMainWindow 结构：菜单栏、工具栏、中心部件、状态栏
"""
import sys

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout,
        QPushButton, QLabel, QMenuBar, QMenu, QToolBar,
        QStatusBar, QFileDialog, QMessageBox
    )
    from PyQt6.QtCore import Qt, QSize
    from PyQt6.QtGui import QAction, QKeySequence
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("PyQt6 not available. Skipping Qt code demo.")
    sys.exit(0)


class EEGViewerWindow(QMainWindow):
    """EEG 查看器主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BCI EEG Viewer")
        self.setMinimumSize(1000, 600)

        self.eeg_data = None
        self.current_channel = 0

        self.setup_ui()
        self.create_actions()
        self.create_menus()
        self.create_toolbars()
        self.create_statusbar()

    def setup_ui(self):
        """设置中心部件"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.info_label = QLabel("No data loaded")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)

        self.plot_button = QPushButton("Show Waveform")
        self.plot_button.clicked.connect(self.on_plot)
        layout.addWidget(self.plot_button)

    def create_actions(self):
        """创建操作 (Action)"""
        self.action_open = QAction("Open EEG File...", self)
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        self.action_open.triggered.connect(self.on_open_file)

        self.action_save = QAction("Save Results", self)
        self.action_save.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save.triggered.connect(self.on_save)
        self.action_save.setEnabled(False)

        self.action_exit = QAction("Exit", self)
        self.action_exit.setShortcut(QKeySequence.StandardKey.Quit)
        self.action_exit.triggered.connect(self.close)

        self.action_filter = QAction("Apply Filter", self)
        self.action_filter.setShortcut(QKeySequence("Ctrl+F"))
        self.action_filter.triggered.connect(self.on_filter)

        self.action_about = QAction("About", self)
        self.action_about.triggered.connect(self.on_about)

    def create_menus(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        file_menu.addAction(self.action_open)
        file_menu.addAction(self.action_save)
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)

        process_menu = menubar.addMenu("Process")
        process_menu.addAction(self.action_filter)

        help_menu = menubar.addMenu("Help")
        help_menu.addAction(self.action_about)

    def create_toolbars(self):
        """创建工具栏"""
        file_toolbar = self.addToolBar("File")
        file_toolbar.setIconSize(QSize(24, 24))
        file_toolbar.addAction(self.action_open)
        file_toolbar.addAction(self.action_save)

        process_toolbar = self.addToolBar("Process")
        process_toolbar.addAction(self.action_filter)

    def create_statusbar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def on_open_file(self):
        """打开文件对话框"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open EEG File",
            "",
            "EEG Files (*.fif *.edf *.bdf);;All Files (*)"
        )
        if filepath:
            self.load_file(filepath)

    def load_file(self, filepath):
        """加载 EEG 文件"""
        self.info_label.setText(f"Loaded: {filepath}")
        self.action_save.setEnabled(True)
        self.status_bar.showMessage(f"Loaded: {filepath}", 3000)

    def on_save(self):
        """保存结果"""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            "",
            "CSV Files (*.csv);;JSON Files (*.json)"
        )
        if filepath:
            self.status_bar.showMessage(f"Saved: {filepath}", 3000)

    def on_filter(self):
        """滤波处理"""
        self.status_bar.showMessage("Applying filter...", 2000)

    def on_plot(self):
        """绘制波形"""
        self.info_label.setText("Plotting waveform...")

    def on_about(self):
        """关于对话框"""
        QMessageBox.about(
            self,
            "About BCI EEG Viewer",
            "BCI EEG Viewer v0.1\n\nA Qt-based EEG data visualization tool."
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = EEGViewerWindow()
    window.show()
    sys.exit(app.exec())