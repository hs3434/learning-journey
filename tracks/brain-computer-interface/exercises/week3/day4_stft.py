"""
Week 3 Day 4 练习：STFT 时频分析
模拟运动想象 EEG，展示 ERD/ERS 现象
"""
import numpy as np
from scipy import signal as sig
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 1. 生成模拟运动想象 EEG
# ============================================================
fs = 250
duration = 6.0  # 6秒: 2秒静息 + 2秒运动想象 + 2秒恢复
t = np.arange(0, duration, 1/fs)
n_samples = len(t)

# 事件时间点
t_cue = 2.0    # 运动想象提示（第2秒）
t_relax = 4.0  # 放松提示（第4秒）

# 模拟 alpha(10Hz) 和 beta(20Hz) 带有 ERD/ERS
np.random.seed(42)

# 基线 alpha 功率
alpha_base = 50
beta_base = 30

# ERD: 运动想象期间 alpha/beta 功率下降
# ERS: 运动结束后 alpha/beta 功率回升(反弹)
alpha_amplitude = np.ones(n_samples) * alpha_base
beta_amplitude = np.ones(n_samples) * beta_base

for i, ti in enumerate(t):
    if t_cue <= ti < t_relax:
        # ERD: 功率逐渐下降到 40%
        progress = (ti - t_cue) / (t_relax - t_cue)
        erd_factor = 1.0 - 0.6 * (1 - np.exp(-3 * progress))  # 指数下降
        alpha_amplitude[i] *= erd_factor
        beta_amplitude[i] *= erd_factor
    elif ti >= t_relax:
        # ERS: 功率反弹超过基线，然后恢复
        progress = (ti - t_relax)
        ers_factor = 1.0 + 0.5 * np.exp(-2 * progress) * np.sin(2 * np.pi * 1.5 * progress)
        alpha_amplitude[i] *= max(0.5, ers_factor)
        beta_amplitude[i] *= max(0.5, ers_factor)

# 生成信号
alpha_signal = alpha_amplitude * np.sin(2 * np.pi * 10 * t + np.random.randn(n_samples) * 0.1)
beta_signal = beta_amplitude * np.sin(2 * np.pi * 20 * t + np.random.randn(n_samples) * 0.1)
drift = 30 * np.sin(2 * np.pi * 0.3 * t)
noise = 8 * np.random.randn(n_samples)

eeg = alpha_signal + beta_signal + drift + noise

# 带通滤波
nyq = 0.5 * fs
b_bp, a_bp = sig.butter(4, [1.0/nyq, 40.0/nyq], btype='band')
eeg_filtered = sig.filtfilt(b_bp, a_bp, eeg)

print(f"信号: {duration}秒, fs={fs}Hz, {n_samples}采样点")
print(f"事件: cue@{t_cue}s, relax@{t_relax}s")
print(f"ERD: 运动想象期间alpha/beta功率下降至40%")
print(f"ERS: 恢复期间功率反弹超过基线")

# ============================================================
# 2. 不同窗口长度的 STFT 对比
# ============================================================
out_dir = '/tmp/day4_plots'

fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)

# 原始时域信号
axes[0].plot(t, eeg_filtered, color='#333333', linewidth=0.5)
axes[0].axvline(t_cue, color='red', linestyle='--', linewidth=1.5, label='Cue (MI start)')
axes[0].axvline(t_relax, color='green', linestyle='--', linewidth=1.5, label='Relax')
axes[0].set_title('Filtered EEG (1-40Hz) — Time Domain', fontsize=12)
axes[0].set_ylabel('Amplitude')
axes[0].legend(loc='upper right')

# 三种窗口长度的 STFT
window_sizes = [64, 128, 256]
colormaps = ['viridis', 'plasma', 'inferno']

