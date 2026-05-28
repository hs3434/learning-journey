"""
Week 1 Day 1: NumPy Array Operations
====================================
NumPy 数组操作、广播、向量化
EEG 数据加载与整形练习
"""
import numpy as np

out_dir = '/tmp'

# ============================================================
# 1. 基本数组创建与索引
# ============================================================
print("=" * 60)
print("1. 基本数组创建与索引")
print("=" * 60)

data = np.load('/work/run/projects/bio-24/my_projects/learning-journey/tracks/brain-computer-interface/projects/output/results.npy', allow_pickle=True)
print(f"EEG shape: {data.shape}")  # (n_channels, n_times)

n_channels, n_times = data.shape
print(f"通道数: {n_channels}, 采样点数: {n_times}")

print(f"\n前5个采样点 (通道0):\n{data[0, :5]}")
print(f"通道0 最后5个采样点:\n{data[0, -5:]}")

slice_ch = data[8:12, 1000:2000]
print(f"\n通道8-11，采样点1000-2000 的 shape: {slice_ch.shape}")

print(f"\n索引 [::2] 每隔一个采样点: {data[0, ::2].shape}")

# ============================================================
# 2. 广播机制
# ============================================================
print("\n" + "=" * 60)
print("2. 广播机制")
print("=" * 60)

baseline = data[:, :500].mean(axis=1, keepdims=True)
corrected = data - baseline
print(f"Baseline shape: {baseline.shape}")
print(f"校正后 shape: {corrected.shape}")
print(f"校正前后 (通道0) 第500点: {data[0, 500]:.2f} -> {corrected[0, 500]:.2f}")

增益 = np.array([1.0, 1.5, 2.0, 1.2])
scaled = data[:4] * 增益[:, np.newaxis]
print(f"\n不同通道增益广播: {scaled.shape}")

# ============================================================
# 3. 统计计算
# ============================================================
print("\n" + "=" * 60)
print("3. 统计计算")
print("=" * 60)

rms = np.sqrt(np.mean(data**2, axis=1))
print(f"各通道 RMS: {rms[:5]}")
print(f"最大 RMS 通道: {np.argmax(rms)}")

var = np.var(data, axis=1)
print(f"\n各通道方差: {var[:5]}")
print(f"Mean across channels at t=100: {data[:, 100].mean():.4f}")

# ============================================================
# 4. 向量化操作
# ============================================================
print("\n" + "=" * 60)
print("4. 向量化操作")
print("=" * 60)

t = np.arange(n_times) / 256
freq = 10
sine_wave = np.sin(2 * np.pi * freq * t)
print(f"正弦波 shape: {sine_wave.shape}, 前5点: {sine_wave[:5]}")

cos_wave = np.cos(2 * np.pi * freq * t)
mixed = sine_wave + cos_wave
print(f"混合后 RMS: {np.sqrt(np.mean(mixed**2)):.4f}")

windowed = data * sine_wave[np.newaxis, :]
print(f"\n加窗后 shape: {windowed.shape}")

# ============================================================
# 5. EEG 数据整形
# ============================================================
print("\n" + "=" * 60)
print("5. EEG 数据整形")
print("=" * 60)

trials_data = data.reshape(n_channels, 10, n_times // 10)
print(f"重塑为 trials: {trials_data.shape} (channels, trials, times)")

trial_mean = trials_data.mean(axis=1)
print(f"trial 平均后: {trial_mean.shape}")

trial_std = trials_data.std(axis=1)
print(f"trial 标准差: {trial_std.shape}")

# z-score normalize across trials
z_scored = (trials_data - trial_mean[:, np.newaxis, :]) / (trial_std[:, np.newaxis, :] + 1e-8)
print(f"Z-score 校正后: {z_scored.shape}")

print("\n✅ Day 1 完成!")