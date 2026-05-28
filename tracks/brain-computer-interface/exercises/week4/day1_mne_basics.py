"""
Week 4 Day 1 练习：MNE-Python 基础
用 MNE 示例数据演示 Raw → Epochs → Evoked 流程
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

out_dir = '/tmp/day6_plots'

# ============================================================
# 1. 下载并加载 MNE 示例数据
# ============================================================
import mne
mne.set_log_level('WARNING')

# 下载示例数据（约 30MB，首次运行需联网）
sample_data_folder = mne.datasets.sample.data_path()
sample_data_raw_file = (sample_data_folder / 'MEG' / 'sample' /
                        'sample_audvis_raw.fif')

raw = mne.io.read_raw_fif(sample_data_raw_file, preload=True, verbose=False)

# 只保留 EEG 通道（去掉 MEG 方便演示）
raw_eeg = raw.copy().pick('eeg')

print(f"Raw 数据信息:")
print(f"  通道数: {len(raw_eeg.ch_names)}")
print(f"  采样率: {raw_eeg.info['sfreq']} Hz")
print(f"  时长: {raw_eeg.times[-1]:.1f} 秒")
print(f"  采样点: {raw_eeg.n_times}")
print(f"  前5个通道: {raw_eeg.ch_names[:5]}")

# ============================================================
# 2. Raw 预处理：滤波
# ============================================================
raw_eeg.filter(l_freq=0.5, h_freq=40, verbose=False)
raw_eeg.notch_filter(freqs=50, verbose=False)
print(f"\n滤波完成: 0.5-40Hz 带通 + 50Hz Notch")

# ============================================================
# 3. 找事件
# ============================================================
events = mne.find_events(raw, stim_channel='STI 014', verbose=False)
event_id = {
    'auditory/left': 1,
    'auditory/right': 2,
    'visual/left': 3,
    'visual/right': 4,
    'smiley': 5,
    'button': 32
}

print(f"\n事件信息:")
print(f"  总事件数: {len(events)}")
for name, code in event_id.items():
    count = np.sum(events[:, 2] == code)
    print(f"  {name}: {count} 次")

# ============================================================
# 4. 创建 Epochs
# ============================================================
epochs = mne.Epochs(
    raw_eeg, events, event_id,
    tmin=-0.2, tmax=0.8,
    baseline=(-0.2, 0),
    preload=True, verbose=False
)

# 自动拒绝异常幅度
epochs.drop_bad(reject={'eeg': 150e-6}, verbose=False)

print(f"\nEpochs 信息:")
print(f"  总 epoch 数: {len(epochs)}")
print(f"  时间窗口: {epochs.tmin}s ~ {epochs.tmax}s")
print(f"  数据 shape: {epochs.get_data().shape}")
print(f"  (n_epochs, n_channels, n_times)")

# ============================================================
# 5. 创建 Evoked（平均）
# ============================================================
evoked_aud_left = epochs['auditory/left'].average()
evoked_vis_left = epochs['visual/left'].average()

print(f"\nEvoked 信息:")
print(f"  听觉左: {len(epochs['auditory/left'])} epochs 平均")
print(f"  视觉左: {len(epochs['visual/left'])} epochs 平均")
print(f"  数据 shape: {evoked_aud_left.data.shape} (n_channels, n_times)")

# ============================================================
# 绘图
# ============================================================

# --- 图1: Raw 功率谱 ---
fig, ax = plt.subplots(1, 1, figsize=(14, 5))
raw_eeg.compute_psd(fmax=50, verbose=False).plot(axes=ax, show=False)
ax.set_title('Raw EEG Power Spectrum (after 0.5-40Hz bandpass + 50Hz notch)', fontsize=12)
plt.tight_layout()
plt.savefig(f'{out_dir}_1_raw_psd.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"\n图1已保存: {out_dir}_1_raw_psd.png")

# --- 图2: Epochs 时域波形（选取 C3 通道） ---
fig, axes = plt.subplots(3, 1, figsize=(14, 10))

# 单个 epoch
epoch_data = epochs['auditory/left'].get_data()
ch_idx = epochs.info['ch_names'].index('EEG 021')  # 接近 C3
times = epochs.times

# 画 5 个单次 epoch
for i in range(min(5, epoch_data.shape[0])):
    axes[0].plot(times, epoch_data[i, ch_idx] * 1e6, alpha=0.5, linewidth=0.5)
axes[0].axvline(0, color='red', linestyle='--', linewidth=1.5, label='Event onset')
axes[0].set_title('Single Epochs (EEG 021 ~ C3, auditory/left)', fontsize=11)
axes[0].set_ylabel('Amplitude (μV)')
axes[0].legend()

# 所有 epoch 平均
axes[1].plot(times, evoked_aud_left.data[ch_idx] * 1e6, color='#2196F3', linewidth=1.5)
axes[1].axvline(0, color='red', linestyle='--', linewidth=1.5)
axes[1].axhline(0, color='gray', linestyle='-', linewidth=0.5)
axes[1].set_title('Evoked (Averaged) — Auditory Left', fontsize=11, color='#2196F3')
axes[1].set_ylabel('Amplitude (μV)')

# 听觉 vs 视觉对比
axes[2].plot(times, evoked_aud_left.data[ch_idx] * 1e6, color='#2196F3', linewidth=1.5, label='Auditory')
axes[2].plot(times, evoked_vis_left.data[ch_idx] * 1e6, color='#F44336', linewidth=1.5, label='Visual')
axes[2].axvline(0, color='red', linestyle='--', linewidth=1.5)
axes[2].axhline(0, color='gray', linestyle='-', linewidth=0.5)
axes[2].set_title('Auditory vs Visual Evoked (C3)', fontsize=11)
axes[2].set_ylabel('Amplitude (μV)')
axes[2].set_xlabel('Time (s)')
axes[2].legend()

plt.tight_layout()
plt.savefig(f'{out_dir}_2_epochs_evoked.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图2已保存: {out_dir}_2_epochs_evoked.png")

# --- 图3: Evoked topo 拓扑图（不同时间点） ---
fig = evoked_aud_left.plot_joint(
    title='Auditory Left Evoked — Topo at different latencies',
    show=False
)
fig.savefig(f'{out_dir}_3_evoked_topo.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图3已保存: {out_dir}_3_evoked_topo.png")

# --- 图4: 数据流程图 — Raw → Epochs → Evoked ---
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# Raw: 长时间序列
raw_data_plot = raw_eeg.get_data(picks=['EEG 021'])[0]
raw_times_plot = raw_eeg.times
# 只取前5秒
mask = raw_times_plot <= 5
axes[0].plot(raw_times_plot[mask], raw_data_plot[mask] * 1e6, color='gray', linewidth=0.3)
axes[0].set_title('Raw (continuous)', fontsize=13, fontweight='bold')
axes[0].set_xlabel('Time (s)')
axes[0].set_ylabel('μV')
axes[0].text(0.5, 0.95, f'shape: ({len(raw_eeg.ch_names)}, {raw_eeg.n_times})',
             transform=axes[0].transAxes, ha='center', fontsize=9, color='blue')

# Epochs: 多段短序列
n_show = 10
for i in range(min(n_show, epoch_data.shape[0])):
    offset = i * 5  # 偏移显示
    axes[1].plot(times, epoch_data[i, ch_idx] * 1e6 + offset, 
                 color='#2196F3', linewidth=0.5, alpha=0.6)
axes[1].axvline(0, color='red', linestyle='--', linewidth=1)
axes[1].set_title('Epochs (segmented)', fontsize=13, fontweight='bold', color='#2196F3')
axes[1].set_xlabel('Time (s)')
axes[1].set_ylabel('Epoch # (offset)')
axes[1].text(0.5, 0.95, f'shape: ({epoch_data.shape[0]}, {epoch_data.shape[1]}, {epoch_data.shape[2]})',
             transform=axes[1].transAxes, ha='center', fontsize=9, color='blue')

# Evoked: 平均后
axes[2].plot(times, evoked_aud_left.data[ch_idx] * 1e6, color='#4CAF50', linewidth=2)
axes[2].axvline(0, color='red', linestyle='--', linewidth=1)
axes[2].axhline(0, color='gray', linestyle='-', linewidth=0.5)
axes[2].set_title('Evoked (averaged)', fontsize=13, fontweight='bold', color='#4CAF50')
axes[2].set_xlabel('Time (s)')
axes[2].set_ylabel('μV')
axes[2].text(0.5, 0.95, f'shape: ({evoked_aud_left.data.shape[0]}, {evoked_aud_left.data.shape[1]})',
             transform=axes[2].transAxes, ha='center', fontsize=9, color='blue')

# 添加箭头
for ax in [axes[0], axes[1]]:
    ax.annotate('', xy=(1.15, 0.5), xytext=(1.05, 0.5),
                xycoords='axes fraction',
                arrowprops=dict(arrowstyle='->', color='red', lw=2))

plt.suptitle('MNE Data Flow: Raw → Epochs → Evoked', fontsize=15, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(f'{out_dir}_4_data_flow.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图4已保存: {out_dir}_4_data_flow.png")

print("\n✅ Day 6 所有图表生成完毕!")
