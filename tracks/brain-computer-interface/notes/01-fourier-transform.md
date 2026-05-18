# 傅里叶变换：从时域到频域

> 对应学习计划：Week 3 Day 2（频域分析）
> 最后更新：2026-05-18

---

## 1. 核心思想

任何周期函数 $f(t)$ 都可以分解为不同频率的正弦和余弦波的叠加。

**类比**：白光通过棱镜分解成不同颜色的光 → 复杂信号通过傅里叶变换分解成不同频率的正弦波。

---

## 2. 傅里叶级数（周期信号 → 离散频谱）

### 2.1 基本公式

对于周期为 $T$ 的函数 $f(t)$，基波角频率 $\omega_0 = 2\pi/T$：

$$
f(t) = \frac{a_0}{2} + \sum_{n=1}^{\infty} \left[ a_n \cos(n\omega_0 t) + b_n \sin(n\omega_0 t) \right]
$$

### 2.2 三角函数正交性（推导的"魔法武器"）

在 $[-\pi, \pi]$ 上的积分：

$$
\int \cos(mx)\cos(nx)\,dx = \begin{cases} \pi & m=n \text{（同频相乘，能量累积）} \\ 0 & m\neq n \text{（不同频，相互抵消）} \end{cases}
$$

$$
\int \sin(mx)\sin(nx)\,dx = \begin{cases} \pi & m=n \\ 0 & m\neq n \end{cases}
$$

$$
\int \sin(mx)\cos(nx)\,dx = 0 \quad \text{永远为零（正弦和余弦正交）}
$$

**类比理解**：正交性 = 投影。$\cos(3\omega t)$ 和 $\cos(5\omega t)$ 是"垂直"的，求 $a_3$ 只需要 $f(t)$ 和 $\cos(3\omega t)$ 做内积，其他频率分量自动归零。

### 2.3 求系数

**求 $a_0$（直流分量）**：

等式两边对 $t$ 在一个周期上积分，正弦/余弦的完整周期积分 = 0：

$$
a_0 = \frac{1}{T} \int_T f(t)\,dt
$$

**求 $a_n$（余弦系数）**：

等式两边乘 $\cos(m\omega_0 t)$，再积分。正交性让其他项全部归零，只剩 $n=m$ 项：

$$
a_n = \frac{2}{T} \int_T f(t)\cos(n\omega_0 t)\,dt
$$

**求 $b_n$（正弦系数）**：同理

$$
b_n = \frac{2}{T} \int_T f(t)\sin(n\omega_0 t)\,dt
$$

**核心技巧**：乘一个基函数再积分，正交性让其他项全部归零，只剩你要的那一项。

### 2.4 复数形式（欧拉公式）

**欧拉公式**：

$$
e^{j\omega t} = \cos(\omega t) + j\sin(\omega t)
$$

$$
\cos(\omega t) = \frac{e^{j\omega t} + e^{-j\omega t}}{2}
$$

$$
\sin(\omega t) = \frac{e^{j\omega t} - e^{-j\omega t}}{2j}
$$

把 $\cos$ 和 $\sin$ 用 $e^{j\omega t}$ 替换，合并 $a_n$ 和 $b_n$：

$$
f(t) = \sum_{n=-\infty}^{+\infty} c_n \cdot e^{j n \omega_0 t}
$$

$$
c_n = \frac{1}{T} \int_T f(t) \cdot e^{-j n \omega_0 t}\,dt
$$

**$c_n$ 和 $a_n/b_n$ 的关系**：

$$
c_n = \frac{a_n - j b_n}{2} \quad (n > 0)
$$

$$
c_0 = \frac{a_0}{2}
$$

$$
c_{-n} = c_n^* \quad \text{（$c_n$ 的共轭）}
$$

复数形式更简洁：一个系数 $c_n$ 同时包含幅度和相位信息。

---

## 3. 傅里叶变换（非周期信号 → 连续频谱）

### 3.1 从级数到变换

傅里叶级数只适用于周期函数。非周期信号怎么办？

**思路**：把非周期信号看作"周期 $T \to \infty$"的周期信号。

