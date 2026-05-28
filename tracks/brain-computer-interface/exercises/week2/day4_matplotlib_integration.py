"""
Week 2 Day 4: Matplotlib Integration
====================================
Matplotlib + QWidget 集成

将 Matplotlib 绘图嵌入 Qt GUI
"""
import sys
import numpy as np

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout,
        QPushButton, QHBoxLayout, QSlider, QLabel
    )
    from PyQt6.QtCore import Qt, QTimer
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.figure import Figure
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("PyQt6 not available. Skipping Qt code demo.")
    sys.exit(0)


class EEGPlotWidget(QWidget):
    """EEG 波形显示 Widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.data = None
        self.current_start = 0

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.canvas = FigureCanvasQTAgg(Figure(figsize=(10, 6)))
        layout.addWidget(self.canvas)

        self.ax = self.canvas.figure.add_subplot(111)
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Amplitude')
        self.ax.set_title('EEG Waveform')

        control_layout = QHBoxLayout()

        self.prev_btn = QPushButton("<< Prev")
        self.prev_btn.clicked.connect(self.prev_chunk)
        control_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Next >>")
        self.next_btn.clicked.connect(self.next_chunk)
        control_layout.addWidget(self.next_btn)

        self.channel_slider = QSlider(Qt.Orientation.Horizontal)
        self.channel_slider.setMinimum(0)
        self.channel_slider.setMaximum(15)
        self.channel_slider.valueChanged.connect(self.on_channel_change)
        control_layout.addWidget(QLabel("Channel:"))
        control_layout.addWidget(self.channel_slider)

        self.position_label = QLabel("Showing: 0-5s")
        control_layout.addWidget(self.position_label)

        layout.addLayout(control_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(100)

    def set_data(self, data, fs=256):
        self.data = data
        self.fs = fs
        self.channel_slider.setMaximum(data.shape[0] - 1)
        self.update_plot()

    def update_plot(self):
        if self.data is None:
            return

        channel = self.channel_slider.value()
        ch_data = self.data[channel]

        window_size = 5 * self.fs
        start = self.current_start * window_size
        end = min(start + window_size, len(ch_data))

        if start >= len(ch_data):
            start = 0
            self.current_start = 0

        t = np.arange(start, end) / self.fs
        chunk = ch_data[start:end]

        self.ax.clear()
        self.ax.plot(t, chunk, linewidth=0.5)
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Amplitude (μV)')
        self.ax.set_title(f'EEG Channel {channel}')
        self.ax.set_xlim(t[0], t[-1])
        self.canvas.draw()

        self.position_label.setText(f"Showing: {t[0]:.1f}-{t[-1]:.1f}s")

    def prev_chunk(self):
        if self.current_start > 0:
            self.current_start -= 1
        self.update_plot()

    def next_chunk(self):
        self.current_start += 1
        self.update_plot()

    def on_channel_change(self, value):
        self.update_plot()


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Matplotlib Integration Demo")
        self.setMinimumSize(1000, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.plot_widget = EEGPlotWidget()
        layout.addWidget(self.plot_widget)

        load_btn = QPushButton("Load Sample Data")
        load_btn.clicked.connect(self.load_data)
        layout.addWidget(load_btn)

    def load_data(self):
        import mne
        mne.set_log_level('WARNING')
        sample_data_folder = mne.datasets.sample.data_path()
        raw_file = sample_data_folder / 'MEG' / 'sample' / 'sample_audvis_raw.fif'
        raw = mne.io.read_raw_fif(raw_file, preload=True, verbose=False)
        raw.pick('eeg')
        self.plot_widget.set_data(raw.get_data()[:16], raw.info['sfreq'])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())