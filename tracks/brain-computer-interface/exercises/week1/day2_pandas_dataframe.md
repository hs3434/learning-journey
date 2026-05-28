# Week 1 Day 2: Pandas DataFrame Operations

## 核心概念

### 1. DataFrame 结构

Pandas DataFrame 是带标签的二维表格，非常适合处理 EEG 元数据：

```python
import pandas as pd

df = pd.DataFrame({
    'channel': ['EEG 01', 'EEG 02', 'EEG 03'],
    'type': ['eeg', 'eeg', 'eeg'],
    'x': [-0.5, 0.0, 0.5],
    'y': [0.0, 0.5, 0.0]
})
```

### 2. 索引与切片

```python
# 列访问
ch_names = df['channel']

# 行选择
subset = df.loc[0:5, ['channel', 'x']]

# 条件过滤
eeg_channels = df[df['type'] == 'eeg']
```

### 3. GroupBy 操作

```python
# 按条件分组统计
epoch_stats = df.groupby('epoch_id').agg({
    'amplitude': ['mean', 'std', 'min', 'max']
})
```

### 4. 合并与连接

```python
# Merge - 类似 SQL JOIN
merged = pd.merge(epochs_df, channel_info, on='channel')

# Concat - 按行/列拼接
combined = pd.concat([df1, df2], axis=0)
```

## EEG 实际应用

### 通道元数据管理

```python
# 创建通道信息表
channel_df = pd.DataFrame({
    'channel': ch_names,
    'type': ['eeg'] * len(ch_names),
    'x': np.linspace(-1, 1, len(ch_names)),
    'y': np.linspace(-1, 1, len(ch_names))
})
```

### 长格式与宽格式转换

```python
# 宽转长
long_df = df.melt(id_vars=['time'], var_name='channel', value_name='amplitude')

# 长转宽
wide_df = long_df.pivot(index='time', columns='channel', values='amplitude')
```

## 练习要点

1. 掌握 DataFrame 创建与基本操作
2. 熟练使用 loc/iloc 索引
3. 练习 GroupBy 分组聚合
4. 理解 merge vs concat 适用场景

## 关键函数

| 函数 | 用途 |
|------|------|
| `pd.DataFrame()` | 创建 DataFrame |
| `df.loc[]` | 标签索引 |
| `df.iloc[]` | 位置索引 |
| `df.groupby()` | 分组 |
| `df.merge()` | 表连接 |
| `df.melt()` | 宽转长 |
| `df.pivot()` | 长转宽 |

## 参考资料

- [Pandas 文档](https://pandas.pydata.org/docs/)
- [Pandas Cheat Sheet](https://pandas.pydata.org/docs/user_guide/10min.html)