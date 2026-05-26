# Week 6 Day 19：解码结果显示与频谱拓扑图

## 1. BCI 解码结果展示什么？

BCI 解码后，用户需要看到**三个层面的信息**：

```
Layer 1: 分类结果
  → "当前试次被判断为：左手运动"（单次结果）

Layer 2: 性能指标  
  → 准确率 85%、ITR 60 bits/min（整体表现）

Layer 3: 可解释性
  → "分类器主要看 C3 通道的 Alpha 能量"（为什么这么判断）
```

类比医疗报告：
- Layer 1 = 诊断结论（"你感冒了"）
- Layer 2 = 检验指标（"白细胞 12000，偏高"）
- Layer 3 = 详细分析（"上呼吸道感染导致"）

---

## 2. 分类结果展示

### 2.1 实时分类显示

```python
class ClassificationResultWidget(QWidget):
    """实时分类结果显示"""
    
    def __init__(self, class_labels):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # 大号结果显示
        self.result_label = QLabel("Waiting...")
        self.result_label.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.result_label)
        
        # 置信度条
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setRange(0, 100)
        layout.addWidget(self.confidence_bar)
        
        # 各类概率
        self.prob_labels = {}
        for label in class_labels:
            lbl = QLabel(f"{label}: --")
            layout.addWidget(lbl)
            self.prob_labels[label] = lbl
    
    def update_result(self, predicted_class, probabilities):
        """更新分类结果"""
        self.result_label.setText(f"Predicted: {predicted_class}")
        self.result_label.setStyleSheet(
            f"color: {'#4CAF50' if probabilities.max() > 0.8 else '#FF9800'}"
        )
        self.confidence_bar.setValue(int(probabilities.max() * 100))
        
        for i, (name, lbl) in enumerate(self.prob_labels.items()):
            lbl.setText(f"{name}: {probabilities[i]:.1%}")
```

### 2.2 混淆矩阵

混淆矩阵是分类结果的"成绩单"：

```
              Predicted
           Left   Right  Foot
Actual  Left  [ 45    3     2 ]   ← 45次左手被正确识别为左手
        Right [  4   42     4 ]   ← 4次右手被错认为左手
        Foot  [  1    5    44 ]   ← 5次脚被错认为右手
```

```python
class ConfusionMatrixWidget(FigureCanvasQTAgg):
    """混淆矩阵可视化"""
    
    def __init__(self):
        self.fig = Figure(figsize=(5, 4))
        super().__init__(self.fig)
    
    def plot(self, y_true, y_pred, class_names):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        from sklearn.metrics import confusion_matrix
        cm = confusion_matrix(y_true, y_pred)
        cm_normalized = cm.astype(float) / cm.sum(axis=1, keepdims=True)
        
        im = ax.imshow(cm_normalized, cmap='Blues', vmin=0, vmax=1)
        
        # 添加数字标注
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                color = 'white' if cm_normalized[i, j] > 0.5 else 'black'
                ax.text(j, i, f'{cm[i, j]}\n({cm_normalized[i, j]:.0%})',
                       ha='center', va='center', color=color, fontsize=9)
        
        ax.set_xticks(range(len(class_names)))
        ax.set_yticks(range(len(class_names)))
        ax.set_xticklabels(class_names, fontsize=9)
        ax.set_yticklabels(class_names, fontsize=9)
        ax.set_xlabel('Predicted', fontsize=11)
        ax.set_ylabel('Actual', fontsize=11)
        ax.set_title('Confusion Matrix', fontsize=12, fontweight='bold')
        
        self.fig.colorbar(im, ax=ax, shrink=0.8)
        self.draw_idle()
```

---

## 3. 性能指标

### 3.1 核心指标计算

```python
@dataclass
class DecodingMetrics:
    """解码性能指标"""
    accuracy: float          # 准确率
    kappa: float            # Cohen's Kappa（修正随机猜测）
    itr: float              # 信息传输率 (bits/min)
    confusion_matrix: np.ndarray  # 混淆矩阵
    cv_scores: np.ndarray   # 交叉验证分数
    
    @staticmethod
    def compute(y_true, y_pred, n_classes, trial_duration=4.0):
        from sklearn.metrics import accuracy_score, cohen_kappa_score
        
        acc = accuracy_score(y_true, y_pred)
        kappa = cohen_kappa_score(y_true, y_pred)
        
        # ITR 计算
        P = acc
        N = n_classes
        if 0 < P < 1:
            itr = (60 / trial_duration) * (
                np.log2(N) + P * np.log2(P) + 
                (1 - P) * np.log2((1 - P) / (N - 1))
            )
        elif P == 1:
            itr = (60 / trial_duration) * np.log2(N)
        else:
            itr = 0.0
        
        cm = confusion_matrix(y_true, y_pred)
        
        return DecodingMetrics(
            accuracy=acc, kappa=kappa, itr=itr,
            confusion_matrix=cm, cv_scores=np.array([])
        )
```

### 3.2 ITR 可视化

ITR（Information Transfer Rate）随准确率变化的曲线：

```
ITR (bits/min)
  ^
  |              ___----====----___
  |          __--                  --__
  |       _-                          -_
  |     _-                              -_
  |   _-                                  -_
  |  -                                     -
  | -                                       -
  |___________________________________________→ Accuracy
  0%    25%   50%   75%   100%
```

