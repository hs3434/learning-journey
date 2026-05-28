# Week 1 Day 3: SciPy Statistics and Signal Basics

## 核心概念

### 1. SciPy 信号处理基础

```python
from scipy import signal, stats
import numpy as np
```

### 2. 常用统计函数

```python
# 基础统计
mean = np.mean(data)
std = np.std(data)
variance = np.var(data)

# SciPy 额外统计
skewness = stats.skew(data)    # 偏度
kurtosis = stats.kurtosis(data)  # 峰度

# 概率分布拟合
from scipy.stats import norm
mu, sigma = norm.fit(data)  # 高斯拟合
```

### 3. 滤波基础

```python
# 设计 Butterworth 带通滤波器
fs = 256
nyq = fs / 2
low = 0.5 / nyq  # 归一化频率
high = 40 / nyq

b, a = signal.butter(4, [low, high], btype='band')
filtered = signal.filtfilt(b, a, data)
```

### 4. 卷积与相关

```python
# 卷积
smoothed = np.convolve(data, window, mode='same')

# 互相关（时延估计）
correlation = np.correlate(signal1, signal2, mode='full')
```

### 5. 插值

```python
from scipy.interpolate import interp1d

f = interp1d(t_old, data_old, kind='cubic')
data_new = f(t_new)
```

## EEG 应用场景

### 1. 异常值检测

```python
# 基于统计的异常检测
z_scores = np.abs(stats.zscore(data))
outliers = np.where(z_scores > 3)
```

### 2. 信号平滑

```python
# 滑动平均
windowed = np.convolve(data, np.ones(5)/5, mode='same')

# Savitzky-Golay 滤波
from scipy.signal import savgol_filter
smoothed = savgol_filter(data, window_length=11, polyorder=3)
```

## 练习要点

1. 掌握滤波器的设计（butter, cheby, ellip）
2. 理解 filtfilt 零相位滤波
3. 练习卷积/相关的使用场景

## 关键函数

| 函数 | 用途 |
|------|------|
| `signal.butter()` | 设计 Butterworth 滤波器 |
| `signal.filtfilt()` | 零相位滤波 |
| `signal.convolve()` | 卷积 |
| `stats.zscore()` | Z-score 标准化 |
| `interp1d()` | 一维插值 |

## 参考资料

- [SciPy 信号处理](https://docs.scipy.org/doc/scipy/reference/signal.html)
- [滤波设计教程](https://docs.scipy.org/doc/scipy/tutorial/signal.html)