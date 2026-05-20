# 事件标记 + Epoch 切分 + Trigger 对齐

> 对应学习计划：Week 4 Day 3（预处理后 → 事件驱动分析）
> 前置知识：预处理（Day 2 笔记 07）
> 最后更新：2026-05-20

---

## 0. 为什么需要事件与 Epoch？

### 0.1 连续 Raw 数据 vs 事件锁定数据

```
Raw 数据：                            Epoch 数据：
─────────────────────────────────    ──────────────────────────────
长时间连续记录（数分钟~数小时）         按"事件"切分的短时间段
所有时间点混在一起                     每个 epoch 对齐到事件 onset
无法直接分析"刺激诱发响应"             便于平均（SNR↑）和时频分析

问题：                                解决思路：
大脑活动是连续的                      但认知任务有离散的事件（刺激 onset）
刺激诱发响应淹没在自发活动中           用事件 onset 做时间零点，对齐切分
                                      同一事件类型的多次试验 → 平均 → SNR
```

### 0.2 核心概念

| 概念 | 说明 |
|------|------|
| **Event（事件）** | 一个时间点 + 一个标签（如"左耳听觉刺激"） |
| **Trigger / Stimulus Channel** | 记录事件代码的通道（如 STI 014） |
| **Epoch** | 以事件 onset 为中心的固定时间窗口（如 -0.2s ~ 0.8s） |
| **Baseline** | Epoch 中用于校正的基线时间段（如事件前 200ms） |
| **t=0** | 事件 onset（刺激到达被试）的时刻 |

---

## 1. 事件标记（Event Detection）

### 1.1 硬件 Trigger 机制

```
实验设备（stim PC）               放大器/采集系统
      │                                   │
      │──── 串口/并口/USB 触发信号 ──────→│ STI 014 通道（或其他 stim channel）
      │                                   │
  发送事件代码                             连续采样
  （如 1=听觉左，2=听觉右）                把事件代码写入数据流

采样率 1000Hz 时：
  → 事件代码持续 1 个采样点（1ms）也能被捕获（MNE 会在邻域内合并）
```

### 1.2 MNE 找事件

```python
import mne

# 方法1：自动从 stim channel 找事件（最常用）
events = mne.find_events(raw, stim_channel='STI 014', verbose=False)

# events 是 numpy array，shape = (n_events, 3)
# 列：[时间索引(sample), 前一时间索引(old_id), 事件代码]
print(events[:5])
# [[ 5739  5738     1]   # event_id=1 at sample 5739
#  [ 6431  6430     2]   # event_id=2 at sample 6431
#  [ 7123  7122     3]   # event_id=3 at sample 7123
#  ...]

# 方法2：从已有 events 重新编码
new_events = mne.merge_events(events, [1, 2], 12)  # 把 1,2 合并成 12

# 方法3：从原有事件ID创建新事件（如 button press = 32）
```

### 1.3 事件代码表

```python
event_id = {
    'auditory/left':  1,    # 听觉-左侧
    'auditory/right': 2,    # 听觉-右侧
    'visual/left':     3,    # 视觉-左侧
    'visual/right':    4,    # 视觉-右侧
    'button':         32,    # 被试按钮反应
}
```

### 1.4 事件相关电位（ERP）简介

```
ERP 是什么：
  → 相同事件类型的 many epochs → 逐点平均
  → 事件锁定的时间点（t=0）附近出现的一致性波形

为什么平均能提取 ERP：
  - 脑电自发活动：各次试验之间无规律 → 随机噪声，平均后趋于 0
  - 事件诱发响应：每次都有 → 信号，平均后保留

经典 ERP 成分（N100/P200/N400 等）：
  N100: 刺激后 ~100ms 的负峰（听觉/视觉早期感知）
  P200: ~200ms 的正峰（注意定向）
  N400: ~400ms 的负峰（语言/语义加工）
```

---

## 2. Epoch 切分

### 2.1 什么是 Epoch

Epoch = 以事件 onset 为中心、长度固定的**数据段**：

```
时间轴:  ←──────────── tmin ──────── [EVENT ONSET] ──────── tmax ──→
         │←────────── baseline ──────→│                     ↑
         │←──────────────── epoch ───────────────────────→│
```

### 2.2 MNE 创建 Epochs

```python
# 基本参数
epochs = mne.Epochs(
    raw,                    # 干净数据（预处理后）
    events,                 # 事件数组
    event_id,               # 事件标签字典
    tmin=-0.2,              # 事件前 200ms
    tmax=0.8,               # 事件后 800ms
    baseline=(None, 0),     # 基线校正：事件前(-0.2~0)作为基线
    preload=True,           # 预加载到内存（后续分析必须）
    verbose=False
)

# 数据结构
# epochs.get_data()  → shape: (n_epochs, n_channels, n_times)
#                     → 3D array！
```