$$
\text{当 } T \to \infty: \quad
\begin{cases}
\text{频率间隔 } \Delta f = 1/T \to 0 & \text{（离散变连续）} \\
\text{求和 } \Sigma \to \text{积分 } \int & \\
c_n \to F(\omega)\,d\omega & \text{（连续谱密度）}
\end{cases}
$$

### 3.2 傅里叶变换公式

$$
F(\omega) = \int_{-\infty}^{+\infty} f(t) \cdot e^{-j\omega t}\,dt \quad \text{（正变换：时域 → 频域）}
$$

$$
f(t) = \frac{1}{2\pi} \int_{-\infty}^{+\infty} F(\omega) \cdot e^{j\omega t}\,d\omega \quad \text{（逆变换：频域 → 时域）}
$$

### 3.3 物理意义

- $F(\omega)$ 告诉你信号在频率 $\omega$ 处有多强的成分
- $|F(\omega)|$ = 幅度谱（每个频率分量的强度）
- $\angle F(\omega)$ = 相位谱（每个频率分量的相位）

---

## 4. DFT / FFT（离散、有限长信号）

### 4.1 离散傅里叶变换

实际采样得到的是离散的、有限长的数据 $x[0], x[1], \ldots, x[N-1]$：

$$
X[k] = \sum_{n=0}^{N-1} x[n] \cdot e^{-j \frac{2\pi k n}{N}} \quad \text{（正变换）}
$$

$$
x[n] = \frac{1}{N} \sum_{k=0}^{N-1} X[k] \cdot e^{j \frac{2\pi k n}{N}} \quad \text{（逆变换）}
$$

### 4.2 FFT 频率分辨率

$$
\Delta f = \frac{f_s}{N} \quad \text{（频率 bin 间距）}
$$

$$
f_k = \frac{k \cdot f_s}{N} = \frac{k}{T} \quad \text{（第 $k$ 个 bin 对应频率）}
$$

其中：
- $f_s$ = 采样率 (Hz)
- $N$ = 采样点数
- $T = N/f_s$ = 信号总时长 (秒)

### 4.3 Python 代码

```python
import numpy as np

# 计算 FFT
X = np.fft.rfft(signal)        # 实数FFT，只返回正频率
magnitude = np.abs(X) / N * 2  # 幅度谱（归一化）
freqs = np.fft.rfftfreq(N, 1/fs)  # 对应的频率轴

# 绘制频谱
import matplotlib.pyplot as plt
plt.plot(freqs, magnitude)
plt.xlabel('Frequency (Hz)')
plt.ylabel('Magnitude')
```

---

## 5. 完整推导路线

$$
\text{正交性} \to \text{系数公式}(a_n, b_n) \to \text{欧拉公式}(\text{复数形式 } c_n) \to T\to\infty \text{ 得傅里叶变换 } F(\omega) \to \text{离散化得 DFT/FFT}
$$

每一步都是上一步的自然推广：
1. **正交性**：不同频率正弦波互相"看不见"
2. **乘基函数+积分**：投影到对应频率方向
3. **欧拉公式**：合并 sin/cos 为更简洁的 $e^{j\omega t}$
4. **$T \to \infty$**：离散频谱 → 连续频谱
5. **离散化**：连续积分 → 离散求和 → 计算机可算

---

## 6. 与泰勒级数的对比

| | 泰勒级数 | 傅里叶级数 |
|---|---|---|
| 基函数 | $\{1, x, x^2, \ldots\}$ | $\{1, \sin, \cos, \sin 2x, \cos 2x, \ldots\}$ |
| 展开方式 | 在一个点附近展开 | 在一个区间上展开 |
| 系数来源 | 导数 $c_n = f^{(n)}(a)/n!$ | 积分 $c_n = \frac{1}{T}\int f\cdot\varphi_n\,dt$ |
| 逼近重点 | 局部 | 全局（均方最优） |

统一视角：两者都是 **Hilbert 空间中的正交展开**，只是选择了不同的正交基和内积。

统一公式：$c_n = \frac{\langle f, \varphi_n \rangle}{\langle \varphi_n, \varphi_n \rangle}$
