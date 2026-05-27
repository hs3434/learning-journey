"""
Week 3 Day 5 练习：小波分析 + ICA 去伪迹
对比 CWT vs STFT，小波去噪，模拟 ICA 去眼眨
"""
import numpy as np
from scipy import signal as sig
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

out_dir = '/tmp/day5_plots'

# ============================================================
# 1. CWT vs STFT 对比 — 多频率成分信号
# ============================================================
fs = 250
duration = 4.0
t = np.arange(0, duration, 1/fs)
n_samples = len(t)

# 模拟信号：低频慢变化 + 高频瞬态
# 0-2s: 只有 5Hz (theta)
# 1-3s: 叠加 20Hz 瞬态 burst
# 2-4s: 只有 5Hz
np.random.seed(42)
theta = 50 * np.sin(2 * np.pi * 5 * t)
beta_burst = np.zeros(n_samples)
for i, ti in enumerate(t):
    if 1.0 <= ti <= 1.3 or 2.0 <= ti <= 2.3:
        beta_burst[i] = 30 * np.sin(2 * np.pi * 20 * ti)
    if 2.5 <= ti <= 2.8:
        beta_burst[i] = 25 * np.sin(2 * np.pi * 35 * ti)
noise = 5 * np.random.randn(n_samples)
eeg = theta + beta_burst + noise

# STFT
nperseg = 128
noverlap = 64
freqs_stft, times_stft, Sxx = sig.spectrogram(
    eeg, fs, window='hann', nperseg=nperseg, noverlap=noverlap, scaling='density'
)

# CWT (Morlet) — 使用 pywt 实现
import pywt
# 选择频率范围
cwt_freqs_target = np.linspace(1, 50, 100)
# 将频率转换为尺度: scale = fc / (f * dt), Morlet fc ≈ 6/(2*pi)
scales = 6 / (2 * np.pi * cwt_freqs_target * (1/fs))
cwt_coeffs, cwt_freqs_actual = pywt.cwt(eeg, scales, 'cmor6-1.0', sampling_period=1/fs)
cwt_freqs = np.array(cwt_freqs_target)

# 绘图
fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

# 时域
axes[0].plot(t, eeg, color='#333', linewidth=0.5)
axes[0].set_title('EEG Signal: 5Hz theta + 20Hz/35Hz beta bursts', fontsize=12)
axes[0].set_ylabel('Amplitude')

# STFT
freq_mask = freqs_stft <= 50
im1 = axes[1].pcolormesh(
    times_stft, freqs_stft[freq_mask],
    10 * np.log10(Sxx[freq_mask] + 1e-10),
    shading='gouraud', cmap='viridis', vmin=-10, vmax=25
)
axes[1].set_title(f'STFT (nperseg={nperseg}, fixed window)', fontsize=12, color='#2196F3')
axes[1].set_ylabel('Frequency (Hz)')
plt.colorbar(im1, ax=axes[1], label='PSD (dB)')

# CWT
freq_mask_cwt = cwt_freqs <= 50
# Sort by frequency for proper display
sort_idx = np.argsort(cwt_freqs[freq_mask_cwt])
cwt_display = np.abs(cwt_coeffs[freq_mask_cwt][sort_idx])
cwt_freq_display = cwt_freqs[freq_mask_cwt][sort_idx]

im2 = axes[2].pcolormesh(
    t, cwt_freq_display,
    10 * np.log10(cwt_display**2 + 1e-10),
    shading='gouraud', cmap='viridis', vmin=-10, vmax=25
)
axes[2].set_title('CWT (Morlet, adaptive window)', fontsize=12, color='#4CAF50')
axes[2].set_ylabel('Frequency (Hz)')
axes[2].set_xlabel('Time (s)')
plt.colorbar(im2, ax=axes[2], label='Power (dB)')

