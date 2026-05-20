"""
Week 4 Day 9：时频分析 + ERD/ERS
简化和弦月环境兼容版（单线程 + 轻量数据）
"""

import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MNE_NUMPY_THREADS'] = '1'
os.environ['MNE_IGNORE_CACHE'] = '1'

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import signal

import mne
from mne.time_frequency import tfr_morlet

# ─────────────────────────────────────────
# 0. 加载数据
# ─────────────────────────────────────────
print(">>> 加载 EEG 数据 …")

try:
    from mne.datasets import sample
    data_path = sample.data_path(download=False)
    fpath = os.path.join(data_path, 'MEG', 'sample', 'sample_audvis_raw.fif')
    raw = mne.io.read_raw_fif(fpath, preload=True, verbose=False)
    raw.pick_types(meg=False, eeg=True, eog=True, stim=True, verbose=False)
    print(f"  ✓ Sample MEG 数据: {len(raw.ch_names)} 通道, sfreq={raw.info['sfreq']}")
except Exception as e:
    print(f"  ⚠ Sample 失败: {e}")
    raise

raw.resample(200, n_jobs=1)        # 降采样到 200 Hz
raw.notch_filter(50, n_jobs=1)    # 去除工频
raw.set_eeg_reference('average', projection=False, verbose=False)

# ─────────────────────────────────────────
# 1. 创建事件 + Epochs
# ─────────────────────────────────────────
events = mne.find_events(raw, stim_channel='STI 014', min_duration=0.005, verbose=False)
event_id = {'event/1': 1, 'event/2': 2}
print(f"  ✓ 事件数: {len(events)}")

epochs = mne.Epochs(
    raw, events, event_id,
    tmin=-1.0, tmax=2.0,
    baseline=(None, 0),
    preload=True, verbose=False,
    reject=dict(eeg=150e-6)
)
print(f"  ✓ Epochs: {len(epochs)} 个, shape {epochs.get_data().shape}")

