# Week 4 Day 5: Decoding Pipeline

## 核心概念

### 1. 特征提取

```python
def extract_features(epochs_data):
    """提取统计特征"""
    n_epochs, n_channels, n_times = epochs_data.shape
    features = []

    for epoch in epochs_data:
        epoch_features = []

        # 时域特征
        epoch_features.append(epoch.mean(axis=1))   # 均值
        epoch_features.append(epoch.max(axis=1))   # 最大值
        epoch_features.append(epoch.min(axis=1))   # 最小值
        epoch_features.append(np.std(epoch, axis=1))  # 标准差

        # 频域特征（alpha 功率）
        from mne.time_frequency import psd_arrayWelch
        psd, _ = psd_arrayWelch(epoch, sfreq=256, fmin=8, fmax=13)
        epoch_features.append(psd.mean(axis=1))

        features.append(np.concatenate(epoch_features))

    return np.array(features)
```

### 2. 分类器训练

```python
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import cross_val_score, StratifiedKFold

# 准备数据
X = extract_features(epochs.get_data())
y = epochs.events[:, 2]

# 分类器
clf = LinearDiscriminantAnalysis()

# 交叉验证
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(clf, X, y, cv=cv)

print(f"准确率: {scores.mean():.3f} ± {scores.std():.3f}")
```

### 3. 完整 Pipeline

```python
class MNEDecoder:
    def __init__(self, raw, events, event_id):
        self.raw = raw
        self.events = events
        self.event_id = event_id
        self.epochs = None
        self.clf = LinearDiscriminantAnalysis()

    def preprocess(self):
        self.raw.filter(0.5, 40)
        self.raw.set_eeg_reference('average')

    def create_epochs(self, tmin=-0.2, tmax=0.5):
        self.epochs = mne.Epochs(
            self.raw, self.events, self.event_id,
            tmin=tmin, tmax=tmax,
            baseline=(tmin, 0),
            preload=True
        )

    def decode(self):
        X = self.extract_features(self.epochs.get_data())
        y = self.epochs.events[:, 2]
        scores = cross_val_score(self.clf, X, y, cv=5)
        return scores.mean(), scores.std()
```

## 评估指标

| 指标 | 说明 |
|------|------|
| 准确率 | 正确分类比例 |
| kappa | 考虑随机的一致性 |
| ITR | 信息传输率 (bits/min) |

## 练习要点

1. 掌握特征提取方法
2. 学会使用 LDA 分类器
3. 理解交叉验证评估

## 参考资料

- [MNE 分类](https://mne.tools/stable/auto_tutorials/machine-learning/plot_decoding.html)
- [scikit-learn LDA](https://scikit-learn.org/stable/modules/generated/sklearn.discriminant_analysis.LinearDiscriminantAnalysis.html)