plt.tight_layout()
plt.savefig(f'{out_dir}_1_cwt_vs_stft.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图1已保存: {out_dir}_1_cwt_vs_stft.png")

# ============================================================
# 2. 小波去噪
# ============================================================
try:
    import pywt
    
    # 生成含噪信号
    t2 = np.arange(0, 2, 1/fs)
    clean_signal = np.sin(2 * np.pi * 10 * t2) + 0.5 * np.sin(2 * np.pi * 25 * t2)
    heavy_noise = 2.0 * np.random.randn(len(t2))
    noisy_signal = clean_signal + heavy_noise
    
    # 小波去噪
    wavelet = 'db4'
    level = 5
    coeffs = pywt.wavedec(noisy_signal, wavelet, level=level)
    
    # 软阈值 (universal threshold)
    sigma = np.median(np.abs(coeffs[-1])) / 0.6745
    threshold = sigma * np.sqrt(2 * np.log(len(noisy_signal)))
    denoised_coeffs = [pywt.threshold(c, threshold, mode='soft') for c in coeffs]
    denoised = pywt.waverec(denoised_coeffs, wavelet)
    denoised = denoised[:len(t2)]  # trim to match length
    
    # 绘图
    fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)
    
    axes[0].plot(t2, clean_signal, color='#4CAF50', linewidth=1)
    axes[0].set_title('Clean Signal (10Hz + 25Hz)', fontsize=11)
    axes[0].set_ylabel('Amplitude')
    
    axes[1].plot(t2, noisy_signal, color='gray', linewidth=0.5)
    axes[1].set_title('Noisy Signal (SNR ≈ 0dB)', fontsize=11, color='gray')
    
    axes[2].plot(t2, denoised, color='#2196F3', linewidth=1)
    axes[2].set_title(f'Wavelet Denoised (db4, soft threshold)', fontsize=11, color='#2196F3')
    
    # 对比
    axes[3].plot(t2, clean_signal, color='#4CAF50', linewidth=1.5, label='Clean')
    axes[3].plot(t2, denoised, color='#2196F3', linewidth=1, alpha=0.8, label='Denoised')
    axes[3].set_title('Clean vs Denoised Comparison', fontsize=11)
    axes[3].legend(loc='upper right')
    axes[3].set_xlabel('Time (s)')
    
    # 计算去噪效果
    mse_before = np.mean((noisy_signal - clean_signal)**2)
    mse_after = np.mean((denoised - clean_signal)**2)
    print(f"\n小波去噪效果:")
    print(f"  去噪前 MSE: {mse_before:.2f}")
    print(f"  去噪后 MSE: {mse_after:.2f}")
    print(f"  MSE 降低: {(1 - mse_after/mse_before)*100:.1f}%")
    
    # 小波分解可视化
    fig2, axes2 = plt.subplots(level+2, 1, figsize=(14, 12), sharex=True)
    axes2[0].plot(t2, noisy_signal, color='gray', linewidth=0.5)
    axes2[0].set_title('Noisy Signal', fontsize=11)
    
    labels = ['Approximation (a5)'] + [f'Detail d{i}' for i in range(level, 0, -1)]
    for i, (c, label) in enumerate(zip(coeffs, labels)):
        # Reconstruct each level for display
        rec = np.zeros(len(t2))
        rec_coeffs = [np.zeros_like(cc) for cc in coeffs]
        rec_coeffs[i] = c
        rec = pywt.waverec(rec_coeffs, wavelet)[:len(t2)]
        axes2[i+1].plot(t2, rec, linewidth=0.8)
        axes2[i+1].set_ylabel(label, fontsize=9)
        if i == 0:
            axes2[i+1].set_title('Low-freq approximation (signal body)', fontsize=10, color='#4CAF50')
        elif i >= level - 1:
            axes2[i+1].set_title(f'{label} (noise)', fontsize=10, color='#F44336')
    
    axes2[-1].set_xlabel('Time (s)')
    plt.tight_layout()
    plt.savefig(f'{out_dir}_2_wavelet_denoise.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"图2已保存: {out_dir}_2_wavelet_denoise.png")
    
    fig2_saved = True

except ImportError:
    print("pywt not installed, skipping wavelet denoise demo")
    fig2_saved = False

# ============================================================
# 3. 模拟 ICA 去眼眨伪迹
# ============================================================
n_channels = 8
n_timepoints = len(t)

# 模拟 4 个源信号
source1 = 30 * np.sin(2 * np.pi * 10 * t)  # alpha (脑电)
source2 = 20 * np.sin(2 * np.pi * 20 * t)  # beta (脑电)
source3 = 15 * np.sin(2 * np.pi * 5 * t)   # theta (脑电)
# 眼眨伪迹：不规则的尖锐偏转
eyeblink = np.zeros(n_timepoints)
blink_times = [0.8, 2.2, 3.5]
for bt in blink_times:
    blink_idx = np.argmin(np.abs(t - bt))
    blink_width = int(0.15 * fs)  # 150ms
    blink_env = np.exp(-0.5 * ((np.arange(-blink_width, blink_width+1) / (blink_width/3))**2))
    start = max(0, blink_idx - blink_width)
    end = min(n_timepoints, blink_idx + blink_width + 1)
    actual_blink = blink_env[start - (blink_idx - blink_width):end - (blink_idx - blink_width)]
    eyeblink[start:end] += 200 * actual_blink[:end-start]

S = np.vstack([source1, source2, source3, eyeblink])  # 4 sources

# 随机混合矩阵 (8 channels x 4 sources)
np.random.seed(123)
A = np.random.randn(n_channels, 4)
# 眼眨在额叶通道（前2个）权重更大
A[0, 3] = 3.0  # Fp1 强眼眨
A[1, 3] = 2.5  # Fp2 强眼眨

# 混合信号
X = A @ S  # 8 channels x n_timepoints

# 用 scipy 的 FastICA
from sklearn.decomposition import FastICA

ica = FastICA(n_components=4, random_state=42)
S_estimated = ica.fit_transform(X.T).T  # 4 components x n_timepoints
A_estimated = ica.mixing_

# 识别眼眨成分（方差最大或与额叶相关最高的）
# 简单方法：找最大绝对幅值的成分
max_amp = [np.max(np.abs(s)) for s in S_estimated]
blink_component = np.argmax(max_amp)
print(f"\nICA 结果:")
print(f"  识别眼眨成分: IC{blink_component} (最大幅值={max_amp[blink_component]:.1f})")

# 去除眼眨成分，重构
S_clean = S_estimated.copy()
S_clean[blink_component] = 0
X_clean = A_estimated @ S_clean

# 绘图
fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)

