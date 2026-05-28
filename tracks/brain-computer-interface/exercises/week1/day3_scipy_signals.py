"""
Week 1 Day 3: SciPy Statistics and Signal Basics
===============================================
SciPy 统计、插值、信号基础
简单滤波操作
"""
import numpy as np
from scipy import signal, stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

out_dir = '/tmp'

# ============================================================
# 1. 统计计算
# ============================================================
print("=" * 60)
print("1. 统计计算")
print("=" * 60)

data_dir = '/work/run/projects/bio-24/my_projects/learning-journey/tracks/brain-computer-interface/projects/output'
data = np.load(f'{data_dir}/results.npy', allow_pickle=True)

ch0 = data[0]

print(f"通道0 均值: {ch0.mean():.4f}")
print(f"通道0 标准差: {ch0.std():.4f}")
print(f"通道0 偏度: {stats.skew(ch0):.4f}")
print(f"通道0 峰度: {stats.kurtosis(ch0):.4f}")

# ============================================================
# 2. 概率分布
# ============================================================
print("\n" + "=" * 60)
print("2. 概率分布")
print("=" * 60)

kurtosis_vals = []
for i in range(data.shape[0]):
    k = stats.kurtosis(data[i])
    kurtosis_vals.append(k)

print(f"各通道峰度范围: {min(kurtosis_vals):.2f} ~ {max(kurtosis_vals):.2f}")

# ============================================================
# 3. 插值
# ============================================================
print("\n" + "=" * 60)
print("3. 插值")
print("=" * 60)

fs = 256
t_original = np.arange(0, 1, 1/fs)
t_downsampled = t_original[::4]
data_downsampled = ch0[::4]

t_highres = np.arange(0, 1, 1/(fs*4))

from scipy.interpolate import interp1d
f = interp1d(t_downsampled, data_downsampled, kind='cubic')
data_upsampled = f(t_highres)

print(f"原始: {ch0.shape}, 下采样: {data_downsampled.shape}, 上采样: {data_upsampled.shape}")

# ============================================================
# 4. 简单滤波
# ============================================================
print("\n" + "=" * 60)
print("4. 简单滤波")
print("=" * 60)

nyq = fs / 2
low, high = 0.5 / nyq, 40 / nyq
b, a = signal.butter(4, [low, high], btype='band')
filtered = signal.filtfilt(b, a, ch0)

print(f"滤波前 RMS: {np.sqrt(np.mean(ch0**2)):.4f}")
print(f"滤波后 RMS: {np.sqrt(np.mean(filtered**2)):.4f}")

# ============================================================
# 5. 相关与卷积
# ============================================================
print("\n" + "=" * 60)
print("5. 相关与卷积")
print("=" * 60)

corr = np.correlate(ch0[:1000], ch0[500:1500], mode='valid')
print(f"互相关结果长度: {len(corr)}")

conv = np.convolve(ch0[:100], ch0[50:150], mode='valid')
print(f"卷积结果长度: {len(conv)}")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

axes[0, 0].plot(ch0[:500], alpha=0.7)
axes[0, 0].set_title('Original EEG (first 500 samples)')
axes[0, 0].set_ylabel('Amplitude')

axes[0, 1].plot(filtered[:500], alpha=0.7)
axes[0, 1].set_title('Filtered EEG (0.5-40Hz bandpass)')

axes[1, 0].hist(ch0, bins=50, alpha=0.7, density=True)
axes[1, 0].set_title('EEG Amplitude Distribution')

axes[1, 1].psd(ch0, Fs=fs, label='Original')
axes[1, 1].psd(filtered, Fs=fs, label='Filtered')
axes[1, 1].set_title('Power Spectral Density')
axes[1, 1].legend()

plt.tight_layout()
plt.savefig(f'{out_dir}/day3_scipy_signals.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"\n图已保存: {out_dir}/day3_scipy_signals.png")

print("\n✅ Day 3 完成!")