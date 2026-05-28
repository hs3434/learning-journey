# Week 1 Day 1: NumPy Array Operations

## 核心概念

### 1. NumPy 数组基础

NumPy 是 Python 科学计算的基础库，核心是多维数组对象 `ndarray`。

```python
import numpy as np

# 创建数组
a = np.array([1, 2, 3, 4, 5])
b = np.zeros((3, 4))  # 3x4 全零矩阵
c = np.arange(0, 10, 2)  # 0-10，步长2
d = np.linspace(0, 1, 5)  # 0-1 等分5点
```

### 2. 数组索引与切片

```python
data = np.random.randn(16, 25600)  # (channels, samples)

# 基本索引
channel_0 = data[0]  # 获取第一通道
first_1000 = data[:, :1000]  # 所有通道前1000点

# 布尔索引
mask = data.mean(axis=1) > 0
selected = data[mask]
```

### 3. 广播机制 (Broadcasting)

NumPy 自动扩展数组维度进行运算：

```python
# 标量与数组
data_centered = data - data.mean(axis=1, keepdims=True)

# shape: (16, 25600) - (16, 1) → 自动广播
```

### 4. 向量化操作

```python
# EEG 滤波后的 RMS 计算
def compute_rms(channels_data):
    return np.sqrt(np.mean(channels_data**2, axis=1))

# 频域特征提取
freqs = np.fft.fftfreq(n_samples, 1/fs)
power = np.abs(np.fft.fft(data))**2
```

## EEG 数据处理应用

### 典型 EEG shape

```
Raw data: (n_channels, n_times)
           e.g., (64, 25600) = 64通道 @ 256Hz × 100秒

Epochs:   (n_epochs, n_channels, n_times)
           e.g., (100, 64, 513) = 100个epoch

Trials:   (n_trials, n_channels, n_times)
```

### 数据整形

```python
# 将连续数据分割为 trials
n_channels, n_times = data.shape
n_trials = 10
trial_len = n_times // n_trials

trials = data.reshape(n_channels, n_trials, trial_len)
# shape: (n_channels, n_trials, trial_len)
```

## 练习要点

1. 掌握数组创建、索引、切片
2. 理解广播机制，避免显式循环
3. 练习向量化解题（EEG 统计量计算）

## 关键函数

| 函数 | 用途 |
|------|------|
| `np.array()` | 创建数组 |
| `np.mean(axis)` | 按轴求均值 |
| `np.std(axis)` | 按轴求标准差 |
| `np.reshape()` | 改变形状 |
| `np.dot()` | 矩阵乘法 |

## 参考资料

- [NumPy 官方文档](https://numpy.org/doc/)
- [NumPy 广播规则](https://numpy.org/doc/stable/user/basics.broadcasting.html)