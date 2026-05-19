# EEG 预处理三步曲：坏通道 + 重参考 + ICA

> 对应学习计划：Week 4 Day 2（预处理核心）
> 前置知识：MNE 基础（Day 1 笔记 06）
> 最后更新：2026-05-19

---

## 0. 为什么要预处理？

原始 EEG 数据就像没洗的菜——有泥沙（噪声）、有烂叶（坏通道）、有杂质（伪迹），直接下锅（分析）结果不可靠。

预处理流程：

```
Raw 原始数据
  ↓
① 坏通道标记/插值    → 去掉"烂叶"
  ↓
② 重参考             → 统一"度量衡"
  ↓
③ ICA 去伪迹         → 洗掉"泥沙"
  ↓
干净的 Epochs → Evoked → 解码
```

**预处理顺序很重要！** 坏通道必须在 ICA 之前处理，重参考也应在 ICA 之前完成。

---

## 1. 坏通道处理（Bad Channels）

### 1.1 什么是坏通道

坏通道 = 记录质量有严重问题的电极，常见原因：

| 类型 | 表现 | 原因 |
|------|------|------|
| **平坦信号** | 信号几乎为零 | 电极脱落、导线断路 |
| **饱和信号** | 信号卡在最大值 | 放大器饱和 |
| **异常噪声** | 幅值远超其他通道 | 电极接触不良、出汗 |
| **跳跃信号** | 不规则跳变 | 导线松动、阻抗不稳 |

### 1.2 如何检测坏通道

**自动检测方法**：

```python
# 方法1：基于幅值阈值
# 信号幅值超过其他通道均值 ± 3SD 的通道
import numpy as np

data = raw.get_data()
ch_std = np.std(data, axis=1)
mean_std = np.mean(ch_std)
bad_by_std = [raw.ch_names[i] for i, s in enumerate(ch_std)
              if s > mean_std + 3 * np.std(ch_std)]

# 方法2：基于通道间相关性
# 与邻近通道相关性过低的通道
# （MNE 的 find_bad_channels_maxwell 可用于 MEG）
```

**手动标记**（最常用）：

```python
# 通过 raw.plot() 交互式查看，手动标记
raw.info['bads'] = ['EEG 053', 'EEG 015']  # 标记坏通道
```

### 1.3 处理方式

| 方式 | 说明 | 适用场景 |
|------|------|----------|
| **直接删除** | 从数据中移除 | 坏通道少、后续分析不需要 |
| **插值修复** | 用周围通道估算 | 坏通道不多、需要保留通道数 |

```python
# 删除坏通道
raw_clean = raw.copy().drop_channels(raw.info['bads'])

# 插值修复（推荐！）
raw_interp = raw.copy().interpolate_bads(reset_bads=True)
# reset_bads=True: 插值后清除坏通道标记
```

### 1.4 插值原理

球面样条插值（Spherical Spline Interpolation）：

$$
V_{bad} = \sum_{i=1}^{N_{good}} w_i \cdot V_{good,i}
$$

用周围好通道的加权平均来估算坏通道的值，权重由电极在头皮上的几何距离决定。

**类比**：坏了一个像素的屏幕，用周围像素颜色填充——距离近的权重大，远的权重小。

---

## 2. 重参考（Re-referencing）

### 2.1 什么是参考电极

EEG 测量的是**两个电极之间的电压差**，不是"绝对电位"：

$$
V_{channel} = V_{scalp} - V_{reference}
$$

所有通道的值都依赖于参考电极的选择，就像温度可以是摄氏度或华氏度——数值不同，但物理量一样。

### 2.2 常见参考方式

| 参考方式 | 说明 | 优缺点 |
|----------|------|--------|
| **原始参考** | 采集时使用的参考（如耳垂、乳突） | 设备决定，可能不理想 |
| **平均参考** | 所有通道的均值作为参考 | ✅ 最常用、最无偏 |
| **特定通道参考** | 如 Cz、Pz | 简单但引入偏置 |
| **双极参考** | 相邻通道差分 | 常用于 EOG/ECG 导联 |

### 2.3 MNE 重参考

```python
# 平均参考（最推荐！）
raw.set_eeg_reference('average')

# 特定通道参考
raw.set_eeg_reference(['Cz'])

# 恢复原始参考（再参考的基础）
raw.set_eeg_reference(ref_channels=None)  # 先回到"无参考"状态
```

### 2.4 为什么平均参考最常用

$$
V_{avg}(t) = \frac{1}{N} \sum_{i=1}^{N} V_i(t)
$$

$$
V_{re-referenced,i} = V_i(t) - V_{avg}(t)
$$

平均参考的优势：
- **无偏**：不偏向任何特定位置
- **可逆**：从平均参考可以转换到任何其他参考
- **理论依据**：在球面上，所有位置的平均电位为零（quasi-static 条件下）

**类比**：原始参考像用"北京时区"看所有城市时间，平均参考像用"所有城市的平均时区"——后者更公平。

### 2.5 ⚠️ 重要注意

- 重参考**必须**在 ICA 之前完成
- 如果采集时用 Cz 做参考，Cz 本身不在数据中 → 平均参考前需要先恢复 Cz
- 坏通道应先处理，否则坏通道的异常值会污染平均参考