### 2.3 基线校正（Baseline Correction）

**为什么需要基线校正？**

$$V_{corrected}(t) = V_{raw}(t) - \mu_{baseline}$$

减去基线期间的均值，消除直流偏移和缓慢漂移，使不同时刻的测量可比。

```
基线选择原则：
  (None, 0)      → 用事件前所有时间点做基线（常用！）
  (-0.2, 0)      → 明确指定基线窗口
  (None, None)   → 不做基线校正
```

**类比**：就像测量温度变化，要先减去室温（基线），再记录温度升降。

### 2.4 Epoch 拒绝（Reject Bad Epochs）

```python
# 幅值异常大的 epoch（眨眼/运动伪迹残留）自动拒绝
epochs.drop_bad(reject={'eeg': 150e-6}, verbose=False)
# 'eeg': 150e-6 → EEG 通道幅值超过 ±150μV 的 epoch 丢弃

# 手动查看被拒绝的原因
print(epochs.drop_log)  # 记录每个 epoch 被拒绝的原因
```

### 2.5 条件筛选与平均

```python
# 筛选条件
auditory_epochs = epochs['auditory/left']
visual_epochs = epochs['auditory/right']

# 平均 → Evoked
evoked_aud_left = auditory_epochs.average()
evoked_aud_right = auditory_epochs.average()

# 多次条件平均
evoked_all = epochs['auditory'].average()  # auditory/left + auditory/right

# 支持通配符
evoked_left = epochs['*/left'].average()   # 所有左侧事件
```

---

## 3. Trigger 对齐与同步问题

### 3.1 Trigger Delay（触发延迟）

```
理想情况：
  刺激 onset（物理光/声音出现）
      ↓ 瞬间
  触发信号发送到采集系统
      ↓
  采集系统记录 STI 通道

现实问题：
  刺激 → 触发 之间有延迟（声/光刺激器本身有延迟）
  延迟量因硬件而异，通常 5-50ms

解决方案：
  1. 硬件同步：让刺激软件直接发 trigger（延迟最小）
  2. 软件延迟补偿：在数据分析时手动 offset
  3. 校准：用已知延迟的刺激测出系统延迟量
```

### 3.2 事件遗漏检测

```python
# 检查是否有遗漏的事件（trigger 宽度太窄导致）
# MNE 默认合并相邻（< 1 sample）事件

# 查看事件分布是否合理
print(mne.find_events(raw, stim_channel='STI 014', min_duration=0.001))
# min_duration: 最小事件持续时间
```

### 3.3 连续 vs 稀疏刺激

```
连续刺激（如稳态视觉诱发电位 SSVEP）：
  → 频率固定，不适合 epoch 平均
  → 适合频域分析（傅里叶/相干分析）

离散刺激（一次性事件，如提示语）：
  → 适合 epoch + 平均 = ERP 分析
  → 适合时频分析 = ERD/ERS 分析
```

---

## 4. 实战：完整流程

```python
import mne
import numpy as np

# 1. 加载连续数据（假设已预处理）
raw = mne.io.read_raw_fif('preprocessed_raw.fif', preload=True, verbose=False)

# 2. 找事件
events = mne.find_events(raw, stim_channel='STI 014', verbose=False)
event_id = {'auditory/left': 1, 'auditory/right': 2, 'visual/left': 3, 'visual/right': 4}

# 3. 创建 Epochs（-0.2s ~ 0.8s，基线校正）
epochs = mne.Epochs(
    raw, events, event_id,
    tmin=-0.2, tmax=0.8,
    baseline=(None, 0),     # 基线：事件前全部
    preload=True, verbose=False
)

# 4. 自动拒绝坏 epoch（幅值超 ±150μV）
epochs.drop_bad(reject={'eeg': 150e-6}, verbose=False)
print(f"有效 epochs: {len(epochs)} / 原始 {len(events)}")

# 5. 平均 → Evoked
evoked_al = epochs['auditory/left'].average()
evoked_vl = epochs['visual/left'].average()

# 6. 可视化
evoked_al.plot_joint(title='Auditory Left ERP')
evoked_al.plot(gfp=True)  # Global Field Power
```

---

## 5. 关键要点总结

1. **Event = 时间点 + 标签**，记录在 stim channel（如 STI 014）
2. **mne.find_events()** 从 stim channel 提取事件信息
3. **Epoch** = 以事件 onset 为中心的固定时间窗口（tmin ~ tmax）
4. **Baseline correction** = 减去事件前均值，消除直流偏移
5. **drop_bad()** 自动拒绝幅值异常的 epoch
6. **Evoked = 多 epoch 平均** → 提取事件相关电位（ERP），SNR↑
7. **Trigger delay** 可能存在，需要硬件/软件同步补偿
8. **Epoch 后平均** 是 ERP 分析的核心范式
