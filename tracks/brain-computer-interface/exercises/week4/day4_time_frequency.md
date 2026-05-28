# Week 4 Day 4: Time-Frequency Analysis & ERD/ERS

## 核心概念

### 1. 时频分析

```python
from mne.time_frequency import tfr_multitaper, tfr_morlet

# Morlet 小波
freqs = np.arange(5, 30, 1)  # 5-30Hz
tfr = tfr_morlet(epochs, freqs=freqs, n_cycles=5, return_itc=False)

# 多锥体 tapers
tfr = tfr_multitaper(epochs, freqs=freqs, n_cycles=5, return_itc=False)
```

### 2. ERD/ERS

事件相关去同步/同步化 (Event-Related Desynchronization/Synchronization)：

- **ERD**: Alpha/Beta 频段功率下降（与运动相关）
- **ERS**: Alpha/Beta 频段功率上升（运动后恢复）

### 3. ERD/ERS 计算

```python
# 计算 power change
baseline = (-0.5, -0.2)  # 事件前
tfr.apply_baseline(baseline)

# 转为百分比变化
power_change = 100 * (tfr.data - baseline_power) / baseline_power
```

### 4. 可视化

```python
# 时频图
tfr.plot(vmin=-100, vmax=100, cmap='RdBu_r')

# 特定频段
tfr.plot_topomap(ch_type='eeg', mode='mean', fmin=8, fmax=13)
```

## 频段特征

| 频段 | ERD/ERS 模式 |
|------|--------------|
| Alpha (8-13Hz) | 对侧运动区 ERD |
| Beta (13-30Hz) | 对侧运动区 ERD，运动后 ERS |
| Gamma (30-100Hz) | 认知相关 ERS |

## 运动想象 ERD/ERS

```python
# MI 左右手实验
# - 左侧 MI → 右侧感觉运动皮层 alpha/beta ERD
# - 右侧 MI → 左侧感觉运动皮层 alpha/beta ERD
```

## 练习要点

1. 理解 ERD/ERS 概念
2. 掌握 Morlet 小波时频分析
3. 学会绘制时频图

## 参考资料

- [MNE 时频](https://mne.tools/stable/auto_tutorials/time-frequency/plot_tutorial_wavelet.html)
- [ERD/ERS 教程](https://mne.tools/stable/auto_tutorials/time-frequency/plot_erds.html)