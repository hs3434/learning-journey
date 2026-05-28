# Week 4 Day 10：解码流程 - 特征提取 + 分类器

## 1. 解码流程概览

```
原始 EEG 连续数据
      ↓ 预处理（滤波、重参考、ICA）
干净 Raw 数据
      ↓ 事件检测 + Epoch 切分
Epochs (n_epochs, n_channels, n_times)
      ↓ 特征提取
特征向量 (n_epochs, n_features)
      ↓ 分类器
预测标签 + 性能评估
```

---

## 2. 特征提取

### 2.1 时域特征（最常用）

```python
X = epochs.get_data()          # (n_ep, n_ch, n_times)

# 方法1：时序均值（最简单）
X_mean = X.mean(axis=2)        # (n_ep, n_ch) — 每个通道时间平均

# 方法2：滑动时间窗口
t_start, t_end = 0.1, 0.3     # 100-300ms
mask = (epochs.times >= t_start) & (epochs.times < t_end)
X_win = X[:, :, mask].mean(axis=2)  # 特定时间窗口平均

# 方法3：ERP 峰值
X_peak = X[:, :, :].max(axis=2)    # 最大值
X_rms  = np.sqrt((X**2).mean(axis=2))  # RMS
```

### 2.2 频域特征

```python
from scipy.signal import welch

def band_power(epoch_data, fs, fmin, fmax, nperseg=128):
    """计算特定频段功率"""
    freqs, psd = welch(epoch_data, fs=fs, nperseg=nperseg)
    mask = (freqs >= fmin) & (freqs <= fmax)
    return psd[:, mask].mean(axis=1)  # 各通道平均功率

# 提取多频段特征
features = np.column_stack([
    band_power(ep, fs, 8, 12),   # Alpha
    band_power(ep, fs, 13, 30),  # Beta
    band_power(ep, fs, 4, 7),    # Theta
])
```

### 2.3 时频特征（CSP）

**CSP（Common Spatial Patterns）** 是运动想象 BCI 的标准特征提取方法：

$$\mathbf{W} = \arg\max_{\mathbf{W}} \frac{\mathbf{W}^T \mathbf{C}_1 \mathbf{W}}{\mathbf{W}^T \mathbf{C}_2 \mathbf{W}}$$

- $\mathbf{C}_1, \mathbf{C}_2$：两类别的协方差矩阵
- 最大化类间方差 / 类内方差比率
- 投影后特征：$\mathbf{Z} = \mathbf{W}^T \mathbf{X}$

```python
from mne.decoding import CSP

csp = CSP(n_components=4, reg='ledoit_wolf')
X_csp = csp.fit_transform(X, y)  # X: (n_ep, n_ch, n_times), y: 标签
# X_csp: (n_ep, 4) — 降维到 4 个空间模式分量
```

---

## 3. 分类器

### 3.1 LDA（线性判别分析）— EEG 解码首选

LDA 假设两类数据服从高斯分布、共享协方差，通过线性超平面最大化类间距离：

$$\mathbf{w} = \mathbf{\Sigma}^{-1}(\boldsymbol{\mu}_1 - \boldsymbol{\mu}_2)$$

```python
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_mean)   # 先标准化！

clf = LinearDiscriminantAnalysis()
clf.fit(X_scaled, y)
y_pred = clf.predict(X_scaled)
coef = clf.coef_  # 空间模式权重
```

**LDA 的系数 = 空间模式（spatial pattern）**：
- 正系数 → 该通道激活越高 → 越偏向 class 1
- 负系数 → 该通道激活越高 → 越偏向 class 2
- 可以直接绘制到头皮地形图上

### 3.2 SVM（支持向量机）

```python
from sklearn.svm import SVC

clf_linear = SVC(kernel='linear', C=1.0)   # 线性核
clf_rbf    = SVC(kernel='rbf',    C=1.0)   # RBF 核（适合非线性边界）
```

### 3.3 其他分类器

