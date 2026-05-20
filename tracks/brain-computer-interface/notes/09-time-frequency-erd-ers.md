# Week 4 Day 4：时频分析 + ERD/ERS

## 1. 为什么要时频分析？

**问题**：FFT 只告诉我们信号里"有哪些频率"，但丢失了"这些频率什么时候出现"的信息。

EEG 是非稳态信号——频率成分随时间变化。运动想象任务中，alpha 节律在运动开始后能量下降（ERD），结束后反弹（ERS）。

**解决方案**：
- **STFT**：加窗截断 + 滑窗 FFT
- **小波变换**：用频率相关的窄/宽窗口自适应捕捉不同时频特征

---

## 2. STFT（短时傅里叶变换）

### 核心思想

对信号加一个固定窗口，在窗口内做 FFT；窗口沿时间轴滑动，得到"时-频-功率"三维图。

```python
from scipy import signal
import numpy as np

# STFT
f, t, Zxx = signal.stft(
    eeg_data,           # (n_channels, n_times) 或 (n_times,)
    fs=250,             # 采样率 Hz
    nperseg=128,        # 窗口长度（点数）
    noverlap=64,        # 重叠点数
    padded=True
)
# f: 频率轴 (nperseg//2 + 1,)
# t: 时间轴 (n_time_steps,)
# Zxx: 复数时频表示 (n_freqs, n_times)
power = np.abs(Zxx) ** 2  # 功率
```

### 窗口大小与频率分辨率的矛盾

| 窗口长度 | 频率分辨率 Δf = fs/nperseg | 时间分辨率 Δt = nperseg/fs | 适合 |
|---------|--------------------------|--------------------------|------|
| 短（32 点）| 粗（~7.8 Hz） | 高（~0.13 s） | 高频瞬态事件 |
| 长（256 点）| 细（~1 Hz） | 低（~1 s） | 低频稳态节律 |

**物理直觉**：低频节律变化慢，需要宽窗口才能累积足够周期来测量频率；高频事件来去都快，需要窄窗口捕捉时间精度。

### 频谱图（Spectrogram）

`signal.spectrogram()` 是 `signal.stft()` 的功率图封装：

```python
f, t, Sxx = signal.spectrogram(
    eeg_data, fs=250,
    nperseg=128, noverlap=96
)
plt.pcolormesh(t, f, 10 * np.log10(Sxx), shading='gouraud')
plt.ylabel('Frequency [Hz]')
plt.xlabel('Time [s]')
plt.title('Spectrogram (dB scale)')
```

---

## 3. 小波变换（Continuous Wavelet Transform, CWT）

### 核心思想

用一系列频率不同的"小波基函数"与信号做卷积。小波基 = 一个母小波的拉伸/压缩版本：

$$\psi_{a,b}(t) = \frac{1}{\sqrt{a}} \psi\left(\frac{t-b}{a}\right)$$

- $a$：尺度（scale）→ 控制频率（$a$ 大 → 频率低）
- $b$：平移 → 控制时间位置

### Morlet 小波（EEG 最常用）

```python
import mne
from mne.time_frequency import tfr_morlet

# 计算 TFR（时频表示）
freqs = np.linspace(8, 30, 20)        # 感兴趣频段：8-30 Hz
n_cycles = freqs / 2                  # 每个频率的周期数（经验值）
power, itc = tfr_morlet(
    epochs,           # mne.Epochs 对象
    freqs=freqs,
    n_cycles=n_cycles,
    return_itc=True,  # 同时返回 ITC（相位锁定了成分）
    decim=3
)
# power: Baseline-corrected power (epochs × freq × times)
```

**n_cycles 的物理含义**：
- n_cycles = 频率 / 2 → 半功率带宽约 ±25%，是时频分辨率的折中
- n_cycles ↑ → 频率精度 ↑，时间精度 ↓

---

## 4. ERD/ERS 原理

### 定义

- **ERD（Event-Related Desynchronization）**：事件后某个频段的能量**低于**基线（能量下降）
- **ERS（Event-Related Synchronization）**：事件后某个频段的能量**高于**基线（能量反弹）

### 公式

$$\text{ERD/ERS}(f, t) = \frac{P_{\text{trial}}(f, t) - P_{\text{baseline}}(f)}{P_{\text{baseline}}(f)} \times 100\%$$

