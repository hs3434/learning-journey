# Motor Imagery (运动想象)

## 原理

运动想象激活感觉运动皮层，产生与实际运动相似的脑电变化模式。

### ERD/ERS 现象

- **ERD (Event-Related Desynchronization)**：事件相关去同步
  - Alpha/Beta 频段功率下降
  - 表示皮层激活

- **ERS (Event-Related Synchronization)**：事件相关同步
  - Alpha/Beta 频段功率上升
  - 表示皮层抑制

### 典型模式

| 想象动作 | 皮层区域 | ERD/ERS 模式 |
|----------|----------|--------------|
| 左手 | 对侧 C3 | ERD |
| 右手 | 对侧 C3 | ERD |
| 双脚 | Cz | ERD |
| 休息 | 感觉运动 | ERS |

## CSP (Common Spatial Pattern)

最常用的 MI 特征提取方法。

### 原理

最大化两类信号的方差差异：

```python
from mne.preprocessing import CSP

# 拟合 CSP
csp = CSP(n_components=4)
X_csp = csp.fit_transform(epochs.get_data(), labels)

# X_csp shape: (n_epochs, n_components)
```

### 使用流程

```python
# 1. 预处理
raw.filter(8, 30)  # 8-30 Hz
epochs = mne.Epochs(raw, events, event_id, tmin=-1, tmax=4)

# 2. 特征提取
csp = CSP(n_components=4)
X = csp.fit_transform(epochs.get_data(), labels)

# 3. 分类
clf = LinearDiscriminantAnalysis()
scores = cross_val_score(clf, X, labels, cv=5)
```

## 时频分析

```python
from mne.time_frequency import tfr_morlet

# 计算时频表征
freqs = np.arange(8, 30, 1)
tfr = tfr_morlet(epochs, freqs=freqs, n_cycles=5, return_itc=False)

# 可视化
tfr.plot(vmin=-100, vmax=100, cmap='RdBu_r')
```

## 实验设计

### cue-based 设计

```
 cue (1.5s) → MI (4s) → rest (2s)
    ↓
  提示方向
```

### 训练协议

```python
protocol = {
    'cue_duration': 1.5,     # 提示
    'mi_duration': 4.0,       # 想象
    'rest_duration': 2.0,     # 休息
    'n_trials': 100,          # 每类试次
    'inter_trial': 1.0       # 试次间隔
}
```

## 预处理

```python
# 标准 MI 预处理
raw.filter(8, 30)                    # 8-30 Hz
raw.notch_filter(50)                 # 去除工频
epochs = mne.Epochs(raw, events, tmin=-1, tmax=4)
epochs.decimate(4)                   # 下采样到 256Hz
epochs.drop_bad(reject=dict(eeg=100e-6))  # 去除坏 epoch
```

## 分类器

| 方法 | 精度 | 复杂度 |
|------|------|--------|
| LDA | 中高 | 低 |
| SVM | 高 | 中 |
| Deep Learning | 高 | 高 |

## 参考资料

- [MNE CSP](https://mne.tools/stable/generated/mne.preprocessing.CSP.html)
- [BCI Competition III MI](http://www.bbci.de/competition/iii/)
- [ERD/ERS 综述](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3578369/)