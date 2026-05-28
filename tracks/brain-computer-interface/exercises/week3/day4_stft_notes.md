# 短时傅里叶变换（STFT）与时频分析

> 对应学习计划：Week 3 Day 4（STFT 时频分析）
> 前置知识：傅里叶变换（01）、频谱泄漏（02）、滤波（03）
> 最后更新：2026-05-18

---

## 1. FFT 的局限：丢失了时间信息

FFT 告诉你信号"包含哪些频率"，但**不告诉你这些频率什么时候出现**。

**类比**：FFT 就像一张全景照片 —— 看得清风景的构成（山、水、树），但不知道"太阳什么时候升起"。

**BCI 实例**：运动想象时 alpha 波功率下降（ERD），恢复时功率反弹（ERS）。用全段 FFT 只能看到"alpha 波存在"，看不到"运动想象时 alpha 功率下降"这个**时间动态**。

---

## 2. STFT 的核心思想

### 2.1 分帧 + 加窗 + FFT

把长信号切成一段一段（**帧**），对每帧做 FFT，得到每帧的频谱，按时间排列成二维图：

$$
X_{\text{STFT}}(m, \omega) = \sum_{n=0}^{N-1} x[n + mH] \cdot w[n] \cdot e^{-j\omega n}
$$

其中：
- $m$ = 帧编号（时间轴）
- $H$ = 帧移（hop size，相邻帧之间的偏移）
- $w[n]$ = 窗函数（汉宁窗等）
- $N$ = 帧长（nperseg）

### 2.2 类比理解

**STFT = 一本翻页动画书**：
- 每一页 = 一帧 = 对一小段时间做 FFT
- 翻页 = 时间推进
- 每页的内容 = 该时刻的频谱
- 合起来 = 频率随时间的变化

### 2.3 与频谱泄漏的关系

STFT 对每帧加窗再做 FFT，因此**每帧都存在频谱泄漏问题**（见 02-spectral-leakage.md）。选择窗函数时面临同样的主瓣宽度 vs 旁瓣衰减的权衡。

---

## 3. 时间-频率分辨率权衡（核心矛盾）

### 3.1 测不准原理

STFT 的根本限制来自信号处理版的测不准原理：

$$
\Delta t \cdot \Delta f \geq \frac{1}{4\pi}
$$

**时间分辨率和频率分辨率不可兼得！**

### 3.2 窗长的影响

| 窗长 $N$ | 时间分辨率 $\Delta t$ | 频率分辨率 $\Delta f$ | 效果 |
|----------|----------------------|----------------------|------|
| 长（512） | 差（$512/f_s$ 秒） | 好（$f_s/512$ Hz） | 看得清频率，看不清时间 |
| 短（64） | 好（$64/f_s$ 秒） | 差（$f_s/64$ Hz） | 看得清时间，看不清频率 |

以 $f_s = 250$ Hz 为例：

| nperseg | $\Delta t$ | $\Delta f$ | 适用场景 |
|---------|-----------|-----------|---------|
| 64 | 256 ms | 3.9 Hz | 捕捉快速事件，频率模糊 |
| 128 | 512 ms | 1.95 Hz | **BCI 折中方案** |
| 256 | 1024 ms | 0.98 Hz | 精确频率定位，时间模糊 |

### 3.3 类比理解

**STFT 窗长 = 相机快门速度**：
- 快门快（短窗）：冻结动作 → 时间清晰，但暗（频率信息少）
- 快门慢（长窗）：模糊动作 → 频率清晰，但时间糊了

### 3.4 为什么没有"最优窗长"

因为同一信号的不同成分可能需要不同分辨率：
- 低频成分（delta, theta）变化慢 → 需要长窗看频率
- 高频成分（gamma）变化快 → 需要短窗看时间

**这就是小波变换的动机**（Week 3 Day 5 内容）：小波自动在低频用长窗、高频用短窗。

---

## 4. 频谱图（Spectrogram）

### 4.1 定义

将 STFT 的结果 $|X_{\text{STFT}}(m, \omega)|^2$ 以二维热力图形式展示：

- **横轴** = 时间
- **纵轴** = 频率
- **颜色** = 功率（通常取 dB）

$$
S(m, f) = 10 \log_{10}|X_{\text{STFT}}(m, 2\pi f)|^2 \quad \text{(dB)}
$$

### 4.2 Python 代码

```python
from scipy import signal as sig

# 计算 STFT 频谱图
nperseg = 128       # 帧长
noverlap = 64       # 重叠（通常 = nperseg // 2）
freqs, times, Sxx = sig.spectrogram(
    eeg, fs=250,
    window='hann',   # 汉宁窗（BCI 默认）
    nperseg=nperseg,
    noverlap=noverlap,
    scaling='density'
)

# 转换为 dB
Sxx_dB = 10 * np.log10(Sxx + 1e-10)

# 绘制频谱图
plt.pcolormesh(times, freqs, Sxx_dB, shading='gouraud', cmap='viridis')
plt.colorbar(label='PSD (dB)')
plt.ylabel('Frequency (Hz)')
plt.xlabel('Time (s)')
```

