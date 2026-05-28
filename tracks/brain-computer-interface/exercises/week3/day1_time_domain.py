"""
Week 3 Day 1: Time Domain Analysis
====================================
时域分析：均值、方差、RMS、峰值
计算 EEG 统计指标
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

out_dir = '/tmp'

# ============================================================
# 1. 基础统计量
# ============================================================
print("=" * 60)
print("1. 基础统计量")
print("=" * 60)

data_dir = '/work/run/projects/bio-24/my_projects/learning-journey/tracks/brain-computer-interface/projects/output'
data = np.load(f'{data_dir}/results.npy', allow_pickle=True)

ch0 = data[0]

print(f"通道0 均值: {ch0.mean():.6f}")
print(f"通道0 方差: {ch0.var():.6f}")
print(f"通道0 标准差: {ch0.std():.6f}")
print(f"通道0 最小值: {ch0.min():.6f}")
print(f"通道0 最大值: {ch0.max():.6f}")

# ============================================================
# 2. RMS 与峰值
# ============================================================
print("\n" + "=" * 60)
print("2. RMS 与峰值")
print("=" * 60)

rms = np.sqrt(np.mean(ch0**2))
print(f"RMS: {rms:.6f}")

# 峰值
peak = np.max(np.abs(ch0))
print(f"峰值 (|max|): {peak:.6f}")

# 峰峰值
peak_to_peak = ch0.max() - ch0.min()
print(f"峰峰值: {peak_to_peak:.6f}")

# ============================================================
# 3. 滑动窗口统计
# ============================================================
print("\n" + "=" * 60)
print("3. 滑动窗口统计")
print("=" * 60)

fs = 256
window_size = int(fs * 0.5)
hop_size = int(fs * 0.25)

n_windows = (len(ch0) - window_size) // hop_size + 1
windows_mean = np.zeros(n_windows)
windows_std = np.zeros(n_windows)
windows_rms = np.zeros(n_windows)

for i in range(n_windows):
    start = i * hop_size
    end = start + window_size
    window = ch0[start:end]
    windows_mean[i] = window.mean()
    windows_std[i] = window.std()
    windows_rms[i] = np.sqrt(np.mean(window**2))

print(f"滑动窗口数: {n_windows}")
print(f"平均 RMS: {windows_rms.mean():.6f}")
print(f"RMS 标准差: {windows_rms.std():.6f}")

# ============================================================
# 4. 通道间相关性
# ============================================================
print("\n" + "=" * 60)
print("4. 通道间相关性")
print("=" * 60)

corr_matrix = np.corrcoef(data[:10])
print(f"前10通道相关系数矩阵 shape: {corr_matrix.shape}")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].plot(ch0[:1000], linewidth=0.5)
axes[0].set_title('EEG Channel 0 (first 1000 samples)')
axes[0].set_xlabel('Sample')
axes[0].set_ylabel('Amplitude')

im = axes[1].imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1)
axes[1].set_title('Channel Correlation Matrix (ch 0-9)')
axes[1].set_xlabel('Channel')
axes[1].set_ylabel('Channel')
plt.colorbar(im, ax=axes[1])

plt.tight_layout()
plt.savefig(f'{out_dir}/day1_time_domain.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"\n图已保存: {out_dir}/day1_time_domain.png")

print("\n✅ Day 1 完成!")