| 分类器 | 适用场景 | 优点 | 缺点 |
|--------|---------|------|------|
| LDA | EEG 标准 | 快速、少量样本好 | 线性假设 |
| SVM | 高维特征 | 泛化强 | 核函数选择 |
| XGBoost | 复杂模式 | 准确率高 | 容易过拟合 |
| 深度学习 | 大数据 | 自动特征 | 需要大量数据 |

---

## 4. 交叉验证

### 4.1 Stratified K-Fold

保持每折中类别比例与整体一致：

```python
from sklearn.model_selection import StratifiedKFold, cross_val_score

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(clf, X_scaled, y, cv=cv)

print(f"CV 准确率: {scores.mean()*100:.1f}% ± {scores.std()*100:.1f}%")
# 各折准确率: scores
```

### 4.2 时间演化解码（Temporal Generalization）

用 t1 时刻训练的模型，在 t2 时刻测试，检测解码的时间稳定性：

```python
from mne.decoding import GeneralizingClassifier

clf_gen = GeneralizingClassifier(LDA(), scoring='accuracy')
clf_gen.fit(X_train, y_train)       # 按时间切片训练
scores_matrix = clf_gen.score(X_test, y_test)  # 时间泛化矩阵
```

---

## 5. 评估指标

```python
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)

# 分类报告（精确率/召回率/F1）
print(classification_report(y_true, y_pred, target_names=['Left', 'Right']))

# 混淆矩阵
cm = confusion_matrix(y_true, y_pred, labels=[1, 2])
```

| 指标 | 公式 | 含义 |
|------|------|------|
| 准确率 (Accuracy) | $\frac{TP+TN}{TP+TN+FP+FN}$ | 整体正确率 |
| 精确率 (Precision) | $\frac{TP}{TP+FP}$ | 预测为正的中真阳性比例 |
| 召回率 (Recall) | $\frac{TP}{TP+FN}$ | 实际正例中被正确预测的比例 |
| F1-Score | $2 \cdot \frac{P \cdot R}{P + R}$ | 精确率和召回率的调和平均 |

---

## 6. 实战：完整解码流程

```python
import mne
import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_score

# 1. 数据准备
raw = mne.io.read_raw_fif('preprocessed_raw.fif', preload=True)
events = mne.find_events(raw, stim_channel='STI 014')
epochs = mne.Epochs(raw, events, event_id={'left': 1, 'right': 2},
                    tmin=-0.2, tmax=0.5, baseline=(None, 0), preload=True)
epochs.drop_bad(reject=dict(eeg=150e-6), verbose=False)

# 2. 特征提取（时域均值，100-300ms 窗口）
X = epochs.get_data()
mask = (epochs.times >= 0.1) & (epochs.times <= 0.3)
X_feat = X[:, :, mask].mean(axis=2)    # (n_ep, n_ch)
y = epochs.events[:, 2]

# 3. Pipeline + 交叉验证
pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('lda',     LinearDiscriminantAnalysis()),
])

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(pipe, X_feat, y, cv=cv)
print(f"LDA CV: {scores.mean()*100:.1f}% ± {scores.std()*100:.1f}%")
```

---

## 7. 本章小结

| 步骤 | 方法 | 要点 |
|------|------|------|
| 特征提取 | 时域均值 / 滑动窗口 / CSP | 降维保留判别信息 |
| 分类器 | LDA / SVM / XGBoost | 少量样本优先 LDA |
| 交叉验证 | Stratified K-Fold | 避免过拟合 |
| 评估 | 混淆矩阵 / F1 / CV曲线 | 多维度衡量性能 |

---

## 参考文献

- Lotte et al. (2018). A review of classification algorithms for EEG-based brain-computer interfaces. *J. Neural Eng.*
- Blankertz et al. (2008). Optimizing spatial filters for robust EEG single-trial analysis. *IEEE SPM*
- MNE-Python: `mne.decoding` 模块文档
