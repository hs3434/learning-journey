# Week 4 Day 2: EEG Preprocessing

## 核心概念

### 1. 坏通道处理

```python
# 自动检测坏通道（高/低标准差）
data_eeg = raw.get_data(picks='eeg')
ch_std = np.std(data_eeg, axis=1)
mean_std = np.mean(ch_std)
std_of_std = np.std(ch_std)

high_threshold = mean_std + 3 * std_of_std
low_threshold = mean_std - 3 * std_of_std

bad_channels = [ch for i, ch in enumerate(eeg_ch_names)
                if ch_std[i] > high_threshold or ch_std[i] < low_threshold]

# 标记坏通道
raw.info['bads'] = bad_channels

# 插值
raw.interpolate_bads(reset_bads=True)
```

### 2. 重参考

```python
# 平均参考
raw.set_eeg_reference('average')

# 乳突参考
raw.set_eeg_reference(['EEG 001', 'EEG 002'])

# 重新参考到其他通道
raw.set_eeg_reference('CAR')  # Common Average Reference
```

### 3. ICA 伪迹去除

```python
from mne.preprocessing import ICA

# 拟合 ICA
ica = ICA(n_components=15, method='fastica')
ica.fit(raw, picks='eeg')

# 查看独立成分
ica.plot_components()
ica.plot_sources(raw)

# 标记眼动成分并去除
ica.exclude = [0, 1]  # 通常是眼动
raw_clean = raw.copy()
ica.apply(raw_clean)
```

### 4. 预处理流程

```python
# 标准预处理流程
raw = mne.io.read_raw_fif('data.fif', preload=True)
raw.pick('eeg')                          # 只保留 EEG
raw.filter(0.5, 40)                     # 带通滤波
raw.notch_filter(50)                    # 去除工频
raw.set_eeg_reference('average')         # 重参考
```

## 伪迹类型与处理

| 伪迹 | 特征 | 处理方法 |
|------|------|----------|
| 眼动 | Fp, Fp2 通道高幅 | ICA, 回归 |
| 眨眼 | 前部通道 delta 波 | ICA |
| 肌肉 | Gamma 高频 | 陷波 |
| 工频 | 50Hz/60Hz | Notch |

## 练习要点

1. 掌握坏通道检测和插值
2. 理解不同重参考方法
3. 学会使用 ICA 去除伪迹

## 参考资料

- [MNE 预处理](https://mne.tools/stable/auto_tutorials/preprocessing/plot_preprocessing.html)
- [ICA 教程](https://mne.tools/stable/auto_tutorials/preprocessing/plot_05_define_to_remove.html)