---

## 3. ICA 伪迹去除

### 3.1 什么是 ICA

ICA（Independent Component Analysis，独立成分分析）是盲源分离方法，能把混合信号分解为**统计独立的成分**。

**经典类比——鸡尾酒会问题**：

```
房间里 3 个人同时说话（3 个源信号）
  ↓
3 个麦克风各录到 3 个人的混合声（3 个混合信号）
  ↓
ICA：从混合声中分离出每个人的单独声音（3 个独立成分）
```

EEG 版本：

```
头皮上 60 个电极同时记录
  ↓
每个电极记录到的是：脑电 + 眼动 + 心电 + 肌电的混合
  ↓
ICA：分解成 60 个独立成分（IC）
  ↓
识别出哪些 IC 是眼动/心电 → 去掉 → 重建干净信号
```

### 3.2 数学原理

观测信号 $X$ 是源信号 $S$ 的线性混合：

$$
X = A \cdot S
$$

ICA 的目标是找到解混矩阵 $W$，使得：

$$
\hat{S} = W \cdot X \approx S
$$

约束条件：$\hat{S}$ 的各成分之间**统计独立**（非高斯性最大化）。

### 3.3 常见伪迹成分的识别

| 伪迹类型 | IC 特征 | 头皮拓扑图 |
|----------|---------|------------|
| **眼动（EOG）** | 低频、大振幅、慢漂移 | 额极区（Fp1/Fp2）集中 |
| **心电（ECG）** | 周期性脉冲、~1Hz 规律 | 颞/颈部左右对称 |
| **肌电（EMG）** | 高频、持续、低振幅 | 颞/颈部局部集中 |
| **线噪声** | 50/60Hz 窄带 | 全局分布 |

### 3.4 MNE 中使用 ICA

```python
from mne.preprocessing import ICA

# 创建 ICA 对象
ica = ICA(
    n_components=20,      # 成分数（通常 20-30）
    method='fastica',     # 算法：fastica / infomax / picard
    random_state=42,
    max_iter=800
)

# 拟合（用 Raw 数据，不是 Epochs！）
ica.fit(raw)

# 查看成分
ica.plot_components()     # 头皮拓扑图
ica.plot_sources(raw)     # 成分时间序列

# 自动检测伪迹成分
eog_indices, eog_scores = ica.find_bads_eog(raw)
ica.exclude = eog_indices

# 手动添加
ica.exclude += [3, 7]     # 手动识别的成分编号

# 应用到数据
raw_clean = ica.apply(raw.copy())
```

### 3.5 选择成分数量

$$
n_{components} = \min(n_{channels} - 1, \text{explained\_variance\_threshold})
$$

- 64 通道 EEG → 通常选 20-30 个成分
- 太少：伪迹和脑电分不开
- 太多：过拟合，成分不稳定

### 3.6 ⚠️ ICA 使用注意事项

| 要点 | 说明 |
|------|------|
| **拟合前先滤波** | 高通 1Hz（去除慢漂移，ICA 更稳定） |
| **用 Raw 拟合** | 不要用 Epochs 拟合 ICA |
| **坏通道先处理** | 坏通道会严重干扰 ICA |
| **重参考先完成** | 参考选择影响 ICA 分解 |
| **不要过度去除** | 去掉太多成分会损失脑电信号 |
| **检查每次结果** | 自动检测不完美，必须人工复查 |

---

## 4. 完整预处理流程

```python
import mne
from mne.preprocessing import ICA

# 1. 加载
raw = mne.io.read_raw_fif('data.fif', preload=True)

# 2. 标记坏通道
raw.info['bads'] = ['EEG 053', 'EEG 015']

# 3. 插值坏通道
raw.interpolate_bads(reset_bads=True)

# 4. 滤波（ICA 前高通 1Hz）
raw.filter(l_freq=1.0, h_freq=40.0)
raw.notch_filter(freqs=50)

# 5. 重参考
raw.set_eeg_reference('average')

# 6. ICA
ica = ICA(n_components=20, random_state=42, max_iter=800)
ica.fit(raw)

# 自动检测 + 手动确认
eog_idx, _ = ica.find_bads_eog(raw)
ica.exclude = eog_idx

# 应用
raw_clean = ica.apply(raw.copy())

# 7. 创建 Epochs
events = mne.find_events(raw_clean)
epochs = mne.Epochs(raw_clean, events, tmin=-0.2, tmax=0.8,
                    baseline=(-0.2, 0), preload=True,
                    reject={'eeg': 150e-6})
epochs.drop_bad()

# 8. Evoked
evoked = epochs['auditory/left'].average()
```

---

## 5. 关键要点总结

1. **预处理顺序**：坏通道 → 重参考 → ICA，顺序不能乱
2. **坏通道**：手动标记 + 插值修复，不要直接删除
3. **重参考**：平均参考最常用、最无偏
4. **ICA**：盲源分离，分解出独立成分，识别并去除伪迹
5. **ICA 前必须**：滤波（高通 1Hz）+ 坏通道处理 + 重参考
6. **不要过度去除**：每次只去掉明确识别的伪迹成分
7. **预处理是基础**：垃圾进垃圾出，预处理质量决定分析结果
