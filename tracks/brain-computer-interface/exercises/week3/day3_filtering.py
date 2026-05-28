"""
Week 3 Day 3 练习：EEG 滤波实战
对比 FIR vs IIR，filtfilt vs lfilter，notch 滤波
"""
import numpy as np
from scipy import signal as sig
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 1. 生成模拟 EEG 信号
# ============================================================
fs = 250          # 采样率 250Hz
duration = 2.0    # 2秒
t = np.arange(0, duration, 1/fs)
n_samples = len(t)

# 模拟EEG：alpha(10Hz) + beta(20Hz) + 漂移(0.2Hz) + 50Hz工频 + 噪声
alpha = 50 * np.sin(2 * np.pi * 10 * t)       # alpha 频段
beta = 20 * np.sin(2 * np.pi * 20 * t)        # beta 频段
drift = 80 * np.sin(2 * np.pi * 0.2 * t)      # 低频漂移
powerline = 30 * np.sin(2 * np.pi * 50 * t)   # 50Hz 工频干扰
noise = 10 * np.random.randn(n_samples)        # 白噪声

eeg_raw = alpha + beta + drift + powerline + noise

print(f"信号长度: {n_samples} 采样点, 采样率: {fs} Hz")
print(f"信号组成: alpha(10Hz) + beta(20Hz) + 漂移(0.2Hz) + 50Hz工频 + 噪声")

# ============================================================
# 2. IIR 带通滤波 (0.5-40Hz) — 用 filtfilt 零相位
# ============================================================
nyq = 0.5 * fs
low = 0.5 / nyq
high = 40.0 / nyq
b_iir, a_iir = sig.butter(4, [low, high], btype='band')
eeg_iir_filtfilt = sig.filtfilt(b_iir, a_iir, eeg_raw)

print(f"\nIIR Butterworth 带通 0.5-40Hz:")
print(f"  阶数: 4, 系数 b 长度: {len(b_iir)}, a 长度: {len(a_iir)}")

# ============================================================
# 3. IIR 带通滤波 — 用 lfilter（有相位延迟）
# ============================================================
eeg_iir_lfilter = sig.lfilter(b_iir, a_iir, eeg_raw)

# ============================================================
# 4. FIR 带通滤波 (0.5-40Hz) — 用 filtfilt 零相位
# ============================================================
numtaps = 101  # 滤波器长度（阶数 = numtaps - 1）
b_fir = sig.firwin(numtaps, [0.5, 40.0], pass_zero='bandpass', fs=fs)
eeg_fir_filtfilt = sig.filtfilt(b_fir, [1.0], eeg_raw)

print(f"\nFIR 带通 0.5-40Hz:")
print(f"  阶数: {numtaps-1}, 系数长度: {len(b_fir)}")
print(f"  群延迟: {(numtaps-1)/2} 个采样点 = {(numtaps-1)/2/fs*1000:.1f} ms")

# ============================================================
# 5. FIR 带通滤波 — 用 lfilter（有群延迟）
# ============================================================
eeg_fir_lfilter = sig.lfilter(b_fir, [1.0], eeg_raw)

# ============================================================
# 6. Notch 滤波（去50Hz工频）
# ============================================================
w0 = 50.0 / (fs / 2)
Q = 30
b_notch, a_notch = sig.iirnotch(w0, Q)
eeg_notch = sig.filtfilt(b_notch, a_notch, eeg_raw)

print(f"\nNotch 滤波器 50Hz:")
print(f"  Q因子: {Q}, 3dB带宽: {50/Q:.1f} Hz")

# ============================================================
# 7. 先带通 + 再 notch（BCI 标准流程）
# ============================================================
eeg_bandpass = sig.filtfilt(b_iir, a_iir, eeg_raw)
eeg_full_pipeline = sig.filtfilt(b_notch, a_notch, eeg_bandpass)

# ============================================================
# 绘图
# ============================================================
out_dir = '/tmp/day3_plots'

# --- 图1: filtfilt vs lfilter 对比 ---
fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)

axes[0].plot(t, eeg_raw, color='gray', alpha=0.7, linewidth=0.5)
axes[0].set_title('Raw EEG (alpha 10Hz + beta 20Hz + drift 0.2Hz + 50Hz + noise)', fontsize=11)
axes[0].set_ylabel('Amplitude')

