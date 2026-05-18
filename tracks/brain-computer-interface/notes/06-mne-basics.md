# MNE-Python 基础：Raw / Epochs / Evoked

> 对应学习计划：Week 4 Day 1（MNE 数据结构）
> 前置知识：信号处理基础（Week 3 笔记 01-05）
> 最后更新：2026-05-18

---

## 1. MNE-Python 是什么

MNE-Python 是 EEG/MEG 数据分析的**标准工具**，相当于 BCI 领域的 NumPy。

| 特性 | 说明 |
|------|------|
| 开源 | 免费，社区活跃 |
| 全流程 | 从数据加载到解码分类，一站式 |
| 数据结构 | Raw → Epochs → Evoked，层层递进 |
| 可视化 | 交互式绘图，支持 topo 图 |
| BCI 必备 | 几乎所有 BCI 论文的代码都用 MNE |

安装：`pip install mne`

---

## 2. 三大数据结构：层层递进

MNE 的数据处理流程就是三个对象的转换链：

```
Raw → Epochs → Evoked
(原始连续数据) (切分后的试次) (多次试次平均)
```

**类比**：

| MNE 对象 | 类比 | 含义 |
|----------|------|------|
| **Raw** | 一整盘录像带 | 连续记录的原始 EEG，可能几分钟到几小时 |
| **Epochs** | 剪辑好的片段 | 按事件标记切分出的一段段短数据（如每次运动想象 -1s 到 +2s） |
| **Evoked** | 多次片段的叠影照片 | 多次 Epochs 取平均，看"典型响应"长什么样 |

---

## 3. Raw：原始连续数据

### 3.1 核心属性

```python
import mne

raw = mne.io.read_raw_fif('sample.fif', preload=True)

# 核心属性
raw.info          # 元信息（采样率、通道名、通道类型、滤波设置等）
raw.ch_names      # 通道名列表 ['Fp1', 'Fp2', 'C3', ...]
raw.n_times       # 采样点数
raw.times         # 时间轴数组
raw.info['sfreq'] # 采样率 (Hz)

# 获取数据矩阵
data = raw.get_data()  # shape: (n_channels, n_times)
```

### 3.2 info 字典

`raw.info` 是 MNE 最重要的元信息容器：

| 字段 | 说明 | 示例 |
|------|------|------|
| `sfreq` | 采样率 | 250.0 Hz |
| `ch_names` | 通道名 | ['Fp1', 'Fp2', ...] |
| `ch_type` | 通道类型 | 'eeg', 'eog', 'ecg' |
| `highpass` | 高通截止频率 | 0.5 Hz |
| `lowpass` | 低通截止频率 | 40.0 Hz |
| `nchan` | 通道数 | 64 |
| `montage` | 电极位置 | standard_1020 |

### 3.3 常用操作

```python
# 加载数据
raw = mne.io.read_raw_fif('sample.fif', preload=True)
raw = mne.io.read_raw_brainvision('sample.vhdr', preload=True)
raw = mne.io.read_raw_edf('sample.edf', preload=True)

# 滤波
raw.filter(l_freq=0.5, h_freq=40.0)  # 带通 0.5-40Hz
raw.notch_filter(freqs=50)            # 50Hz 工频

# 选择通道
raw_eeg = raw.pick('eeg')             # 只保留 EEG 通道
raw_pick = raw.pick_channels(['C3', 'C4', 'P3', 'P4'])

# 裁剪
raw_crop = raw.copy().crop(tmin=10, tmax=60)  # 取 10-60秒

# 可视化
raw.plot()  # 交互式查看原始波形
raw.compute_psd().plot()  # 功率谱
```

---

## 4. Epochs：切分后的试次

### 4.1 为什么要切分

BCI 实验通常有**多次重复**（trials/epochs）：
- 每次运动想象 → 一个 epoch
- 每次闪烁刺激 → 一个 epoch
- 需要把连续数据**按事件标记**切成一段段

### 4.2 事件（Events）

MNE 用事件数组标记"发生了什么"：

```python
# 事件数组：shape (n_events, 3)
# 每行 = [采样点, 0, 事件编码]
events = mne.find_events(raw)

# 示例：
# [[  500, 0, 1],   # 第500个采样点，事件1（左手想象）
#  [ 1500, 0, 2],   # 第1500个采样点，事件2（右手想象）
#  [ 2500, 0, 1],   # 第2500个采样点，事件1
#  [ 3500, 0, 3]]   # 第3500个采样点，事件3（休息）
```

事件编码映射：

```python
event_id = {
    'left_hand': 1,
    'right_hand': 2,
    'rest': 3
}
```

### 4.3 创建 Epochs