在 4-class BCI 中：
- 25% = 随机猜测，ITR = 0
- 50% = ITR 约 15 bits/min
- 75% = ITR 约 40 bits/min
- 100% = ITR = 60 bits/min（理论最大值）

---

## 4. 频谱拓扑图

### 4.1 为什么需要频谱拓扑图？

时域波形看的是"电压随时间变化"，但 BCI 很多范式是**频域特征**：

| 范式 | 频域特征 | 拓扑分布 |
|------|----------|----------|
| MI | Alpha/Beta ERD | 对侧运动皮层 |
| SSVEP | 稳态频率功率 | 枕叶 |
| P300 | 时域振幅 | 顶叶 |

拓扑图 = **把频域特征画到头皮上**，一眼看出哪个脑区在"干活"。

### 4.2 实现方式

```python
class SpectralTopoWidget(FigureCanvasQTAgg):
    """频谱拓扑图组件"""
    
    def __init__(self):
        self.fig = Figure(figsize=(10, 4))
        super().__init__(self.fig)
    
    def plot_band_topomaps(self, epochs, bands=None):
        """多频段头皮拓扑图"""
        if bands is None:
            bands = {
                'Delta (1-4 Hz)': (1, 4),
                'Theta (4-8 Hz)': (4, 8),
                'Alpha (8-13 Hz)': (8, 13),
                'Beta (13-30 Hz)': (13, 30),
            }
        
        self.fig.clear()
        n_bands = len(bands)
        
        for i, (name, (fmin, fmax)) in enumerate(bands.items()):
            ax = self.fig.add_subplot(1, n_bands, i + 1)
            
            # 计算频段功率
            psd = epochs.compute_psd(fmin=fmin, fmax=fmax)
            psd_avg = psd.average()
            
            # 绘制拓扑图
            psd_avg.plot_topomap(axes=ax, show=False)
            ax.set_title(name, fontsize=9)
        
        self.fig.tight_layout()
        self.draw_idle()
```

### 4.3 时频拓扑图序列

展示某个频段功率随时间在头皮上的变化：

```python
def plot_topo_timecourse(self, epochs, band='alpha', times=None):
    """时频拓扑图时间序列"""
    from mne.time_frequency import tfr_morlet
    
    freqs = np.logspace(np.log10(4), np.log10(30), 20)
    n_cycles = freqs / 2
    
    power, _ = tfr_morlet(epochs, freqs=freqs, n_cycles=n_cycles,
                           return_itc=False, n_jobs=1)
    
    # 选择频段
    if band == 'alpha':
        power_band = power.copy().pick(freqs=[8, 13])
    
    # 多时间点拓扑图
    if times is None:
        times = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    
    power_band.plot_topomap(times=times, show=False)
```

---

## 5. 解码结果的可解释性

### 5.1 特征权重可视化

线性分类器（LDA/SVM）的权重可以直接解释为"哪些特征最重要"：

```python
def plot_lda_weights(lda, channel_names, times):
    """LDA 权重的时空分布"""
    # lda.coef_ shape: (n_classes-1, n_features)
    weights = lda.coef_[0].reshape(len(channel_names), len(times))
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # 左：权重热力图（通道×时间）
    im = ax1.imshow(weights, aspect='auto', cmap='RdBu_r',
                    extent=[times[0], times[-1], 
                            len(channel_names), 0])
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Channel')
    ax1.set_title('LDA Weights (Channel × Time)')
    fig.colorbar(im, ax=ax1)
    
    # 右：权重的头皮分布（特定时间点）
    # ...
```

### 5.2 CSP 模式可视化

```python
def plot_csp_patterns(csp, info, n_patterns=4):
    """CSP 空间滤波器模式"""
    fig, axes = plt.subplots(1, n_patterns, figsize=(15, 3))
    
    for i in range(n_patterns):
        mne.viz.plot_topomap(csp.patterns_[i], info, axes=axes[i], show=False)
        label = f'CSP {i+1}' + (' (max var)' if i < n_patterns//2 else ' (min var)')
        axes[i].set_title(label, fontsize=10)
    
    fig.suptitle('CSP Spatial Patterns', fontsize=13, fontweight='bold')
```

---

## 6. 解码面板完整布局

```
┌──────────────────────────────────────────────────────────┐
│  Decoding Results Dashboard                                │
├──────────────────────┬───────────────────────────────────┤
│                      │                                    │
│   Confusion Matrix   │   Accuracy / ITR over time        │
│   (热力图)           │   (折线图)                         │
│                      │                                    │
├──────────────────────┼───────────────────────────────────┤
│                      │                                    │
│   Band Topomaps      │   LDA/CSP Weights                 │
│   (4个头皮图)        │   (特征重要性)                     │
│                      │                                    │
├──────────────────────┴───────────────────────────────────┤
│  Summary: Acc=85.2% | Kappa=0.78 | ITR=62 bits/min       │
└──────────────────────────────────────────────────────────┘
```

---

## 7. 总结

| 概念 | 核心要点 |
|------|----------|
| 三层结果 | 分类结果 + 性能指标 + 可解释性 |
| 混淆矩阵 | 对角线=正确，非对角线=混淆 |
| ITR | BCI 系统的核心性能指标（bits/min） |
| 频谱拓扑图 | 频域特征的头皮空间分布 |
| 特征权重 | LDA/CSP 权重的可解释性可视化 |
| Dashboard | 多图表协同展示完整解码结果 |