axes[1].plot(t, eeg_iir_filtfilt, color='#2196F3', linewidth=0.8)
axes[1].set_title('IIR + filtfilt (zero-phase, zero delay)', fontsize=11, color='#2196F3')
axes[1].set_ylabel('Amplitude')

axes[2].plot(t, eeg_iir_lfilter, color='#F44336', linewidth=0.8)
axes[2].set_title('IIR + lfilter (causal, has phase delay)', fontsize=11, color='#F44336')
axes[2].set_ylabel('Amplitude')

axes[3].plot(t, eeg_iir_filtfilt, color='#2196F3', linewidth=0.8, label='filtfilt (zero-phase)')
axes[3].plot(t, eeg_iir_lfilter, color='#F44336', linewidth=0.8, alpha=0.6, label='lfilter (with delay)')
axes[3].set_title('Overlay: filtfilt vs lfilter', fontsize=11)
axes[3].set_ylabel('Amplitude')
axes[3].legend(loc='upper right')
axes[3].set_xlabel('Time (s)')

plt.tight_layout()
plt.savefig(f'{out_dir}_1_filtfilt_vs_lfilter.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"\n图1已保存: {out_dir}_1_filtfilt_vs_lfilter.png")

# --- 图2: FIR vs IIR 对比 ---
fig, axes = plt.subplots(3, 1, figsize=(14, 8), sharex=True)

axes[0].plot(t, eeg_raw, color='gray', alpha=0.7, linewidth=0.5)
axes[0].set_title('Raw EEG', fontsize=11)

axes[1].plot(t, eeg_iir_filtfilt, color='#2196F3', linewidth=0.8, label='IIR Butter order=4')
axes[1].set_title('IIR Butterworth + filtfilt', fontsize=11, color='#2196F3')
axes[1].legend(loc='upper right')

axes[2].plot(t, eeg_fir_filtfilt, color='#4CAF50', linewidth=0.8, label=f'FIR order={numtaps-1}')
axes[2].set_title(f'FIR (firwin, {numtaps} taps) + filtfilt', fontsize=11, color='#4CAF50')
axes[2].legend(loc='upper right')
axes[2].set_xlabel('Time (s)')

plt.tight_layout()
plt.savefig(f'{out_dir}_2_fir_vs_iir.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图2已保存: {out_dir}_2_fir_vs_iir.png")

# --- 图3: 频域对比 ---
fig, axes = plt.subplots(3, 1, figsize=(14, 8))

nperseg = 256
for ax, data, title, color in [
    (axes[0], eeg_raw, 'Raw EEG - PSD', 'gray'),
    (axes[1], eeg_iir_filtfilt, 'IIR bandpass 0.5-40Hz - PSD', '#2196F3'),
    (axes[2], eeg_fir_filtfilt, 'FIR bandpass 0.5-40Hz - PSD', '#4CAF50'),
]:
    freqs, psd = sig.welch(data, fs, nperseg=nperseg)
    ax.semilogy(freqs, psd, color=color, linewidth=1)
    ax.set_title(title, fontsize=11)
    ax.set_ylabel('PSD')
    ax.set_xlim(0, 80)
    # 标注关键频率
    for f, label in [(10, 'alpha'), (20, 'beta'), (50, '50Hz')]:
        ax.axvline(f, color='red', linestyle='--', alpha=0.4, linewidth=0.8)
        ax.text(f+1, ax.get_ylim()[1]*0.5, label, fontsize=8, color='red', alpha=0.6)

axes[2].set_xlabel('Frequency (Hz)')
plt.tight_layout()
plt.savefig(f'{out_dir}_3_psd_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图3已保存: {out_dir}_3_psd_comparison.png")

# --- 图4: Notch + Bandpass 完整流程 ---
fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)

axes[0].plot(t, eeg_raw, color='gray', alpha=0.7, linewidth=0.5)
axes[0].set_title('Raw EEG', fontsize=11)

axes[1].plot(t, eeg_bandpass, color='#2196F3', linewidth=0.8)
axes[1].set_title('Step 1: Bandpass 0.5-40Hz (50Hz still leaks)', fontsize=11, color='#2196F3')

axes[2].plot(t, eeg_full_pipeline, color='#4CAF50', linewidth=0.8)
axes[2].set_title('Step 2: + Notch 50Hz (clean signal)', fontsize=11, color='#4CAF50')

# 对比原始 alpha
axes[3].plot(t, alpha, color='orange', linewidth=1, label='True alpha (10Hz)')
axes[3].plot(t, eeg_full_pipeline, color='#4CAF50', linewidth=0.8, alpha=0.7, label='Filtered signal')
axes[3].set_title('Filtered vs True Alpha Component', fontsize=11)
axes[3].legend(loc='upper right')
axes[3].set_xlabel('Time (s)')

plt.tight_layout()
plt.savefig(f'{out_dir}_4_full_pipeline.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图4已保存: {out_dir}_4_full_pipeline.png")

# --- 图5: 滤波器频率响应对比 ---
fig, axes = plt.subplots(2, 1, figsize=(14, 8))

# IIR 频率响应
w_iir, h_iir = sig.freqz(b_iir, a_iir, worN=2048, fs=fs)
axes[0].plot(w_iir, 20 * np.log10(np.abs(h_iir) + 1e-10), color='#2196F3', label='IIR single pass')
# filtfilt = |H|^2
axes[0].plot(w_iir, 20 * np.log10(np.abs(h_iir)**2 + 1e-10), color='#2196F3', linestyle='--', label='IIR filtfilt (|H|²)')
axes[0].axvline(0.5, color='red', linestyle=':', alpha=0.5, label='0.5 Hz')
axes[0].axvline(40, color='red', linestyle=':', alpha=0.5, label='40 Hz')
axes[0].set_title('IIR Butterworth Frequency Response', fontsize=11)
axes[0].set_ylabel('Magnitude (dB)')
axes[0].set_xlim(0, 80)
axes[0].set_ylim(-80, 5)
axes[0].legend(loc='upper right')
axes[0].grid(True, alpha=0.3)

# FIR 频率响应
w_fir, h_fir = sig.freqz(b_fir, [1.0], worN=2048, fs=fs)
axes[1].plot(w_fir, 20 * np.log10(np.abs(h_fir) + 1e-10), color='#4CAF50', label='FIR single pass')
axes[1].plot(w_fir, 20 * np.log10(np.abs(h_fir)**2 + 1e-10), color='#4CAF50', linestyle='--', label='FIR filtfilt (|H|²)')
axes[1].axvline(0.5, color='red', linestyle=':', alpha=0.5)
axes[1].axvline(40, color='red', linestyle=':', alpha=0.5)
axes[1].set_title(f'FIR Frequency Response (order={numtaps-1})', fontsize=11)
axes[1].set_ylabel('Magnitude (dB)')
axes[1].set_xlabel('Frequency (Hz)')
axes[1].set_xlim(0, 80)
axes[1].set_ylim(-80, 5)
axes[1].legend(loc='upper right')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{out_dir}_5_freq_response.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图5已保存: {out_dir}_5_freq_response.png")

# --- 图6: FIR lfilter 的群延迟可视化 ---
fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharex=True)

group_delay = (numtaps - 1) / 2  # 采样点
group_delay_ms = group_delay / fs * 1000

axes[0].plot(t, eeg_fir_lfilter, color='#F44336', linewidth=0.8, label='FIR + lfilter (with delay)')
axes[0].plot(t, eeg_fir_filtfilt, color='#4CAF50', linewidth=0.8, alpha=0.8, label='FIR + filtfilt (zero delay)')
axes[0].set_title(f'FIR: lfilter has group delay = {group_delay} samples = {group_delay_ms:.0f} ms', fontsize=11)
axes[0].legend(loc='upper right')

# 将 lfilter 结果左移群延迟，看是否对齐
eeg_shifted = np.roll(eeg_fir_lfilter, -int(group_delay))
axes[1].plot(t, eeg_shifted, color='#F44336', linewidth=0.8, alpha=0.7, label='lfilter (manually shifted)')
axes[1].plot(t, eeg_fir_filtfilt, color='#4CAF50', linewidth=0.8, alpha=0.8, label='filtfilt (inherently zero-phase)')
axes[1].set_title('After manually compensating group delay, they align!', fontsize=11)
axes[1].legend(loc='upper right')
axes[1].set_xlabel('Time (s)')

plt.tight_layout()
plt.savefig(f'{out_dir}_6_group_delay.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图6已保存: {out_dir}_6_group_delay.png")

print("\n✅ 所有图表生成完毕!")
