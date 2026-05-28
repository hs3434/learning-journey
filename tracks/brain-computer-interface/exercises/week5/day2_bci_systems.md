# Week 5 Day 2: BCI Systems and Protocols

## 核心概念

### 1. BCI 系统分类

| 类型 | 输入信号 | 输出 |
|------|----------|------|
| 同步 (Synchronous) | 规定时间窗口 | 刺激选择 |
| 异步 (Asynchronous) | 实时连续 | 连续控制 |

### 2. 常见 BCI 协议

```python
# 刺激协议示例
protocol = {
    'SSVEP': {'freqs': [8, 10, 12, 15], 'n_targets': 4},
    'P300': {'n_repetitions': 10, 'interval': 0.1},
    'MI': {'n_classes': 2, 'duration': 4}
}
```

### 3. 信号采集系统

```python
# 常见设备
devices = {
    'BrainAmp': {'channels': 32, 'fs': 100},
    'g.USBamp': {'channels': 16, 'fs': 256},
    'BCI2000': {'channels': 64, 'fs': 400}
}
```

### 4. LSL (Lab Streaming Layer)

实时信号流：

```python
from pylsl import StreamInlet, resolve_byprop

# 查找 EEG 流
streams = resolve_byprop('type', 'EEG')
inlet = StreamInlet(streams[0])

# 接收数据
sample, timestamp = inlet.pull_sample()
```

## BCI 工作流程

```python
# 完整流程
def bci_workflow():
    # 1. 采集
    raw = acquire_eeg()

    # 2. 预处理
    raw.filter(0.5, 40).set_eeg_reference('average')

    # 3. 特征提取
    features = extract_features(raw)

    # 4. 分类
    command = classifier.predict(features)

    # 5. 输出
    apply_command(command)
```

## 练习要点

1. 理解同步/异步 BCI
2. 掌握 BCI 协议设计
3. 了解信号采集基础

## 参考资料

- [BCI 协议设计](https://www.bci2000.org/mediawiki/index.php/User_Reference:Protocol)
- [LSL 文档](https://github.com/labstreaminglayer/lsl_apps)