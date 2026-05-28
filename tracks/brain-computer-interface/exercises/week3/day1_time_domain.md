# Week 3 Day 1: Time Domain Analysis

## 核心概念

### 1. 时域统计量

EEG 时域分析关注信号的统计特征：

```python
import numpy as np

# 基础统计
mean = np.mean(data, axis=1)      # 均值
variance = np.var(data, axis=1)   # 方差
std = np.std(data, axis=1)        # 标准差

# RMS (Root Mean Square)
rms = np.sqrt(np.mean(data**2, axis=1))

# 峰值
peak = np.max(np.abs(data), axis=1)
peak_to_peak = np.max(data, axis=1) - np.min(data, axis=1)
```

### 2. 滑动窗口统计

```python
def sliding_window_stats(data, fs, window_sec=0.5, hop_sec=0.25):
    window_size = int(fs * window_sec)
    hop_size = int(fs * hop_sec)

    n_windows = (len(data) - window_size) // hop_size + 1

    means = np.zeros(n_windows)
    stds = np.zeros(n_windows)

    for i in range(n_windows):
        start = i * hop_size
        end = start + window_size
        window = data[start:end]
        means[i] = window.mean()
        stds[i] = window.std()

    return means, stds
```

### 3. 通道间相关性

```python
# 相关系数矩阵
corr_matrix = np.corrcoef(data)

# 时延估计（互相关）
lag = np.argmax(np.correlate(signal1, signal2, mode='full'))
```

## EEG 典型值

| 频段 | 幅度范围 | 说明 |
|------|----------|------|
| Alpha | 10-30 μV | 放松、闭眼 |
| Beta | 5-20 μV | 主动思考 |
| Theta | 5-10 μV | 困倦 |
| Delta | 10-20 μV | 深度睡眠 |

## 异常检测

```python
# Z-score 异常检测
z_scores = (data - data.mean(axis=0)) / (data.std(axis=0) + 1e-8)
outliers = np.where(np.abs(z_scores) > 3)
```

## 练习要点

1. 掌握时域统计量的计算
2. 理解 RMS 和峰值的区别
3. 学会滑动窗口分析

## 参考资料

- [NumPy 统计函数](https://numpy.org/doc/stable/reference/routines.statistics.html)