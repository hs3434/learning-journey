# Week 3 Day 4: STFT Time-Frequency Analysis

## 核心概念

### 1. 短时傅里叶变换 (STFT)

```python
from scipy.signal import stft

fs = 256
f, t, Zxx = stft(data, fs=fs, nperseg=256, noverlap=192)

# 计算功率谱
power = np.abs(Zxx) ** 2

# 可视化
plt.pcolormesh(t, f, 10 * np.log10(power))
```

### 2. 窗口大小选择

| 窗口长度 | 频率分辨率 | 时间分辨率 |
|----------|------------|------------|
| 小 (32-128) | 差 | 好 |
| 大 (512-1024) | 好 | 差 |

```python
# 高时间分辨率
f1, t1, Zxx1 = stft(data, fs=fs, nperseg=64)

# 高频率分辨率
f2, t2, Zxx2 = stft(data, fs=fs, nperseg=512)
```

### 3. noverlap 参数

`noverlap` 控制相邻窗口重叠：

```python
stft(data, fs=fs, nperseg=256, noverlap=192)  # 75% 重叠
```

### 4. 事件相关频谱分析 (ERSA)

```python
# 对多个事件周围的频谱平均
tfr_matrix = []
for epoch in epochs:
    f, t, Zxx = stft(epoch, fs=fs, nperseg=64)
    tfr_matrix.append(np.abs(Zxx)**2)

tfr_average = np.mean(tfr_matrix, axis=0)
```

## 频谱图可视化

```python
plt.figure(figsize=(14, 5))
plt.pcolormesh(t, f, 10 * np.log10(power + 1e-12),
               shading='gouraud', cmap='magma')
plt.colorbar(label='Power (dB)')
plt.axvline(0, color='white', linestyle='--')  # 事件时刻
plt.ylabel('Frequency (Hz)')
plt.xlabel('Time (s)')
```

## 练习要点

1. 理解时频分辨率的权衡
2. 掌握 STFT 的使用
3. 学会绘制频谱图

## 参考资料

- [SciPy STFT](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.stft.html)