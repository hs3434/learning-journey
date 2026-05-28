# Week 5 Day 4: Motor Imagery and ERD/ERS

## 核心概念

### 1. 运动想象 (Motor Imagery)

运动想象激活感觉运动皮层：
- 左手想象 → 右侧 C3 区域 ERD
- 右手想象 → 左侧 C3 区域 ERD
- 双脚想象 → Cz 区域 ERD

### 2. ERD/ERS 模式

```python
# ERD 计算
def compute_erd(epochs, baseline=(-0.5, -0.2), target_band=(8, 13)):
    """计算事件相关去同步"""
    # 频段功率
    psd, freqs = compute_psd(epochs, fmin=target_band[0], fmax=target_band[1])

    # Baseline 功率
    baseline_idx = (freqs >= baseline[0]) & (freqs <= baseline[1])
    baseline_power = psd[:, :, baseline_idx].mean()

    # ERD (%)
    erd = 100 * (psd - baseline_power) / baseline_power
    return erd
```

### 3. CSP (共同空间模式)

最常用的 MI 特征提取：

```python
from mne.preprocessing import CSP

csp = CSP(n_components=4)
X_csp = csp.fit_transform(epochs.get_data(), labels)

# 然后用 LDA 分类
clf = LinearDiscriminantAnalysis()
scores = cross_val_score(clf, X_csp, labels, cv=5)
```

### 4. 时空特征

```python
# 空间模式（C3, Cz, C4 通道）
motor_channels = ['C3', 'Cz', 'C4']
epochs MI = epochs.pick(motor_channels)

# 特征：alpha/beta 功率比
def compute_mrpr(epochs):
    """Motor Related Power Ratio"""
    psd = epochs.compute_psd(fmin=8, fmax=30)
    alpha = psd[:, :, (8, 13)].mean()
    beta = psd[:, :, (13, 30)].mean()
    return alpha / (beta + 1e-8)
```

## MI 实验设计

```python
# 典型 MI 实验
protocol = {
    'cue_duration': 1.5,  # 提示
    'mi_duration': 4.0,   # 想象
    'rest_duration': 2.0,  # 休息
    'n_trials': 100
}
```

## 练习要点

1. 理解 MI 的 ERD/ERS 机制
2. 掌握 CSP 特征提取
3. 学会设计 MI 实验

## 参考资料

- [CSP 文档](https://mne.tools/stable/generated/mne.preprocessing.CSP.html)
- [MI 综述](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3578369/)