# Week 3 Day 3: Digital Filtering

## 核心概念

### 1. 滤波器类型

```python
from scipy.signal import butter, cheby, ellip

# Butterworth (最平坦)
b, a = butter(order, [low, high], btype='band')

# Chebyshev (更陡峭但有纹波)
b, a = cheby(order, ripple, [low, high], btype='band')

# Elliptic (最陡峭)
b, a = ellip(order, ripple, stop_db, [low, high], btype='band')
```

### 2. 零相位滤波

```python
filtered = signal.filtfilt(b, a, data)
```

`filtfilt` 比 `lfilter` 更好：
- 零相位偏移
- 前后滤波消除相位畸变

### 3. 滤波器设计参数

```python
fs = 256
nyq = fs / 2

# 带通滤波
lowcut = 0.5
highcut = 40
b, a = butter(4, [lowcut/nyq, highcut/nyq], btype='band')

# Notch 陷波滤波 (去除工频)
notch_freq = 50
Q = 30  # 品质因子
b, a = butter(4, [notch_freq/nyq - 1/nyq, notch_freq/nyq + 1/nyq], btype='band')
# 或使用 iirnotch
b, a = iirnotch(notch_freq/nyq, Q)
```

### 4. 滤波器的频率响应

```python
w, h = signal.freqz(b, a)
freqs_hz = w * fs / (2 * np.pi)

plt.figure()
plt.semilogy(freqs_hz, np.abs(h))
plt.xlabel('Frequency (Hz)')
plt.ylabel('Magnitude')
```

## 常见应用

### 预处理流程

```python
# 1. 带通滤波 (0.5-40Hz)
raw.filter(l_freq=0.5, h_freq=40)

# 2. 工频陷波 (50Hz)
raw.notch_filter(freqs=50)

# 3. 重参考
raw.set_eeg_reference('average')
```

## 练习要点

1. 理解 IIR vs FIR
2. 掌握 butterworth 滤波器设计
3. 学会去除工频干扰

## 参考资料

- [SciPy 滤波](https://docs.scipy.org/doc/scipy/reference/signal.html)
- [MNE 滤波](https://mne.tools/stable/auto_tutorials/intro/plot_30_filtering_resampling.html)