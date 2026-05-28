# Week 3 Day 5: Wavelet Transform and ICA

## 核心概念

### 1. 小波变换

```python
from scipy.signal import cwt, morlet2

# 连续小波变换
 widths = np.arange(1, 128)
 cwt_matrix = cwt(data, morlet2, widths)

# MNE 中的小波分析
 from mne.time_frequency import tfr_multitaper
 tfr = tfr_multitaper(epochs, freqs=np.arange(1, 40), n_cycles=5)
```

### 2. ICA 独立成分分析

去除眼动、肌肉伪迹：

```python
from mne.preprocessing import ICA

ica = ICA(n_components=20, random_state=42)
ica.fit(raw)

# 识别眼动成分（通常在前几个）
ica.plot_sources(raw)

# 去除眼动成分
ica.exclude = [0, 1]  # 眼动成分索引
raw_clean = raw.copy()
ica.apply(raw_clean)
```

### 3. 去伪迹策略

| 伪迹类型 | 特征 | 处理方法 |
|----------|------|----------|
| 眼动 | 低频慢波 | ICA, 回归 |
| 眨眼 | 高 amplitude | ICA |
| 肌肉 | 高频 gamma | 陷波滤波 |
| 工频 | 50Hz | Notch 滤波 |

### 4. 伪迹检测

```python
# 幅值阈值
reject_criteria = dict(eeg=150e-6)  # 150 μV

# 峰间幅度
epochs.drop_bad(reject=reject_criteria)
```

## ICA 在 EEG 中的应用

```python
# 1. 拟合 ICA
ica = ICA(n_components=15, method='fastica')
ica.fit(raw, picks='eeg')

# 2. 可视化成分
ica.plot_components()

# 3. 标记伪迹成分
ica.plot_sources(raw)  # 手动标记

# 4. 去除
ica.exclude = [0]  # 眼动
ica.apply(raw)
```

## 练习要点

1. 理解小波变换的时频特性
2. 掌握 ICA 的标准用法
3. 学会识别和去除伪迹

## 参考资料

- [MNE ICA](https://mne.tools/stable/generated/mne.preprocessing.ICA.html)
- [小波变换](https://mne.tools/stable/auto_tutorials/time-frequency/plot_tutorial_wavelet.html)