for idx, (nperseg, cmap) in enumerate(zip(window_sizes, colormaps)):
    noverlap = nperseg // 2
    freqs, times, Sxx = sig.spectrogram(
        eeg_filtered, fs, 
        window='hann', 
        nperseg=nperseg, 
        noverlap=noverlap,
        scaling='density'
    )
    
    # 只显示 0-40Hz
    freq_mask = freqs <= 40
    
    im = axes[idx+1].pcolormesh(
        times, freqs[freq_mask], 
        10 * np.log10(Sxx[freq_mask] + 1e-10),
        shading='gouraud', 
        cmap=cmap,
        vmin=-20, vmax=30
    )
    axes[idx+1].axvline(t_cue, color='red', linestyle='--', linewidth=1.5)
    axes[idx+1].axvline(t_relax, color='green', linestyle='--', linewidth=1.5)
    
    freq_res = fs / nperseg
    time_res = nperseg / fs
    axes[idx+1].set_title(
        f'STFT nperseg={nperseg} | freq_res={freq_res:.1f}Hz, time_res={time_res:.0f}ms',
        fontsize=11
    )
    axes[idx+1].set_ylabel('Frequency (Hz)')
    plt.colorbar(im, ax=axes[idx+1], label='PSD (dB)')

axes[3].set_xlabel('Time (s)')
plt.tight_layout()
plt.savefig(f'{out_dir}_1_window_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"\n图1已保存: {out_dir}_1_window_comparison.png")

# ============================================================
# 3. ERD/ERS 可视化 — 频段功率随时间变化
# ============================================================
fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

# 用 nperseg=128 (折中方案)
nperseg = 128
noverlap = nperseg // 2
freqs, times, Sxx = sig.spectrogram(
    eeg_filtered, fs,
    window='hann',
    nperseg=nperseg,
    noverlap=noverlap,
    scaling='density'
)

# 完整时频图
freq_mask = freqs <= 40
im = axes[0].pcolormesh(
    times, freqs[freq_mask],
    10 * np.log10(Sxx[freq_mask] + 1e-10),
    shading='gouraud', cmap='RdBu_r',
    vmin=-20, vmax=30
)
axes[0].axvline(t_cue, color='red', linestyle='--', linewidth=1.5, label='Cue')
axes[0].axvline(t_relax, color='green', linestyle='--', linewidth=1.5, label='Relax')
axes[0].set_title('STFT Spectrogram (nperseg=128)', fontsize=12)
axes[0].set_ylabel('Frequency (Hz)')
axes[0].legend(loc='upper right')
plt.colorbar(im, ax=axes[0], label='PSD (dB)')

# Alpha 频段 (8-13Hz) 功率随时间变化
alpha_mask = (freqs >= 8) & (freqs <= 13)
alpha_power = np.mean(Sxx[alpha_mask], axis=0)
alpha_power_db = 10 * np.log10(alpha_power + 1e-10)

# 基线归一化 (用前2秒作为基线)
baseline_mask = times < t_cue
baseline_mean = np.mean(alpha_power_db[baseline_mask])
alpha_erd = alpha_power_db - baseline_mean

axes[1].plot(times, alpha_erd, color='#2196F3', linewidth=1.5)
axes[1].axvline(t_cue, color='red', linestyle='--', linewidth=1.5)
axes[1].axvline(t_relax, color='green', linestyle='--', linewidth=1.5)
axes[1].axhline(0, color='gray', linestyle='-', linewidth=0.5)
axes[1].fill_between(times, alpha_erd, 0, where=alpha_erd < 0, 
                      color='#2196F3', alpha=0.3, label='ERD (power decrease)')
axes[1].fill_between(times, alpha_erd, 0, where=alpha_erd > 0,
                      color='#F44336', alpha=0.3, label='ERS (power increase)')
axes[1].set_title('Alpha Band (8-13Hz) — ERD/ERS', fontsize=12, color='#2196F3')
axes[1].set_ylabel('Power (dB rel. baseline)')
axes[1].legend(loc='upper right')

# Beta 频段 (13-30Hz) 功率随时间变化
beta_mask = (freqs >= 13) & (freqs <= 30)
beta_power = np.mean(Sxx[beta_mask], axis=0)
beta_power_db = 10 * np.log10(beta_power + 1e-10)
baseline_mean_beta = np.mean(beta_power_db[baseline_mask])
beta_erd = beta_power_db - baseline_mean_beta

axes[2].plot(times, beta_erd, color='#4CAF50', linewidth=1.5)
axes[2].axvline(t_cue, color='red', linestyle='--', linewidth=1.5)
axes[2].axvline(t_relax, color='green', linestyle='--', linewidth=1.5)
axes[2].axhline(0, color='gray', linestyle='-', linewidth=0.5)
axes[2].fill_between(times, beta_erd, 0, where=beta_erd < 0,
                      color='#4CAF50', alpha=0.3, label='ERD (power decrease)')
axes[2].fill_between(times, beta_erd, 0, where=beta_erd > 0,
                      color='#F44336', alpha=0.3, label='ERS (power increase)')
axes[2].set_title('Beta Band (13-30Hz) — ERD/ERS', fontsize=12, color='#4CAF50')
axes[2].set_ylabel('Power (dB rel. baseline)')
axes[2].set_xlabel('Time (s)')
axes[2].legend(loc='upper right')

plt.tight_layout()
plt.savefig(f'{out_dir}_2_erd_ers.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图2已保存: {out_dir}_2_erd_ers.png")

# ============================================================
# 4. FFT vs STFT 对比 — 为什么需要 STFT
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 8))

