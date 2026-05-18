# 滤波（Filtering）

> 对应学习计划：Week 3 Day 3（滤波）
> 前置知识：傅里叶变换（见 01-fourier-transform.md）、频谱泄漏（见 02-spectral-leakage.md）
> 最后更新：2026-05-18

---

## 1. 为什么需要滤波

EEG 信号中混杂了大量不需要的成分：

| 成分 | 频率 | 性质 |
|------|------|------|
| 低频漂移 | < 0.5 Hz | 电极移动、出汗 |
| Alpha 波 | 8-13 Hz | 有用信号 |
| Beta 波 | 13-30 Hz | 有用信号 |
| 50Hz 工频 | 50 Hz | 电网干扰 |
| 高频噪声 | > 40 Hz | 肌电、仪器噪声 |

**滤波 = 频域上的"门禁"**：让目标频段通过，把干扰频段挡掉。

---

## 2. 两大滤波器家族：FIR vs IIR

### 2.1 定义

$$
y[n] = \underbrace{\sum_{k=0}^{M} b_k x[n-k]}_{\text{FIR 部分}} + \underbrace{\sum_{k=1}^{N} a_k y[n-k]}_{\text{IIR 反馈部分}}
$$

- **FIR（有限脉冲响应）**：$a_k = 0$，只用输入 $x$，不用输出 $y$ 的历史
- **IIR（无限脉冲响应）**：$a_k \neq 0$，输出反馈回来，形成递归

### 2.2 核心对比

| 特性 | FIR | IIR |
|------|-----|-----|
| 脉冲响应 | 有限长（$M+1$ 个采样点后归零） | 无限长（指数衰减但永远不为零） |
| 稳定性 | **天然稳定**（无反馈） | 可能不稳定（极点在单位圆外时） |
| 相位 | 可以做到**严格线性相位** | 非线性相位 |
| 阶数 | 需要较高阶数才能达到同样衰减 | 低阶就能实现陡峭过渡带 |
| 计算量 | 较大（阶数高） | 较小（阶数低） |
| 类比 | CNN 卷积（无记忆） | RNN（有隐状态反馈） |

### 2.3 类比理解

- **FIR = CNN**：只看当前和过去 $M$ 个输入，滑动窗口卷积。输出完全由输入决定，没有"记忆"。
- **IIR = RNN**：输出不仅依赖输入，还依赖之前的输出（隐状态），有"内部记忆"。

### 2.4 Python 代码

```python
from scipy import signal as sig

# IIR 带通滤波器（Butterworth, 4阶）
b_iir, a_iir = sig.butter(4, [0.5, 40.0], btype='band', fs=250)

# FIR 带通滤波器（101 阶 = 100 taps）
b_fir = sig.firwin(101, [0.5, 40.0], pass_zero='bandpass', fs=250)
```

---

## 3. filtfilt：零相位滤波

### 3.1 问题：lfilter 有相位延迟

用 `lfilter` 做一次前向滤波，信号会产生**相位移**（时域上表现为延迟）：

$$
y_1[n] = \text{lfilter}(b, a, x[n]) \quad \text{（有相位延迟）}
$$

### 3.2 解决：正反两次滤波

`filtfilt` 的核心思路：**前向滤波一次，再反向滤波一次**。

$$
y_2[n] = \text{lfilter}(b, a, y_1^{\text{reversed}}[n])^{\text{reversed}}
$$

- 第一次：信号延迟 $\phi$
- 第二次：信号又延迟 $\phi$，但方向相反 → $\phi + (-\phi) = 0$

### 3.3 filtfilt 的频率响应

单次滤波的幅度响应为 $|H(f)|$，filtfilt 两次滤波后：

$$
|H_{\text{filtfilt}}(f)| = |H(f)|^2
$$

- 通带衰减加倍（通带更平）
- 阻带衰减加倍（阻带更深）
- **代价**：过渡带变窄，但两次滤波让衰减更陡

### 3.4 代码对比

```python
# 有相位延迟（因果滤波，实时系统用）
y_lfilter = sig.lfilter(b, a, x)

# 零相位（非因果，离线分析用）
y_filtfilt = sig.filtfilt(b, a, x)
```

### 3.5 什么时候用哪个

| 场景 | 选择 | 原因 |
|------|------|------|
| 离线分析 EEG | `filtfilt` | 零相位，波形不失真 |
| 实时 BCI 系统 | `lfilter` | 因果性要求，不能"偷看"未来数据 |
| 实时 + 需要零相位 | FIR + 手动补偿群延迟 | 延迟固定可预测 |

---

## 4. 群延迟（Group Delay）

### 4.1 定义

群延迟是滤波器对信号各频率分量的**时间延迟**：

$$
\tau_g(\omega) = -\frac{d\phi(\omega)}{d\omega}
$$

其中 $\phi(\omega)$ 是滤波器的相位响应。

### 4.2 FIR 的群延迟

线性相位 FIR 滤波器的群延迟是**常数**：

$$
\tau_g = \frac{M}{2} \quad \text{（采样点）}
$$

其中 $M$ 是滤波器阶数。例如 100 阶 FIR，群延迟 = 50 个采样点。