- $P_{\text{baseline}}$：事件前的平均功率（通常取 t ∈ [-0.5, 0] s）
- 正值 → ERS；负值 → ERD
- 单位：百分比（%）

### 典型模式

| 频段 | 频率范围 | 运动想象时 | 备注 |
|------|---------|-----------|------|
| Mu (μ) | 8-12 Hz | ERD（对侧半球）| 中央前回 alpha 节律 |
| Beta (β) | 13-30 Hz | ERD + ERS | 运动后反弹明显 |
| Gamma (γ) | 30-100 Hz | ERS | 与认知加工相关 |
| Theta (θ) | 4-7 Hz | ERS | 记忆负荷相关 |

### 运动想象的 ERD/ERS 时序

```
mu ERD: -0.5s → 0s 开始，持续到运动后 1-2s
mu ERS: 运动结束后 1-3s 反弹
beta ERD: 运动开始时出现，比 mu 更短暂
```

---

## 5. GFP 在时频域的扩展

时域 GFP = $\sqrt{\frac{1}{N}\sum_i (x_i - \bar{x}_i)^2}$（通道间方差）

时频 GFP = 对所有通道的时频功率取 RMS（或平均）：

$$GFP_{tf}(t, f) = \sqrt{\frac{1}{N}\sum_{i=1}^N (P_i(t, f) - \bar{P}(t, f))^2}$$

这样可以直接看到"全脑同步活动强度"的时频动态。

---

## 6. MNE-Python TFR 可视化

### 时频图（功率地形图网格）

```python
import mne
from mne.time_frequency import tfr_morlet
import matplotlib.pyplot as plt

# 计算 TFR
freqs = np.logspace(*np.log10([8, 30]), num=30)  # 对数间隔更合理
n_cycles = freqs / 2
power, itc = tfr_morlet(epochs, freqs=freqs, n_cycles=n_cycles,
                         return_itc=True, decim=5)

# 绘图选项 1：多通道时频曲线
fig = power.plot(picks=['C3', 'Cz', 'C4'],
                  baseline=(None, 0), mode='percent',
                  title='ERD/ERS at C3/Cz/C4')

# 绘图选项 2：地形图时间序列（类似 Evoked 的拓扑版）
# 在特定频段内取平均，绘制多个时间点的脑地形图
power.plot_topomap(tmin=0.0, tmax=0.5, fmin=8, fmax=12,
                    baseline=(None, 0), mode='percent',
                    title='Alpha ERD (8-12 Hz)')
```

### 基线校正模式

```python
# mode 参数决定基线校正方式
power.plot(..., baseline=(None, 0), mode='percent')   # 百分比变化（推荐）
power.plot(..., baseline=(None, 0), mode='zscore')    # Z-score（跨频段可比）
power.plot(..., baseline=(None, 0), mode='mean')      # 减均值不除标准差
```

---

## 7. 统计检验：Bootstrap + 显著性掩码

时频分析后需要判断哪些像素是"显著"的：

```python
from mne.stats import bootstrap_confidence_interval

# 对每个 (freq, time) 像素做 bootstrap
# epochs_array: (n_epochs, n_channels, n_freqs, n_times)
# 先 average across epochs → (n_channels, n_freqs, n_times)
# 再 pick 一个通道

# MNE 内置方法对 TFR 做统计
# 使用 mne.time_frequency.tfr_morlet + mne.stats.permutation_t_test
```

---

## 8. 本章小结

| 概念 | 核心要点 |
|------|---------|
| STFT | 固定窗口，频率分辨率 = fs/nperseg，适合稳态信号 |
| 小波变换 | 自适应窗口，n_cycles 控制分辨率，高频时间好、低频频率好 |
| ERD/ERS | 相对基线的功率变化，正=ERS，负=ERD |
| 典型模式 | Mu/Beta ERD（运动想象），Alpha ERS（放松闭眼）|
| TFR 可视化 | 地形图网格 + 基线校正（mode='percent' 最常用）|

---

## 参考文献

- Pfurtscheller & Lopes da Silva (1999). Event-related EEG/MEG synchronization and desynchronization. *Clinical Neurophysiology*
- Cohen (2014). *Analyzing Neural Time Series Data* — 第 13-15 章
- MNE-Python: `mne.time_frequency` 模块文档
