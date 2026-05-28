"""
Week 3 Day 2: Frequency Domain Analysis
========================================
频域分析：FFT、功率谱密度
绘制 EEG 频谱图
"""
import numpy as np
from scipy import signal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

out_dir = '/tmp'

# ============================================================
# 1. FFT 基本计算
# ============================================================
print("=" * 60)
print("1. FFT 基本计算")
print("=" * 60)

data_dir = '/work/run/projects/bio-24/my_projects/learning-journey/tracks/brain-computer-interface/projects/output'
data = np.load(f'{data_dir}/results.npy', allow_pickle=True)

fs = 256
ch0 = data[0]

n = len(ch0)
fft_result = np.fft.fft(ch0)
freqs = np.fft.fftfreq(n, 1/fs)

positive_mask = freqs >= 0
freqs_positive = freqs[positive_mask]
magnitude = np.abs(fft_result)[positive_mask]

print(f"频率点数: {len(freqs_positive)}")
print(f"频率分辨率: {fs/n:.3f} Hz")
print(f"最大频率 (Nyquist): {fs/2:.1f} Hz")

# ============================================================
# 2. 功率谱密度 (Welch)
# ============================================================
print("\n" + "=" * 60)
print("2. 功率谱密度 (Welch)")
print("=" * 60)

nperseg = 256
freqs_welch, psd = signal.welch(ch0, fs, nperseg=nperseg)

print(f"Welch PSD 频率点数: {len(freqs_welch)}")
print(f"Alpha 频段 (8-13Hz) 平均功率: {psd[(freqs_welch >= 8) & (freqs_welch <= 13)].mean():.6f}")
print(f"Beta 频段 (13-30Hz) 平均功率: {psd[(freqs_welch >= 13) & (freqs_welch <= 30)].mean():.6f}")

# ============================================================
# 3. 频段功率计算
# ============================================================
print("\n" + "=" * 60)
print("3. 频段功率计算")
print("=" * 60)

bands = {
    'Delta (0.5-4Hz)': (0.5, 4),
    'Theta (4-8Hz)': (4, 8),
    'Alpha (8-13Hz)': (8, 13),
    'Beta (13-30Hz)': (13, 30),
    'Gamma (30-100Hz)': (30, 100)
}

for band_name, (low, high) in bands.items():
    band_idx = (freqs_welch >= low) & (freqs_welch <= high)
    band_power = np.mean(psd[band_idx])
    print(f"{band_name}: {band_power:.6f}")

# ============================================================
# 4. 多通道频谱对比
# ============================================================
print("\n" + "=" * 60)
print("4. 多通道频谱对比")
print("=" * 60)

n_channels = 4
freqs_arr = []
psd_arr = []
for i in range(n_channels):
    f, p = signal.welch(data[i], fs, nperseg=nperseg)
    freqs_arr.append(f)
    psd_arr.append(p)

# ============================================================
# 5. 可视化
# ============================================================
print("\n" + "=" * 60)
print("5. 可视化")
print("=" * 60)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

axes[0, 0].semilogy(freqs_welch, psd, linewidth=0.5)
axes[0, 0].set_xlabel('Frequency (Hz)')
axes[0, 0].set_ylabel('Power/Frequency (dB/Hz)')
axes[0, 0].set_title('Power Spectral Density (Channel 0)')
axes[0, 0].set_xlim(0, 50)
axes[0, 0].grid(True, alpha=0.3)

for i, (f, p) in enumerate(zip(freqs_arr, psd_arr)):
    axes[0, 1].semilogy(f, p, linewidth=0.5, label=f'Ch {i}', alpha=0.8)
axes[0, 1].set_xlabel('Frequency (Hz)')
axes[0, 1].set_ylabel('Power/Frequency (dB/Hz)')
axes[0, 1].set_title('PSD Comparison (4 channels)')
axes[0, 1].set_xlim(0, 50)
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

band_names = list(bands.keys())
band_powers = []
for band_name, (low, high) in bands.items():
    band_idx = (freqs_welch >= low) & (freqs_welch <= high)
    band_powers.append(np.mean(psd[band_idx]))

axes[1, 0].bar(band_names, band_powers)
axes[1, 0].set_ylabel('Power')
axes[1, 0].set_title('Band Power Distribution')
axes[1, 0].tick_params(axis='x', rotation=45)

for i, (f, p) in enumerate(zip(freqs_arr, psd_arr)):
    axes[1, 1].semilogy(f, p, linewidth=0.5, alpha=0.5)
axes[1, 1].axvline(10, color='red', linestyle='--', label='Alpha peak')
axes[1, 1].axvline(20, color='orange', linestyle='--', label='Beta peak')
axes[1, 1].set_xlabel('Frequency (Hz)')
axes[1, 1].set_ylabel('Power/Frequency (dB/Hz)')
axes[1, 1].set_title('All Channels PSD with Markers')
axes[1, 1].set_xlim(0, 50)
axes[1, 1].legend()

plt.tight_layout()
plt.savefig(f'{out_dir}/day2_freq_domain.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图已保存: {out_dir}/day2_freq_domain.png")

print("\n✅ Day 2 完成!")