```python
epochs = mne.Epochs(
    raw, events,
    event_id=event_id,
    tmin=-0.2,      # 事件前 0.2秒（基线）
    tmax=0.8,       # 事件后 0.8秒
    baseline=(-0.2, 0),  # 基线校正区间
    preload=True    # 预加载到内存
)
```

**基线校正**：用事件前的信号均值作为零点，减去它，消除基线漂移。

### 4.4 Epochs 常用操作

```python
# 基本信息
epochs.info        # 同 Raw 的 info
epochs.events      # 事件数组
epochs.event_id    # 事件编码映射
epochs.tmin        # 起始时间
epochs.tmax        # 结束时间

# 获取数据
data = epochs.get_data()  # shape: (n_epochs, n_channels, n_times)

# 按条件选择
epochs_left = epochs['left_hand']   # 只要左手想象
epochs_right = epochs['right_hand'] # 只要右手想象

# 平均 → Evoked
evoked_left = epochs_left.average()
evoked_right = epochs_right.average()

# 可视化
epochs.plot()          # 交互式查看所有 epoch
epochs.plot_image()    # 每个epoch的时频热力图
```

### 4.5 数据形状对比

| 对象 | shape | 说明 |
|------|-------|------|
| Raw | (n_channels, n_times) | 连续数据，n_times 很大 |
| Epochs | (n_epochs, n_channels, n_times) | 多了一段试次维度 |
| Evoked | (n_channels, n_times) | 平均后回到二维，但 n_times 是短窗口 |

---

## 5. Evoked：平均响应

### 5.1 为什么要平均

单次 epoch 有大量噪声，信号被淹没。多次平均后，随机噪声互相抵消，信号浮现：

$$
\text{Evoked}(t) = \frac{1}{N} \sum_{i=1}^{N} \text{Epoch}_i(t)
$$

信噪比提升：$\text{SNR} \propto \sqrt{N}$（100 次平均 → SNR 提升 10 倍）

### 5.2 类比理解

- 单次 epoch = 在暗光下拍一张照片 → 模糊
- Evoked = 多张照片叠在一起 → 噪声抵消，图像清晰

### 5.3 常用操作

```python
# 创建
evoked = epochs.average()              # 所有条件平均
evoked_left = epochs['left_hand'].average()

# 可视化
evoked.plot()                  # 波形图（各通道）
evoked.plot_topomap()          # 拓扑图（各时间点头皮分布）
evoked.plot_joint()            # 波形 + topo 联合图

# 对比
mne.viz.plot_compare_evokeds(
    [evoked_left, evoked_right],
    legend=['Left', 'Right']
)
```

---

## 6. MNE 数据处理标准流程

```
1. 加载 Raw
   ↓
2. 预处理：滤波 + Notch
   ↓
3. 找事件 (find_events)
   ↓
4. 创建 Epochs (带基线校正)
   ↓
5. 去伪迹 (ICA) → 干净的 Epochs
   ↓
6. 平均 → Evoked (看 ERP/ERD)
   ↓
7. 特征提取 + 分类 (BCI 解码)
```

### 6.1 完整代码骨架

```python
import mne
from mne.preprocessing import ICA

# 1. 加载
raw = mne.io.read_raw_fif('data.fif', preload=True)

# 2. 预处理
raw.filter(0.5, 40)
raw.notch_filter(50)

# 3. 找事件
events = mne.find_events(raw)
event_id = {'left': 1, 'right': 2}

# 4. 创建 Epochs
epochs = mne.Epochs(raw, events, event_id,
                    tmin=-0.2, tmax=0.8,
                    baseline=(-0.2, 0),
                    preload=True)

# 5. ICA 去伪迹
ica = ICA(n_components=20, random_state=42)
ica.fit(raw)
ica.exclude = [0]  # 手动识别的伪迹成分
epochs_clean = ica.apply(epochs.copy())

# 6. 平均
evoked_left = epochs_clean['left'].average()
evoked_right = epochs_clean['right'].average()

# 7. 可视化
mne.viz.plot_compare_evokeds([evoked_left, evoked_right])
```

---

## 7. 关键要点总结

1. **MNE 三大对象层层递进**：Raw（连续）→ Epochs（切分）→ Evoked（平均）
2. **Raw = 录像带**，包含所有连续数据 + info 元信息
3. **Epochs = 剪辑片段**，按事件标记切分，带基线校正
4. **Evoked = 叠影照片**，多次平均提升 SNR（$\propto \sqrt{N}$）
5. **事件数组 shape = (n_events, 3)**：[采样点, 0, 事件编码]
6. **基线校正**：减去事件前基线均值，消除漂移
7. **标准流程**：加载→滤波→找事件→Epochs→ICA→Evoked→解码
