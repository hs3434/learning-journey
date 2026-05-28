# Week 5 Day 1: BCI Decoding Fundamentals

## 核心概念

### 1. BCI 系统架构

```
Signal → Preprocessing → Feature Extraction → Classification → Output
```

### 2. EEG 信号采集

```python
# 常见采集参数
fs = 256  # 采样率 (Hz)
n_channels = 32  # 通道数
n_trials = 100  # 试次数

# 数据 shape
data.shape = (n_channels, n_trials * fs * duration)
```

### 3. 常见 BCI 范式

| 范式 | 信号特征 | 应用 |
|------|----------|------|
| SSVEP | 频域稳态响应 | 拼写器 |
| MI | ERD/ERS | 运动控制 |
| P300 | 事件相关电位 | 字符输入 |
| ERP | 事件相关 | 认知 |

## 特征提取方法

```python
# 时域
features = {
    'mean': np.mean(epoch, axis=-1),
    'std': np.std(epoch, axis=-1),
    'max': np.max(epoch, axis=-1),
    'min': np.min(epoch, axis=-1),
}

# 频域
from scipy.signal import welch
psd, freqs = welch(epoch, fs=256, nperseg=128)
alpha_power = psd[(freqs >= 8) & (freqs <= 13)].mean()
```

## 分类方法

```python
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.svm import SVC

# LDA (线性判别分析) - EEG 分类首选
clf = LDA()

# SVM (支持向量机)
clf = SVC(kernel='rbf')
```

## 练习要点

1. 理解 BCI 系统架构
2. 掌握基本特征提取
3. 学会简单分类器使用

## 参考资料

- [BCI 综述](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3550142/)
- [MNE 分类教程](https://mne.tools/stable/auto_tutorials/machine-learning/plot_decoding.html)