# 原始源信号（含眼眨）
ch_names = ['Fp1', 'Fp2', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2']
# 显示额叶通道（眼眨最明显）
for ch_idx in [0, 1]:
    axes[0].plot(t, X[ch_idx], linewidth=0.5, label=ch_names[ch_idx])
axes[0].set_title('Raw EEG (Fp1, Fp2) — Eyeblink artifacts visible', fontsize=11, color='#F44336')
axes[0].legend(loc='upper right')
axes[0].set_ylabel('Amplitude')

# ICA 分离出的成分
colors_ic = ['#2196F3', '#4CAF50', '#FF9800', '#F44336']
for i, (s, c) in enumerate(zip(S_estimated, colors_ic)):
    label = f'IC{i}' + (' ← EYE BLINK' if i == blink_component else '')
    lw = 1.5 if i == blink_component else 0.8
    axes[1].plot(t, s, color=c, linewidth=lw, label=label)
axes[1].set_title('ICA Components (Separated)', fontsize=11)
axes[1].legend(loc='upper right', fontsize=9)
axes[1].set_ylabel('Amplitude')

# 去除眼眨后
for ch_idx in [0, 1]:
    axes[2].plot(t, X_clean[ch_idx], linewidth=0.5, label=ch_names[ch_idx])
axes[2].set_title('Clean EEG (after removing eyeblink IC)', fontsize=11, color='#4CAF50')
axes[2].legend(loc='upper right')
axes[2].set_ylabel('Amplitude')

# 对比：原始 vs 去眼眨（Fp1）
axes[3].plot(t, X[0], color='#F44336', linewidth=0.5, alpha=0.6, label='Raw Fp1')
axes[3].plot(t, X_clean[0], color='#4CAF50', linewidth=0.8, label='Clean Fp1')
axes[3].set_title('Fp1: Before vs After ICA Artifact Removal', fontsize=11)
axes[3].legend(loc='upper right')
axes[3].set_xlabel('Time (s)')

plt.tight_layout()
plt.savefig(f'{out_dir}_3_ica_artifact_removal.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图3已保存: {out_dir}_3_ica_artifact_removal.png")

# ============================================================
# 4. 小波 vs STFT 分辨率对比（可视化）
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# STFT: 固定网格
stft_time_res = nperseg / fs
stft_freq_res = fs / nperseg
axes[0].set_title('STFT: Fixed Resolution', fontsize=12, color='#2196F3')
# 画固定网格
for f in np.arange(0, 50, stft_freq_res * 2):
    axes[0].axhline(f, color='#2196F3', alpha=0.3, linewidth=0.5)
for ti in np.arange(0, 4, stft_time_res):
    axes[0].axvline(ti, color='#2196F3', alpha=0.3, linewidth=0.5)
axes[0].set_xlabel('Time (s)')
axes[0].set_ylabel('Frequency (Hz)')
axes[0].set_xlim(0, 4)
axes[0].set_ylim(0, 50)
axes[0].text(2, 25, 'All cells\nsame size', ha='center', va='center', fontsize=14, color='#2196F3', fontweight='bold')

# CWT: 自适应网格
axes[1].set_title('CWT: Adaptive Resolution', fontsize=12, color='#4CAF50')
for f in [5, 10, 20, 35]:
    t_width = 6 / (2 * np.pi * f)  # 近似时间分辨率
    f_width = f / 6  # 近似频率分辨率
    rect = plt.Rectangle((2 - t_width, f - f_width/2), 2*t_width, f_width,
                          fill=False, edgecolor='#4CAF50', linewidth=1.5)
    axes[1].add_patch(rect)
    axes[1].text(2, f, f'{f}Hz', ha='center', va='center', fontsize=9, color='#4CAF50')
axes[1].set_xlabel('Time (s)')
axes[1].set_ylabel('Frequency (Hz)')
axes[1].set_xlim(0, 4)
axes[1].set_ylim(0, 50)
axes[1].text(2, 45, 'Low-freq: wide time, narrow freq\nHigh-freq: narrow time, wide freq', 
             ha='center', va='center', fontsize=10, color='#4CAF50', fontweight='bold')

plt.tight_layout()
plt.savefig(f'{out_dir}_4_resolution_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图4已保存: {out_dir}_4_resolution_comparison.png")

print("\n✅ Day 5 所有图表生成完毕!")
