# SSVEP (Steady-State Visual Evoked Potential)

## 原理

当视觉皮层接收到周期性闪烁的刺激时，会产生与刺激频率相同或倍频的同步电位响应。

### 特点

- **频率响应**：刺激频率在 8-30 Hz 范围内效果最佳
- **信噪比高**：稳态响应比瞬态 ERP 更易检测
- **信息传输率高 (ITR)**：适合拼写器等应用

### 频率选择

| 频段 | 频率范围 | 特点 |
|------|----------|------|
| Low | 8-12 Hz | Alpha，易检测但易疲劳 |
| Medium | 12-20 Hz | 平衡速度和精度 |
| High | 20-30 Hz | 快但检测困难 |

## CCA (典型相关分析)

### 原理

CCA 找两组信号（EEG 信号和参考信号）之间的最大相关性。

### 实现

```python
import numpy as np

class SSVEPDetector:
    def __init__(self, freqs, fs, n_harmonics=5):
        self.freqs = freqs
        self.fs = fs
        self.n_harmonics = n_harmonics

    def generate_template(self, freq):
        """生成正弦余弦参考信号"""
        t = np.arange(0, 1, 1/self.fs)
        template = []
        for h in range(1, self.n_harmonics + 1):
            template.append(np.sin(2 * np.pi * h * freq * t))
            template.append(np.cos(2 * np.pi * h * freq * t))
        return np.array(template)

    def cca(self, data, freq):
        """CCA 计算"""
        X = data.T  # (n_samples, n_channels)
        Y = self.generate_template(freq)  # (2*n_harmonics, n_samples)

        C_xx = np.cov(X, rowvar=True)
        C_yy = np.cov(Y, rowvar=True)
        C_xy = np.dot(X, Y.T)

        # 求解典型变量
        try:
            r = np.linalg.solve(C_yy, C_xy)
            R = np.dot(np.dot(X, r), np.linalg.inv(C_xx))
            eigvals = np.linalg.eigvalsh(R)
            return np.max(eigvals)
        except:
            return 0
```

## FBCCA (滤波 CCA)

使用滤波器组分离各次谐波：

```python
from scipy.signal import butter, filtfilt

def fbcca(self, data, freq):
    """滤波 CCA"""
    scores = []
    for h in range(1, self.n_harmonics + 1):
        # 带通滤波分离 h 次谐波
        low = (freq * h - 2) / (self.fs / 2)
        high = (freq * h + 2) / (self.fs / 2)
        b, a = butter(4, [low, high], btype='band')
        filtered = filtfilt(b, a, data, axis=-1)

        # 计算该谐波的 CCA 分数
        score = self.cca(filtered, freq * h)
        scores.append(score)

    return np.mean(scores)
```

## 参数设置

```python
config = {
    'stim_freqs': [8, 10, 12, 15],  # 刺激频率
    'n_harmonics': 5,                # 谐波数
    'window_len': 2.0,              # 分析窗口 (秒)
    'method': 'fbcca'               # 方法: cca, fbcca, itcc
}
```

## 优缺点

| 优点 | 缺点 |
|------|------|
| 高 ITR | 需要视觉刺激设备 |
| 无需训练 | 用户需注视屏幕中心 |
| 实现简单 | 对眼动敏感 |

## 参考资料

- [BCI Competition IV SSVEP](http://www.bbci.de/competition/iv/)
- [FBCCA 论文](https://ieeexplore.ieee.org/document/6570375)