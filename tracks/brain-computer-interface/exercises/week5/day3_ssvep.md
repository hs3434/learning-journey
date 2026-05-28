# Week 5 Day 3: SSVEP and CCA

## 核心概念

### 1. SSVEP 原理

稳态视觉诱发电位 (Steady-State Visual Evoked Potential)：
- 视觉刺激引起的大脑皮层同步电位
- 频率与刺激频率相同或倍频
- 信噪比高，分类简单

### 2. CCA (典型相关分析)

```python
import numpy as np
from scipy.signal import correlate

class SSVEPDetector:
    def __init__(self, freqs, fs, n_harmonics=5):
        self.freqs = freqs
        self.fs = fs
        self.n_harmonics = n_harmonics

    def generate_template(self, freq):
        """生成参考信号"""
        t = np.arange(0, 1, 1/self.fs)
        template = np.zeros((self.n_harmonics, len(t)))

        for h in range(1, self.n_harmonics + 1):
            template[h-1] = np.sin(2 * np.pi * h * freq * t)

        return template

    def cca_score(self, data, freq):
        """计算 CCA 分数"""
        X = data.T  # (n_samples, n_channels)
        Y = self.generate_template(freq)  # (n_harmonics, n_samples)

        C_xx = np.cov(X)
        C_yy = np.cov(Y)
        C_xy = np.dot(X, Y.T)

        try:
            r = np.linalg.solve(C_yy, C_xy.T)
            R = np.cov(np.dot(X, r))
            eigenvalues = np.linalg.eigvalsh(R)
            return np.max(eigenvalues)
        except:
            return 0

    def detect(self, data):
        scores = [self.cca_score(data, f) for f in self.freqs]
        return np.argmax(scores), scores
```

### 3. FBCCA (滤波 CCA)

改进版，使用滤波器组分离谐波：

```python
def fbcca_score(self, data, freq):
    """滤波 CCA"""
    total_score = 0
    for h in range(1, self.n_harmonics + 1):
        # 滤波后计算 CCA
        filtered = self.bandpass_filter(data, freq * h - 2, freq * h + 2)
        total_score += self.cca_score(filtered, freq * h)
    return total_score / self.n_harmonics
```

### 4. 参数选择

| 参数 | 建议值 |
|------|--------|
| 刺激频率 | 8-15 Hz (alpha range) |
| 刺激数量 | 4-6 targets |
| 分析窗口 | 1-3 秒 |
| 谐波数 | 3-5 |

## 练习要点

1. 理解 SSVEP 机制
2. 掌握 CCA 分类算法
3. 学会实现简单 SSVEP 检测器

## 参考资料

- [SSVEP 综述](https://ieeexplore.ieee.org/document/5200237)
- [CCA 方法](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3949405/)