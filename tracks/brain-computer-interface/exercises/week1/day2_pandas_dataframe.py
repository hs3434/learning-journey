"""
Week 1 Day 2: Pandas DataFrame Operations
========================================
Pandas DataFrame、GroupBy、merge
批量处理 EEG 数据
"""
import numpy as np
import pandas as pd
from pathlib import Path

out_dir = '/tmp'

# ============================================================
# 1. DataFrame 创建与索引
# ============================================================
print("=" * 60)
print("1. DataFrame 创建与索引")
print("=" * 60)

data_dir = Path('/work/run/projects/bio-24/my_projects/learning-journey/tracks/brain-computer-interface/projects/output')
results = np.load(data_dir / 'results.npy', allow_pickle=True)

channels = [f'EEG {i:02d}' for i in range(results.shape[0])]
times = np.arange(results.shape[1]) / 256

df = pd.DataFrame(results.T, columns=channels, index=times)
df.index.name = 'Time (s)'
print(f"DataFrame shape: {df.shape}")
print(f"\n前5行:\n{df.iloc[:5, :5]}")
print(f"\n列名: {df.columns[:5].tolist()}")

print(f"\n索引 'EEG 00' 列:\n{df['EEG 00'].describe()}")

# ============================================================
# 2. 切片与过滤
# ============================================================
print("\n" + "=" * 60)
print("2. 切片与过滤")
print("=" * 60)

alpha_df = df.loc[0.5:1.0]
print(f"0.5-1.0秒 数据: {alpha_df.shape}")

col_subset = df[['EEG 00', 'EEG 01', 'EEG 02']]
print(f"\n选择列: {col_subset.shape}")

# ============================================================
# 3. 统计与聚合
# ============================================================
print("\n" + "=" * 60)
print("3. 统计与聚合")
print("=" * 60)

stats = df.agg(['mean', 'std', 'min', 'max'])
print(f"各通道统计:\n{stats.iloc[:, :3]}")

channel_means = df.mean()
print(f"\n各通道均值 (前5):\n{channel_means[:5]}")

# ============================================================
# 4. GroupBy 操作
# ============================================================
print("\n" + "=" * 60)
print("4. GroupBy 操作")
print("=" * 60)

epoch_labels = np.array([0]*256 + [1]*256 + [2]*256 + [3]*256)[:df.shape[0]]
df['epoch'] = np.repeat(np.arange(4), 256)[:df.shape[0]]

epoch_stats = df.groupby('epoch').mean()
print(f"各 epoch 平均:\n{epoch_stats.iloc[:3, :3]}")

epoch_stats_df = df.groupby('epoch').agg(['mean', 'std'])
print(f"\n各 epoch 聚合统计:\n{epoch_stats_df.iloc[:3]}")

# ============================================================
# 5. Merge 与连接
# ============================================================
print("\n" + "=" * 60)
print("5. Merge 与连接")
print("=" * 60)

channel_info = pd.DataFrame({
    'channel': channels,
    'type': ['eeg'] * len(channels),
    'x': np.linspace(-1, 1, len(channels)),
    'y': np.linspace(-1, 1, len(channels))
})
print(f"通道元数据:\n{channel_info.head()}")

df_reset = df.reset_index()
merged = df_reset.melt(id_vars=['Time (s)'], var_name='channel', value_name='amplitude')
print(f"\n宽转长格式:\n{merged.head()}")

merged_with_info = merged.merge(channel_info, on='channel')
print(f"\n合并后:\n{merged_with_info.head()}")

print("\n✅ Day 2 完成!")