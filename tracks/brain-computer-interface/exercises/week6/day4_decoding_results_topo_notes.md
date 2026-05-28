# Week 6 Day 4: Decoding Results and Topomap

## 核心概念

### 1. 解码结果显示

```python
class ResultPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # 准确率显示
        self.accuracy_label = QLabel("Accuracy: -")
        self.accuracy_label.setStyleSheet("font-size: 24px; font-weight: bold")
        layout.addWidget(self.accuracy_label)

        # ITR 显示
        self.itr_label = QLabel("ITR: - bits/min")
        layout.addWidget(self.itr_label)

        # 混淆矩阵
        self.confusion_matrix_widget = FigureCanvasQTAgg(Figure())
        layout.addWidget(self.confusion_matrix_widget)
```

### 2. 拓扑图

```python
import mne
import numpy as np

def plot_topomap(evoked, info):
    """绘制拓扑图"""
    fig, ax = plt.subplots()
    mne.viz.plot_topomap(evoked.data, info, axes=ax, show=False)
    return fig

def plot_topo_series(evoked, times):
    """绘制时间序列拓扑图"""
    fig = evoked.animate_topomap(times=times)
    return fig
```

### 3. 频谱拓扑图

```python
def plot_psd_topomap(epochs, info):
    """绘制 PSD 拓扑分布"""
    psd, freqs = mne.time_frequency.psd Welch(epochs, fmin=8, fmax=13)

    # Alpha 功率平均
    alpha_psd = psd[:, :, (freqs >= 8) & (freqs <= 13)].mean(axis=-1)
    alpha_power = alpha_psd.mean(axis=0)

    fig, ax = plt.subplots()
    mne.viz.plot_topomap(alpha_power, info, axes=ax, cmap='viridis')
    ax.set_title('Alpha Power Topomap')
```

### 4. 分类器结果可视化

```python
def plot_classification_results(y_true, y_pred, classes):
    """混淆矩阵"""
    from sklearn.metrics import confusion_matrix
    import seaborn as sns

    cm = confusion_matrix(y_true, y_pred)

    fig, ax = plt.subplots()
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=classes, yticklabels=classes, ax=ax)
    ax.set_xlabel('Predicted')
    ax.set_ylabel('True')
    return fig
```

### 5. 时频拓扑图

```python
def plot_tfr_topomap(tfr, info, time_idx):
    """特定时间点的时频拓扑图"""
    fig, axes = plt.subplots(1, len(time_idx), figsize=(15, 4))

    for i, t in enumerate(time_idx):
        mne.viz.plot_topomap(tfr.data[:, :, t], info,
                            axes=axes[i], show=False)
        axes[i].set_title(f't={t}ms')

    return fig
```

## 练习要点

1. 掌握解码结果展示
2. 学会拓扑图绘制
3. 理解时频拓扑

## 参考资料

- [MNE 拓扑图](https://mne.tools/stable/auto_tutorials/evoked/plot_topomap.html)
- [混淆矩阵](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html)