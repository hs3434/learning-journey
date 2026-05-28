"""
Week 1 Day 4: Matplotlib Visualization
======================================
Matplotlib 可视化、subplot、多图
EEG 时序图绘制
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

out_dir = '/tmp'

# ============================================================
# 1. 基础绘图
# ============================================================
print("=" * 60)
print("1. 基础绘图")
print("=" * 60)

data_dir = '/work/run/projects/bio-24/my_projects/learning-journey/tracks/brain-computer-interface/projects/output'
data = np.load(f'{data_dir}/results.npy', allow_pickle=True)

fs = 256
t = np.arange(data.shape[1]) / fs

plt.figure(figsize=(14, 5))
plt.plot(t, data[0], linewidth=0.5)
plt.xlabel('Time (s)')
plt.ylabel('Amplitude (μV)')
plt.title('EEG Channel 0')
plt.tight_layout()
plt.savefig(f'{out_dir}/day4_basic_plot.png', dpi=150)
plt.close()
print("Saved basic plot")

# ============================================================
# 2. 多子图
# ============================================================
print("\n" + "=" * 60)
print("2. 多子图")
print("=" * 60)

fig, axes = plt.subplots(3, 1, figsize=(14, 10))

for i in range(3):
    axes[i].plot(t, data[i], linewidth=0.3)
    axes[i].set_ylabel(f'Ch {i}')
    if i == 2:
        axes[i].set_xlabel('Time (s)')

plt.tight_layout()
plt.savefig(f'{out_dir}/day4_subplots.png', dpi=150)
plt.close()
print("Saved subplots")

# ============================================================
# 3. 特殊格式
# ============================================================
print("\n" + "=" * 60)
print("3. 特殊格式")
print("=" * 60)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

axes[0, 0].scatter(t[::10], data[0, ::10], s=1, alpha=0.5)
axes[0, 0].set_title('Scatter Plot')

axes[0, 1].hist(data[0], bins=100, alpha=0.7)
axes[0, 1].set_title('Histogram')

axes[1, 0].imshow(data[:, :1000], aspect='auto', cmap='viridis')
axes[1, 0].set_title('Image (all channels, first 1000 samples)')

axes[1, 1].stem(t[:100], data[0, :100], linefmt='-', markerfmt=',')
axes[1, 1].set_title('Stem Plot')

plt.tight_layout()
plt.savefig(f'{out_dir}/day4_special_plots.png', dpi=150)
plt.close()
print("Saved special plots")

# ============================================================
# 4. 多图对比
# ============================================================
print("\n" + "=" * 60)
print("4. 多图对比")
print("=" * 60)

from scipy.signal import butter, filtfilt
nyq = fs / 2
b, a = butter(4, [0.5/nyq, 40/nyq], btype='band')
filtered = filtfilt(b, a, data[0])

fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

axes[0].plot(t, data[0], label='Original', alpha=0.7)
axes[0].set_title('Original EEG')
axes[0].set_ylabel('Amplitude')

axes[1].plot(t, filtered, label='Filtered (0.5-40Hz)', color='orange')
axes[1].set_title('Filtered EEG')
axes[1].set_ylabel('Amplitude')
axes[1].set_xlabel('Time (s)')

for ax in axes:
    ax.legend()

plt.tight_layout()
plt.savefig(f'{out_dir}/day4_comparison.png', dpi=150)
plt.close()
print("Saved comparison plot")

# ============================================================
# 5. EEG 多通道瀑布图
# ============================================================
print("\n" + "=" * 60)
print("5. EEG 多通道瀑布图")
print("=" * 60)

n_channels = 8
fig, ax = plt.subplots(figsize=(14, 10))

offset = 50
for i in range(n_channels):
    ax.plot(t, data[i] * 1e6 + i * offset, linewidth=0.3, label=f'Ch {i}')

ax.set_xlabel('Time (s)')
ax.set_ylabel('Channels (offset)')
ax.set_title('EEG Channels (offset for clarity)')
ax.legend(loc='upper right')

plt.tight_layout()
plt.savefig(f'{out_dir}/day4_waterfall.png', dpi=150)
plt.close()
print("Saved waterfall plot")

print("\n✅ Day 4 完成!")