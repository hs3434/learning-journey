# Week 1 Day 4: Matplotlib Visualization

## 核心概念

### 1. 基本绘图

```python
import matplotlib.pyplot as plt
import numpy as np

plt.figure(figsize=(14, 5))
plt.plot(t, data, linewidth=0.5)
plt.xlabel('Time (s)')
plt.ylabel('Amplitude (μV)')
plt.title('EEG Channel 0')
plt.tight_layout()
plt.savefig('eeg.png', dpi=150)
```

### 2. 多子图

```python
fig, axes = plt.subplots(3, 1, figsize=(14, 10))

for i in range(3):
    axes[i].plot(t, data[i], linewidth=0.3)
    axes[i].set_ylabel(f'Ch {i}')

axes[-1].set_xlabel('Time (s)')
```

### 3. 特殊图表类型

```python
# 散点图
plt.scatter(x, y, s=1, alpha=0.5)

# 直方图
plt.hist(data, bins=100, alpha=0.7)

# 图像热力图
plt.imshow(data, aspect='auto', cmap='viridis')
```

### 4. 样式与布局

```python
# 主题设置
plt.style.use('seaborn-v0_8-darkgrid')

# 图例
plt.legend(loc='upper right')

# 网格
plt.grid(True, alpha=0.3)
```

## EEG 可视化实战

### 多通道瀑布图

```python
n_channels = 16
offset = 50

for i in range(n_channels):
    plt.plot(t, data[i] * 1e6 + i * offset, linewidth=0.3, label=f'Ch {i}')
```

### PSD 对比图

```python
from scipy.signal import welch

fs = 256
freqs, psd = welch(data, fs, nperseg=256)

plt.semilogy(freqs, psd)
plt.xlabel('Frequency (Hz)')
plt.ylabel('Power/Frequency')
```

## 练习要点

1. 掌握 subplots 多子图布局
2. 学会选择合适的图表类型（时域/频域/统计）
3. 练习导出高质量图像

## 关键函数

| 函数 | 用途 |
|------|------|
| `plt.plot()` | 线图 |
| `plt.scatter()` | 散点图 |
| `plt.hist()` | 直方图 |
| `plt.imshow()` | 热力图 |
| `plt.subplots()` | 多子图 |
| `fig.savefig()` | 保存图像 |

## 参考资料

- [Matplotlib 教程](https://matplotlib.org/stable/tutorials/index.html)
- [EEG 可视化示例](https://mne.tools/stable/tutorials/visualization/plot_visualize_raw.html)