这意味着所有频率分量被**均匀延迟**，波形形状不变，只是整体平移。

### 4.3 IIR 的群延迟

IIR 滤波器的群延迟是**频率的函数** $\tau_g(\omega)$：不同频率延迟不同 → 波形失真。

### 4.4 可视化

```python
# FIR 群延迟 = (numtaps - 1) / 2
group_delay = (numtaps - 1) / 2  # 采样点

# 手动补偿：将 lfilter 结果左移群延迟
y_compensated = np.roll(y_lfilter, -int(group_delay))
# 补偿后与 filtfilt 结果对齐
```

---

## 5. 频率响应 H(f)

### 5.1 定义

滤波器的频率响应 $H(f)$ 描述了它对每个频率分量的**幅度和相位**影响：

$$
H(f) = |H(f)| \cdot e^{j\phi(f)}
$$

- $|H(f)|$ = 幅度响应（每个频率通过多少）
- $\phi(f)$ = 相位响应（每个频率延迟多少）

### 5.2 dB 计算

工程上习惯用对数尺度（分贝）表示幅度响应：

$$
|H(f)|_{\text{dB}} = 20 \log_{10}|H(f)|
$$

| 线性幅度 $|H|$ | dB 值 | 含义 |
|---|---|---|
| 1.0 | 0 dB | 完全通过 |
| 0.707 | -3 dB | 半功率点（截止频率定义） |
| 0.1 | -20 dB | 衰减到 1/10 |
| 0.01 | -40 dB | 衰减到 1/100 |
| 0.001 | -60 dB | 衰减到 1/1000 |

### 5.3 Python 代码

```python
# 计算频率响应
w, h = sig.freqz(b, a, worN=2048, fs=fs)

# 转换为 dB
magnitude_dB = 20 * np.log10(np.abs(h) + 1e-10)

# 绘制
plt.plot(w, magnitude_dB)
plt.ylabel('Magnitude (dB)')
plt.xlabel('Frequency (Hz)')
```

---

## 6. Notch 滤波器（陷波滤波器）

### 6.1 用途

专门去除某个特定频率（如 50Hz 工频干扰），同时尽量不影响附近频率。

### 6.2 原理

在目标频率处放一个极窄的"深坑"：

$$
H(f_0) \approx 0 \quad \text{（在 50Hz 处几乎完全衰减）}
$$

$$
H(f \neq f_0) \approx 1 \quad \text{（其他频率几乎不受影响）}
$$

### 6.3 Q 因子

Q 因子控制"深坑"的宽度：

$$
\text{带宽} = \frac{f_0}{Q}
$$

- Q = 30, $f_0$ = 50Hz → 带宽 ≈ 1.67Hz（很窄，精准去除 50Hz）
- Q 越大 → 坑越窄越深 → 去除越精准，但对频率漂移越敏感

### 6.4 代码

```python
# IIR notch 滤波器
w0 = 50.0 / (fs / 2)  # 归一化频率
Q = 30                  # Q 因子
b_notch, a_notch = sig.iirnotch(w0, Q)

# 零相位滤波
eeg_clean = sig.filtfilt(b_notch, a_notch, eeg)
```

---

## 7. BCI 标准滤波流程

```
原始 EEG → 带通滤波 (0.5-40Hz) → Notch (50Hz) → 干净信号
```

**为什么要先带通再 notch？**

1. 带通先去掉低频漂移和高频噪声
2. Notch 精准去除 50Hz 工频
3. 顺序可以互换，但先带通可以让 notch 处理的信号更干净

### 7.1 完整代码

```python
from scipy import signal as sig

fs = 250  # 采样率

# 1. 带通滤波 (0.5-40Hz)
b_bp, a_bp = sig.butter(4, [0.5, 40.0], btype='band', fs=fs)
eeg_bp = sig.filtfilt(b_bp, a_bp, eeg_raw)

# 2. Notch 滤波 (50Hz)
b_notch, a_notch = sig.iirnotch(50.0 / (fs/2), Q=30)
eeg_clean = sig.filtfilt(b_notch, a_notch, eeg_bp)
```

---

## 8. BCI 常用滤波参数速查

| 目的 | 滤波器类型 | 参数 |
|------|-----------|------|
| 去低频漂移 | 高通 | 0.5 Hz 或 1 Hz |
| 去高频噪声 | 低通 | 40 Hz 或 50 Hz |
| Alpha 波提取 | 带通 | 8-13 Hz |
| Beta 波提取 | 带通 | 13-30 Hz |
| 去工频 | Notch | 50 Hz（中国）/ 60 Hz（美国），Q=30 |
| SSVEP 分析 | 带通 | 根据刺激频率调整 |

---

## 9. 关键要点总结

1. **FIR = CNN（卷积，无记忆），IIR = RNN（递归，有反馈）**
2. **离线分析用 `filtfilt`（零相位），实时系统用 `lfilter`（因果）**
3. **FIR 群延迟 = (阶数/2) 采样点，是常数；IIR 群延迟随频率变化**
4. **dB = 20 log₁₀(幅度)，-3dB = 半功率点 = 截止频率**
5. **BCI 标准流程：带通 0.5-40Hz → Notch 50Hz**