# 全段 FFT
freqs_fft = np.fft.rfftfreq(n_samples, 1/fs)
fft_result = np.abs(np.fft.rfft(eeg_filtered))**2 / n_samples
axes[0, 0].semilogy(freqs_fft, fft_result, color='gray', linewidth=0.8)
axes[0, 0].set_xlim(0, 40)
axes[0, 0].set_title('Full FFT (6 seconds)', fontsize=11)
axes[0, 0].set_ylabel('Power')
axes[0, 0].axvspan(8, 13, alpha=0.1, color='blue', label='alpha')
axes[0, 0].axvspan(13, 30, alpha=0.1, color='green', label='beta')
axes[0, 0].legend()

# 分段 FFT
# 静息段 (0-2s)
rest_mask = t < t_cue
freqs_rest = np.fft.rfftfreq(np.sum(rest_mask), 1/fs)
fft_rest = np.abs(np.fft.rfft(eeg_filtered[rest_mask]))**2 / np.sum(rest_mask)
axes[0, 1].semilogy(freqs_rest, fft_rest, color='#2196F3', linewidth=1, label='Rest (0-2s)')

# 运动想象段 (2-4s)
mi_mask = (t >= t_cue) & (t < t_relax)
freqs_mi = np.fft.rfftfreq(np.sum(mi_mask), 1/fs)
fft_mi = np.abs(np.fft.rfft(eeg_filtered[mi_mask]))**2 / np.sum(mi_mask)
axes[0, 1].semilogy(freqs_mi, fft_mi, color='#F44336', linewidth=1, label='MI (2-4s)')

# 恢复段 (4-6s)
rec_mask = t >= t_relax
freqs_rec = np.fft.rfftfreq(np.sum(rec_mask), 1/fs)
fft_rec = np.abs(np.fft.rfft(eeg_filtered[rec_mask]))**2 / np.sum(rec_mask)
axes[0, 1].semilogy(freqs_rec, fft_rec, color='#4CAF50', linewidth=1, label='Recovery (4-6s)')

axes[0, 1].set_xlim(0, 40)
axes[0, 1].set_title('Segmented FFT (3 periods)', fontsize=11)
axes[0, 1].set_ylabel('Power')
axes[0, 1].legend()