# ─────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────
def savefig(fig, idx):
    path = f'/tmp/day9_plot_{idx}.png'
    fig.savefig(path, dpi=120, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ 保存图 {idx}: {path}")
    return path

# ─────────────────────────────────────────
# 图 1：STFT 频谱图
# ─────────────────────────────────────────
print("\n>>> 图 1：STFT 频谱图")
epochs_pick = epochs.pick_types(eeg=True)  # legacy but works
picked_ch = 'C3' if 'C3' in epochs_pick.ch_names else epochs_pick.ch_names[0]
# Get all EEG epochs data, then manually slice for the single channel
epochs_pick_data = epochs_pick.get_data()  # (n_ep, n_ch, n_times)
ch_idx = list(epochs_pick.ch_names).index(picked_ch)
data = epochs_pick_data[0, ch_idx, :]  # first epoch, picked channel, all times

fs = 200
nperseg = 128
noverlap = 96

f, t, Zxx = signal.stft(data, fs=fs, nperseg=nperseg, noverlap=noverlap)
power = np.abs(Zxx) ** 2

fig1, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
times_raw = np.linspace(-1, 2, len(data))  # original times

ax = axes[0]
ax.plot(times_raw, data * 1e6, color='steelblue', linewidth=0.8)
ax.set_ylabel('EEG [μV]')
ax.set_title(f'原始 EEG 时域信号 ({picked_ch})', fontsize=11)
ax.axvline(0, color='red', linestyle='--', label='Event onset')
ax.legend(fontsize=9)

ax = axes[1]
pc = ax.pcolormesh(t - 1, f, 10 * np.log10(power + 1e-12),
                   shading='gouraud', cmap='magma')
ax.set_ylabel('Frequency [Hz]')
ax.set_xlabel('Time [s] (relative to event)')
ax.set_title(f'STFT Spectrogram (nperseg={nperseg}, Δf={fs/nperseg:.1f}Hz)', fontsize=11)
ax.axvline(0, color='white', linestyle='--', linewidth=1)
cb = fig1.colorbar(pc, ax=ax, shrink=0.8)
cb.set_label('Power [dB]')

fig1.suptitle('图 1：STFT 频谱图 — 单通道示范', fontsize=14, fontweight='bold')
savefig(fig1, 1)

# ─────────────────────────────────────────
# 图 2：不同窗口大小对比
# ─────────────────────────────────────────
print(">>> 图 2：STFT 窗口大小对比")
fig2, axes = plt.subplots(3, 1, figsize=(13, 10), sharex=True)
windows = [32, 128, 512]
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

for ax, nperseg_w, color in zip(axes, windows, colors):
    f_w, t_w, Zxx_w = signal.stft(data, fs=fs, nperseg=nperseg_w, noverlap=nperseg_w * 3 // 4)
    pwr = np.abs(Zxx_w) ** 2
    pc = ax.pcolormesh(t_w - 1, f_w, 10 * np.log10(pwr + 1e-12),
                       shading='gouraud', cmap='viridis')
    ax.set_ylabel('Frequency [Hz]')
    ax.set_title(f'STFT — nperseg={nperseg_w}  (Δf={fs/nperseg_w:.1f}Hz, 窗口={nperseg_w/fs:.2f}s)',
                 fontsize=10)
    ax.axvline(0, color='red', linestyle='--', linewidth=1)
    cb = fig2.colorbar(pc, ax=ax, shrink=0.8)
    cb.set_label('dB')

axes[-1].set_xlabel('Time [s] (relative to event)')
fig2.suptitle('图 2：STFT 窗口大小与频率分辨率权衡', fontsize=14, fontweight='bold')
savefig(fig2, 2)

# ─────────────────────────────────────────
# 图 3：Morlet 小波 TFR（使用 Epochs 平均）
# ─────────────────────────────────────────
print("\n>>> 图 3：计算 Morlet 小波 TFR …")
freqs = np.logspace(*np.log10([4, 40]), num=30)
n_cycles = freqs / 3

power, itc = tfr_morlet(
    epochs, freqs=freqs, n_cycles=n_cycles,
    return_itc=True, decim=3, n_jobs=1,
    verbose=False
)
# tfr_morlet returns (AverageTFR, AverageTFR) for epochs input
power_avg = power  # Already averaged
itc_avg = itc
print(f"  ✓ TFR shape: {power_avg.data.shape}")  # (n_chs, n_freqs, n_times)

ch = 'C3' if 'C3' in power_avg.ch_names else power_avg.ch_names[0]

fig3, ax = plt.subplots(figsize=(12, 6))
power_avg.plot(
    [ch], baseline=(None, 0), mode='percent',
    axes=ax, colorbar=True, show=False,
    title=f'ERD/ERS at {ch}'
)
ax.set_title(f'图 3：ERD/ERS 时频图 — {ch} 通道 (Baseline: pre-event %)', fontsize=12)
savefig(fig3, 3)

# ─────────────────────────────────────────
# 图 4：各频段 ERD/ERS 曲线
# ─────────────────────────────────────────
print(">>> 图 4：各频段 ERD/ERS 曲线")

from scipy.signal import butter, sosfiltfilt

def bandpass_power(data, low, high, fs, order=4):
    """带通滤波 + Hilbert 包络"""
    sos = butter(order, [low/(fs/2), high/(fs/2)], btype='band', output='sos')
    bp = sosfiltfilt(sos, data, axis=-1)
    return bp ** 2

epochs_data = epochs.get_data()  # (n_ep, n_ch, n_times)
times = epochs.times
sfreq = epochs.info['sfreq']

band_defs = [
    ('Theta (4-7 Hz)', 4, 7, '#4CAF50'),
    ('Alpha (8-12 Hz)', 8, 12, '#FF9800'),
    ('Beta (13-30 Hz)', 13, 30, '#E91E63'),
    ('Gamma (30-40 Hz)', 30, 40, '#9C27B0'),
]

fig4, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True)

for ax, (name, fmin, fmax, color) in zip(axes.flat, band_defs):
    # 计算所有 epoch 的带通功率
    all_powers = np.array([bandpass_power(ep, fmin, fmax, sfreq) for ep in epochs_data])
    # 基线（前 200ms）
    t_baseline = times < 0
    b_mean = all_powers[:, :, t_baseline].mean(axis=(1, 2), keepdims=True)
    b_mean = np.clip(b_mean, 1e-12, None)
    # ERD/ERS %
    erd = ((all_powers - b_mean) / b_mean) * 100  # (n_ep, n_ch, n_times)
    # 平均所有通道和 epoch
    mean_curve = erd.mean(axis=(0, 1))  # (n_times,)
    se = erd.std(axis=(0, 1)) / np.sqrt(erd.shape[0])

    ax.plot(times, mean_curve, color=color, linewidth=2)
    ax.fill_between(times, mean_curve - se, mean_curve + se, color=color, alpha=0.2)
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    ax.axvline(0, color='red', linestyle='--', linewidth=1)
    ax.set_ylabel('ERD/ERS [%]')
    ax.set_title(f'{name}', fontsize=11, color=color)
    ax.set_ylim(-80, 100)
    ax.grid(True, alpha=0.3)

    peak_erd = mean_curve.min()
    peak_ers = mean_curve.max()
    t_erd = times[np.argmin(mean_curve)]
    t_ers = times[np.argmax(mean_curve)]
    ax.annotate(f'ERD: {peak_erd:.1f}%', xy=(t_erd, peak_erd),
                xytext=(t_erd + 0.2, peak_erd + 15), fontsize=8, color='darkred')
    ax.annotate(f'ERS: {peak_ers:.1f}%', xy=(t_ers, peak_ers),
                xytext=(t_ers + 0.2, peak_ers - 15), fontsize=8, color='darkgreen')

axes[-1, 0].set_xlabel('Time [s] (relative to event)')
axes[-1, 1].set_xlabel('Time [s] (relative to event)')
fig4.suptitle('图 4：各频段 ERD/ERS 曲线（多 epoch 平均 ± SE）', fontsize=14, fontweight='bold')
savefig(fig4, 4)

# ─────────────────────────────────────────
# 图 5：Alpha ERD 拓扑图（单时间窗口）
# ─────────────────────────────────────────
print(">>> 图 5：Alpha ERD 拓扑图")
fig5 = power_avg.plot_topomap(
    tmin=0.1, tmax=0.6, fmin=8, fmax=12,
    baseline=(None, 0), mode='percent',
    show=False, vlim=(-150, 150)
)
fig5.suptitle('Fig5: Alpha (8-12 Hz) ERD topography 0.1-0.6s post-event', fontsize=13, fontweight='bold', y=1.02)
path5 = '/tmp/day9_plot_5.png'
fig5.savefig(path5, dpi=120, bbox_inches='tight')
plt.close(fig5)
print(f"  ✓ 保存图 5: {path5}")

# ─────────────────────────────────────────
# 图 6：多时间点拓扑图 — Beta 频段
# ─────────────────────────────────────────
print(">>> 图 6：Beta 频段拓扑时间序列")
times_to_plot = [-0.4, -0.1, 0.1, 0.3, 0.6, 1.2]

fig6, axes = plt.subplots(2, 3, figsize=(15, 8))
fig6.suptitle('图 6：Beta (13-30 Hz) 频段能量拓扑随时间演变', fontsize=14, fontweight='bold')

for ax, t_val in zip(axes.flat, times_to_plot):
    try:
        power_avg.plot_topomap(
            t=t_val, fmin=13, fmax=30,
            baseline=(None, 0), mode='percent',
            axes=ax, show=False, colorbar=False,
            vlim=(-100, 100)
        )
    except Exception:
        label = f't={t_val}s NA'
        ax.text(0.5, 0.5, label, ha='center', va='center',
                transform=ax.transAxes)
        ax.set_title(f't={t_val:.2f}s')

fig6.subplots_adjust(right=0.88, hspace=0.4, wspace=0.3)
cbar_ax = fig6.add_axes([0.9, 0.15, 0.02, 0.7])
sm = plt.cm.ScalarMappable(cmap='RdBu_r', norm=plt.Normalize(-100, 100))
sm.set_array([])
fig6.colorbar(sm, cax=cbar_ax, label='ERD/ERS [%]')
savefig(fig6, 6)

# ─────────────────────────────────────────
# 图 7：时频 GFP
# ─────────────────────────────────────────
print(">>> 图 7：时频 GFP")
P = power_avg.data  # (n_chs, n_freqs, n_times)
mean_P = P.mean(axis=0, keepdims=True)
gfp_tf = np.sqrt(((P - mean_P) ** 2).mean(axis=0))  # (n_freqs, n_times)
freqs_TFR = power_avg.freqs
times_TFR = power_avg.times

fig7, ax = plt.subplots(figsize=(12, 6))
pc = ax.pcolormesh(times_TFR, freqs_TFR, gfp_tf,
                   shading='gouraud', cmap='plasma')
ax.set_ylabel('Frequency [Hz]')
ax.set_xlabel('Time [s] (relative to event)')
ax.set_title('图 7：时频 GFP — 全脑同步活动强度', fontsize=13)
ax.axvline(0, color='white', linestyle='--', linewidth=1)
cb = fig7.colorbar(pc, ax=ax, shrink=0.8)
cb.set_label('GFP [μV²]')
fig7.suptitle('图 7：时频 GFP — 通道间功率标准差', fontsize=14, fontweight='bold')
savefig(fig7, 7)

# ─────────────────────────────────────────
# 图 8：ITC（Inter-Trial Coherence）
# ─────────────────────────────────────────
print(">>> 图 8：ITC")
fig8, ax = plt.subplots(figsize=(12, 5))
itc_avg.plot([ch], baseline=(None, 0), mode='mean', axes=ax,
             colorbar=True, show=False)
ax.set_title(f'图 8：ITC (相位锁定了成分) — {ch}', fontsize=13)
ax.set_ylabel('ITC (0=无锁相, 1=完美锁相)')
savefig(fig8, 8)

# ─────────────────────────────────────────
# 汇总
# ─────────────────────────────────────────
print("\n" + "="*50)
print("汇总")
print("="*50)
print(f"  Epochs: {len(epochs)} 个, shape {epochs.get_data().shape}")
print(f"  TFR: {len(freqs)} 频段, times {times_TFR[0]:.2f}~{times_TFR[-1]:.2f}s")
print(f"  ERD/ERS 频段: Theta/Alpha/Beta/Gamma")
print(f"  GFP shape: {gfp_tf.shape}")
print("  图 1-8 已保存到 /tmp/day9_plot_*.png")
print("="*50)
