# Week 3 Day 2: Frequency Domain Analysis

## 核心概念

### 1. FFT 基础

```python
import numpy as np

n = len(data)
fft_result = np.fft.fft(data)
freqs = np.fft.fftfreq(n, 1/fs)

# 只取正频率
positive_mask = freqs >= 0
magnitude = np.abs(fft_result)[positive_mask]
```

### 2. 功率谱密度 (PSD)

使用 Welch 方法估计 PSD，更平滑：

```python
from scipy.signal import welch

fs = 256
freqs, psd = welch(data, fs, nperseg=256)
```

### 3. 频段功率

```python
bands = {
    'Delta': (0.5, 4),
    'Theta': (4, 8),
    'Alpha': (8, 13),
    'Beta': (13, 30),
    'Gamma': (30, 100)
}

band_powers = {}
for band_name, (low, high) in bands.items():
    mask = (freqs >= low) & (freqs <= high)
    band_powers[band_name] = np.mean(psd[mask])
```

### 4. 时频分析

```python
from scipy.signal import spectrogram

f, t, Sxx = spectrogram(data, fs, nperseg=256, noverlap=128)
```

## EEG 频段特征

| 频段 | 频率范围 | 关联状态 |
|------|----------|----------|
| Delta | 0.5-4 Hz | 深度睡眠 |
| Theta | 4-8 Hz | 困倦、冥想 |
| Alpha | 8-13 Hz | 放松、闭眼 |
| Beta | 13-30 Hz | 清醒、主动思考 |
| Gamma | 30-100 Hz | 认知活动 |

## 频谱图可视化

```python
import matplotlib.pyplot as plt

plt.figure(figsize=(14, 5))
plt.pcolormesh(t, f, 10 * np.log10(Sxx), shading='gouraud')
plt.colorbar(label='Power (dB)')
plt.ylabel('Frequency (Hz)')
plt.xlabel('Time (s)')
```

## 练习要点

1. 理解 FFT 和 PSD 的区别
2. 掌握 Welch 方法
3. 学会计算各频段功率

## 参考资料

- [SciPy FFT](https://docs.scipy.org/doc/scipy/reference/tutorial/fft.html)
- [功率谱密度](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html)