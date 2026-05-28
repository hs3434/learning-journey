# Week 4 Day 3: Events and Epochs

## 核心概念

### 1. 事件检测

```python
# 从 stim 通道检测事件
events = mne.find_events(raw, stim_channel='STI 014')

print(f"事件数量: {len(events)}")
print(f"前5个事件:\n{events[:5]}")
# 输出格式: [sample, previous_value, event_id]
```

### 2. 事件信息

```python
event_id = {
    'auditory/left': 1,
    'auditory/right': 2,
    'visual/left': 3,
    'visual/right': 4
}
```

### 3. 创建 Epochs

```python
epochs = mne.Epochs(
    raw,
    events,
    event_id,
    tmin=-0.2,      # 事件前 200ms
    tmax=0.5,       # 事件后 500ms
    baseline=(-0.2, 0),  # baseline 校正
    preload=True,
    reject=dict(eeg=150e-6)  # 拒绝异常幅度
)

print(f"Epochs 数量: {len(epochs)}")
print(f"数据 shape: {epochs.get_data().shape}")
```

### 4. 选择数据

```python
# 按条件选择
auditory = epochs['auditory/left']
visual = epochs['auditory/right']

# 组合条件
combined = epochs['auditory/left', 'auditory/right']
```

### 5. Evoked（平均）

```python
evoked = epochs['auditory/left'].average()
evoked_data = evoked.data
print(f"Evoked shape: {evoked_data.shape}")
```

## 事件对齐

```python
# 确保 trigger 对齐
import numpy as np

# 事件时间（秒）
event_times = events[:, 0] / raw.info['sfreq']

# 相对时间（以第一个事件为0）
relative_times = event_times - event_times[0]
```

## 练习要点

1. 掌握事件检测方法
2. 理解 Epochs 创建参数
3. 学会 baseline 校正

## 参考资料

- [MNE Epochs](https://mne.tools/stable/generated/mne.Epochs.html)
- [事件处理](https://mne.tools/stable/auto_tutorials/epochs/plot_objects_from_raw.html)