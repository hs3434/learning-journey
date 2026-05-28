# Week 1 Day 5: Comprehensive EEG Processing

## 今日目标

综合运用 Week 1 所学，完成一个完整的 EEG 数据处理流程。

## 流程概览

```
Raw EEG → 预处理 → Epochs → 可视化 → 导出
```

## 完整示例

### 1. 数据加载

```python
import mne
import numpy as np
import pandas as pd

# 加载 MNE 示例数据
sample_data = mne.datasets.sample.data_path()
raw = mne.io.read_raw_fif(
    sample_data / 'MEG' / 'sample' / 'sample_audvis_raw.fif',
    preload=True
)
raw.pick('eeg')
```

### 2. 预处理

```python
# 带通滤波
raw.filter(l_freq=0.5, h_freq=40)

# Notch 滤波（去除工频）
raw.notch_filter(freqs=50)
```

### 3. Epochs 创建

```python
events = mne.find_events(raw, stim_channel='STI 014')

epochs = mne.Epochs(
    raw, events,
    event_id={'auditory/left': 1, 'auditory/right': 2},
    tmin=-0.2, tmax=0.5,
    baseline=(-0.2, 0),
    preload=True
)
```

### 4. 可视化

```python
# PSD
raw.compute_psd().plot()

# Evoked
evoked = epochs['auditory/left'].average()
evoked.plot()
```

### 5. 数据导出

```python
# DataFrame
df = epochs.to_data_frame()

# NumPy 数组
data = epochs.get_data()
```

## 常见问题

### Q: 为什么先滤波再重参考？
A: 滤波是频率操作，重参考是空间操作。顺序不影响结果，但通常滤波在前更稳定。

### Q: 如何选择 baseline？
A: 通常用事件前 200ms (-0.2 to 0) 或 (-0.1, 0)。确保baseline期间无明显事件。

## 练习要点

1. 串联所有学过的工具
2. 理解 MNE 数据结构（Raw → Epochs → Evoked）
3. 练习完整的数据处理流程

## 参考资料

- [MNE-Python 教程](https://mne.tools/stable/documentation.html)
- [EEG 处理完整流程](https://mne.tools/stable/auto_tutorials/intro/plot_30_filtering_resampling.html)