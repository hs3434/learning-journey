# Week 4 Day 1: MNE-Python Basics

## 核心概念

### 1. MNE 数据结构

```
Raw → Epochs → Evoked
```

| 结构 | 说明 | Shape |
|------|------|-------|
| Raw | 连续数据 | (n_channels, n_times) |
| Epochs | 分段数据 | (n_epochs, n_channels, n_times) |
| Evoked | 平均数据 | (n_channels, n_times) |

### 2. 加载数据

```python
import mne

# 加载 FIF 文件
raw = mne.io.read_raw_fif('data.fif', preload=True)

# 加载 EDF 文件
raw = mne.io.read_raw_edf('data.edf', preload=True)

# 查看信息
print(raw.info)
print(f"通道: {raw.ch_names}")
print(f"采样率: {raw.info['sfreq']} Hz")
print(f"时长: {raw.times[-1]:.1f} 秒")
```

### 3. 基本操作

```python
# 选择通道
raw.pick('eeg')
raw.pick(['EEG 001', 'EEG 002'])

# 获取数据
data = raw.get_data()
data = raw.get_data(picks='eeg', start=0, stop=1000)
```

### 4. 转换为 DataFrame

```python
df = raw.to_data_frame()
print(df.head())
```

## 数据结构转换

```python
# Raw → DataFrame
df = raw.to_data_frame(index=True, scale_time=1000)

# Epochs → DataFrame
df = epochs.to_data_frame(index=True)

# Evoked → DataFrame
df = evoked.to_data_frame(index=True)
```

## 练习要点

1. 理解 Raw/Epochs/Evoked 的关系
2. 掌握数据加载方法
3. 学会查看数据结构信息

## 参考资料

- [MNE 文档](https://mne.tools/stable/)
- [MNE 数据结构](https://mne.tools/stable/auto_tutorials/raw/plot_30_reading_raw_data.html)