### 4.3 帧移（hop size）与重叠

- **帧移** = 相邻帧起始点的距离 = `nperseg - noverlap`
- **重叠** = 相邻帧重叠的采样点数
- 通常设置 `noverlap = nperseg // 2`（50% 重叠）

50% 重叠的好处：
1. 更平滑的时间过渡
2. 减少信息丢失（窗函数边缘衰减部分的信号也能被覆盖）
3. 时间轴采样点翻倍

---

## 5. ERD/ERS：STFT 在 BCI 中的核心应用

### 5.1 什么是 ERD/ERS

| 缩写 | 全称 | 含义 |
|------|------|------|
| ERD | Event-Related Desynchronization | 事件相关去同步：特定频段功率**下降** |
| ERS | Event-Related Synchronization | 事件相关同步：特定频段功率**上升** |

**运动想象的典型模式**：
- 想象握拳 → 大脑运动皮层 alpha/beta 功率下降（ERD）
- 放松 → 功率恢复甚至反弹超过基线（ERS）

### 5.2 STFT 如何检测 ERD/ERS

1. 对 EEG 信号做 STFT，得到时频图
2. 在目标频段（如 alpha 8-13Hz）内取平均功率
3. 用**基线归一化**：$P_{\text{ERD}}(t) = P(t) - P_{\text{baseline}}$
4. 画功率随时间变化的曲线：
   - 低于 0 = ERD（功率下降）
   - 高于 0 = ERS（功率上升）

### 5.3 代码

```python
# 1. 计算 STFT
freqs, times, Sxx = sig.spectrogram(eeg, fs, window='hann', nperseg=128, noverlap=64)

# 2. 提取 alpha 频段功率
alpha_mask = (freqs >= 8) & (freqs <= 13)
alpha_power = np.mean(Sxx[alpha_mask], axis=0)
alpha_power_dB = 10 * np.log10(alpha_power + 1e-10)

# 3. 基线归一化（用事件前的静息段作为基线）
baseline = np.mean(alpha_power_dB[times < t_cue])
alpha_erd = alpha_power_dB - baseline

# 4. ERD < 0, ERS > 0
```

---

## 6. FFT vs STFT 对比

| 特性 | FFT | STFT |
|------|-----|------|
| 输出 | 一维频谱 | 二维时频图 |
| 时间信息 | ❌ 无 | ✅ 有 |
| 频率分辨率 | $\Delta f = f_s/N_{\text{总}}$（高） | $\Delta f = f_s/N_{\text{帧}}$（低） |
| 计算量 | $O(N \log N)$ | $O(K \cdot M \log M)$（$K$ 帧，$M$ 帧长） |
| 适用场景 | 稳态信号 | 非稳态信号（EEG） |
| 类比 | 全景照片 | 翻页动画 / 视频 |

**关键区别**：EEG 是非稳态信号（频谱随时间变化），所以 BCI 分析中 **STFT 比 FFT 更常用**。

---

## 7. 窗函数对 STFT 的影响

不同窗函数在 STFT 中的效果：

| 窗函数 | 频谱图效果 |
|--------|-----------|
| 矩形窗 (boxcar) | 频率分辨率最高，但时间方向有"竖纹"（旁瓣泄漏） |
| 汉宁窗 (hann) | **BCI 默认**，泄漏少，频率和时间平衡 |
| 海明窗 (hamming) | 类似汉宁窗，旁瓣略不均匀 |
| 布莱克曼窗 (blackman) | 泄漏最少，但频率分辨率最低 |

```python
# 不同窗函数的 STFT
for win in ['boxcar', 'hann', 'hamming', 'blackman']:
    freqs, times, Sxx = sig.spectrogram(eeg, fs, window=win, nperseg=128, noverlap=64)
```

---

## 8. BCI 中 STFT 的实战参数建议

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| 采样率 $f_s$ | 250-500 Hz | EEG 常用 |
| 帧长 nperseg | 128-256 | 折中时间/频率分辨率 |
| 重叠 noverlap | nperseg // 2 | 50% 重叠 |
| 窗函数 | hann | BCI 默认 |
| 频率范围 | 0-40 Hz | EEG 有用频段 |
| 显示方式 | dB 刻度 | 10 log₁₀(Sxx)，方便观察功率变化 |

---

## 9. 关键要点总结

1. **FFT 丢失时间信息 → STFT 用分帧+加窗+FFT 恢复时间维度**
2. **时间-频率分辨率不可兼得**：窗长 ↑ → 频率分辨率 ↑ 但时间分辨率 ↓
3. **频谱图**：横轴时间、纵轴频率、颜色=功率(dB)
4. **ERD/ERS**：STFT 检测事件相关功率变化的核心工具
5. **BCI 默认参数**：nperseg=128, noverlap=64, 窗=hann
6. **STFT 的局限**：固定窗长，无法同时兼顾高低频 → 小波变换是下一步