# STFT 时频图
nperseg = 128
noverlap = nperseg // 2
freqs_stft, times_stft, Sxx_stft = sig.spectrogram(
    eeg_filtered, fs, window='hann',
    nperseg=nperseg, noverlap=noverlap, scaling='density'
)
freq_mask = freqs_stft <= 40
im = axes[1, 0].pcolormesh(
    times_stft, freqs_stft[freq_mask],
    10 * np.log10(Sxx_stft[freq_mask] + 1e-10),
    shading='gouraud', cmap='hot', vmin=-20, vmax=30
)
axes[1, 0].axvline(t_cue, color='cyan', linestyle='--', linewidth=1.5)
axes[1, 0].axvline(t_relax, color='cyan', linestyle='--', linewidth=1.5)
axes[1, 0].set_title('STFT Spectrogram', fontsize=11)
axes[1, 0].set_ylabel('Frequency (Hz)')
axes[1, 0].set_xlabel('Time (s)')
plt.colorbar(im, ax=axes[1, 0], label='PSD (dB)')

# Alpha 功率时间曲线
alpha_mask_stft = (freqs_stft >= 8) & (freqs_stft <= 13)
alpha_pwr = np.mean(Sxx_stft[alpha_mask_stft], axis=0)
alpha_pwr_db = 10 * np.log10(alpha_pwr + 1e-10)
bl = np.mean(alpha_pwr_db[times_stft < t_cue])
alpha_erd_curve = alpha_pwr_db - bl

axes[1, 1].plot(times_stft, alpha_erd_curve, color='#2196F3', linewidth=1.5)
axes[1, 1].axvline(t_cue, color='red', linestyle='--', linewidth=1.5, label='Cue')
axes[1, 1].axvline(t_relax, color='green', linestyle='--', linewidth=1.5, label='Relax')
axes[1, 1].axhline(0, color='gray', linestyle='-', linewidth=0.5)
axes[1, 1].fill_between(times_stft, alpha_erd_curve, 0, 
                          where=alpha_erd_curve < 0, color='blue', alpha=0.2)
axes[1, 1].set_title('Alpha ERD/ERS Curve', fontsize=11)
axes[1, 1].set_ylabel('Power (dB)')
axes[1, 1].set_xlabel('Time (s)')
axes[1, 1].legend()

plt.tight_layout()
plt.savefig(f'{out_dir}_3_fft_vs_stft.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图3已保存: {out_dir}_3_fft_vs_stft.png")

# ============================================================
# 5. 窗函数对比 — Hann vs Boxcar vs Hamming
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 8))

windows = [('boxcar', 'Rectangular (no window)'), 
           ('hann', 'Hann'), 
           ('hamming', 'Hamming'),
           ('blackman', 'Blackman')]

for idx, (win_name, win_label) in enumerate(windows):
    ax = axes[idx // 2, idx % 2]
    
    freqs_w, times_w, Sxx_w = sig.spectrogram(
        eeg_filtered, fs, window=win_name,
        nperseg=128, noverlap=64, scaling='density'
    )
    freq_mask_w = freqs_w <= 40
    
    im = ax.pcolormesh(
        times_w, freqs_w[freq_mask_w],
        10 * np.log10(Sxx_w[freq_mask_w] + 1e-10),
        shading='gouraud', cmap='viridis', vmin=-20, vmax=30
    )
    ax.axvline(t_cue, color='red', linestyle='--', linewidth=1)
    ax.axvline(t_relax, color='green', linestyle='--', linewidth=1)
    ax.set_title(f'Window: {win_label}', fontsize=11)
    ax.set_ylabel('Frequency (Hz)')
    if idx >= 2:
        ax.set_xlabel('Time (s)')

plt.tight_layout()
plt.savefig(f'{out_dir}_4_window_functions.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图4已保存: {out_dir}_4_window_functions.png")

print("\n✅ Day 4 所有图表生成完毕!")
