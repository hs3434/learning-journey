"""
Week 4 Day 3 练习：事件标记 + Epoch 切分 + Trigger 对齐
用 MNE 示例数据演示：事件检测 → Epoch 切分 → 基线校正 → Evoked 平均
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

out_dir = '/workspace/learning-journey/tracks/brain-computer-interface/projects/signal-processor/exercises/day8_plot'

# ============================================================
# 1. 下载并加载 MNE 示例数据
# ============================================================
import mne
mne.set_log_level('WARNING')

sample_data_folder = mne.datasets.sample.data_path()
sample_data_raw_file = (sample_data_folder / 'MEG' / 'sample' /
                        'sample_audvis_raw.fif')

raw = mne.io.read_raw_fif(sample_data_raw_file, preload=True, verbose=False)
raw_eeg = raw.copy().pick('eeg')

print(f"Raw 数据: {len(raw_eeg.ch_names)} EEG 通道, "
      f"{raw_eeg.info['sfreq']} Hz, {raw_eeg.times[-1]:.1f} 秒")

# ============================================================
# 2. 简单预处理（高通 + notch）— 不做完整 ICA，只演示事件/epoch
# ============================================================
raw_eeg.filter(l_freq=1.0, h_freq=40, verbose=False)
raw_eeg.notch_filter(freqs=50, verbose=False)
raw_eeg.set_eeg_reference('average', verbose=False)
print("预处理完成: 1-40Hz 带通 + 50Hz Notch + 平均参考")

# ============================================================
# 3. 事件检测（Event Detection）
# ============================================================
events = mne.find_events(raw, stim_channel='STI 014', verbose=False)

event_id = {
    'auditory/left':  1,
    'auditory/right': 2,
    'visual/left':     3,
    'visual/right':    4,
    'smiley':          5,
    'button':         32,
}

print(f"\n事件检测结果: 共 {len(events)} 个事件")
for name, code in event_id.items():
    count = np.sum(events[:, 2] == code)
    if count > 0:
        print(f"  {name} (code={code}): {count} 次")

# --- 图1: 事件光栅图（Event Raster）---
fig, ax = plt.subplots(1, 1, figsize=(16, 4))
ax.eventplot(
    [events[events[:, 2] == code, 0] / raw.info['sfreq']
     for code in [1, 2, 3, 4]],
    lineoffsets=[1, 2, 3, 4],
    linelengths=0.8,
    colors=['#2196F3', '#4CAF50', '#FF9800', '#9C27B0']
)
ax.set_yticks([1, 2, 3, 4])
ax.set_yticklabels(['Aud/L', 'Aud/R', 'Vis/L', 'Vis/R'])
ax.set_xlabel('Time (s)')
ax.set_title('Event Raster — All Trial Events', fontsize=12)
ax.set_xlim(0, 60)  # 只显示前60秒
plt.tight_layout()
plt.savefig(f'{out_dir}_1_event_raster.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图1已保存: {out_dir}_1_event_raster.png")

# --- 图2: 事件间期（ISI）分布 + 事件数量统计 ---
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# ISI 分布
event_times = events[:, 0] / raw.info['sfreq']
isis = np.diff(event_times)
axes[0].hist(isis, bins=50, color='#607D8B', edgecolor='white', alpha=0.8)
axes[0].set_xlabel('Inter-Stimulus Interval (s)')
axes[0].set_ylabel('Count')
axes[0].set_title('ISI Distribution — Event Timing', fontsize=11)
axes[0].axvline(np.median(isis), color='red', linestyle='--',
                label=f'Median={np.median(isis):.2f}s')
axes[0].legend()

# 各条件事件数量
codes = [1, 2, 3, 4]
names = ['Aud/L', 'Aud/R', 'Vis/L', 'Vis/R']
counts = [np.sum(events[:, 2] == c) for c in codes]
colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0']
axes[1].bar(names, counts, color=colors, width=0.6)
axes[1].set_ylabel('Count')
axes[1].set_title('Event Counts by Condition', fontsize=11)
for i, (name, count) in enumerate(zip(names, counts)):
    axes[1].text(i, count + 1, str(count), ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig(f'{out_dir}_2_event_stats.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图2已保存: {out_dir}_2_event_stats.png")

# ============================================================
# 4. Epoch 切分 + 基线校正
# ============================================================
epochs = mne.Epochs(
    raw_eeg, events, event_id,
    tmin=-0.2, tmax=0.8,         # 事件前200ms，事件后800ms
    baseline=(None, 0),          # 事件前所有时间做基线校正
    preload=True, verbose=False
)

# 自动拒绝坏 epoch
epochs.drop_bad(reject={'eeg': 150e-6}, verbose=False)

print(f"\nEpochs 信息:")
print(f"  有效 epochs: {len(epochs)} (拒绝 {(len(events)-len(epochs))} 个)")
print(f"  时间窗口: {epochs.tmin}s ~ {epochs.tmax}s")
print(f"  数据 shape: {epochs.get_data().shape} (n_epochs, n_channels, n_times)")

# --- 图3: Epoch 叠加 vs 平均（单通道）---
ch_name = 'EEG 021'  # ~C3
ch_idx = epochs.info['ch_names'].index(ch_name)
times = epochs.times

aud_left_data = epochs['auditory/left'].get_data()
evoked_al = epochs['auditory/left'].average()

fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

# 上图：多个单次 epoch 叠加（半透明）
n_show = 20
for i in range(min(n_show, aud_left_data.shape[0])):
    axes[0].plot(times, aud_left_data[i, ch_idx] * 1e6,
                 color='#2196F3', alpha=0.3, linewidth=0.5)

# 平均线（粗红线）
axes[0].plot(times, evoked_al.data[ch_idx] * 1e6,
             color='red', linewidth=2.5, label='Evoked (average)')
axes[0].axvline(0, color='black', linestyle='--', linewidth=1.5, label='Event onset')
axes[0].axhline(0, color='gray', linestyle='-', linewidth=0.5)
axes[0].set_ylabel('Amplitude (μV)')
axes[0].set_title(f'Single Trials (n={aud_left_data.shape[0]}) vs Evoked — {ch_name} (~C3)\nAuditory Left', fontsize=11)
axes[0].legend()

# 下图：视觉 vs 听觉 Evoked
evoked_ar = epochs['auditory/right'].average()
evoked_vl = epochs['visual/left'].average()
evoked_vr = epochs['visual/right'].average()

axes[1].plot(times, evoked_al.data[ch_idx] * 1e6,
             color='#2196F3', linewidth=1.5, label='Aud/L')
axes[1].plot(times, evoked_ar.data[ch_idx] * 1e6,
             color='#4CAF50', linewidth=1.5, label='Aud/R')
axes[1].plot(times, evoked_vl.data[ch_idx] * 1e6,
             color='#FF9800', linewidth=1.5, label='Vis/L')
axes[1].plot(times, evoked_vr.data[ch_idx] * 1e6,
             color='#9C27B0', linewidth=1.5, label='Vis/R')
axes[1].axvline(0, color='black', linestyle='--', linewidth=1.5, label='Event onset')
axes[1].axhline(0, color='gray', linestyle='-', linewidth=0.5)
axes[1].set_xlabel('Time (s)')
axes[1].set_ylabel('Amplitude (μV)')
axes[1].set_title('Evoked Comparison — Auditory vs Visual', fontsize=11)
axes[1].legend()

plt.tight_layout()
plt.savefig(f'{out_dir}_3_epochs_vs_evoked.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图3已保存: {out_dir}_3_epochs_vs_evoked.png")

# ============================================================
# 5. 基线校正效果对比
# ============================================================
epochs_no_base = mne.Epochs(
    raw_eeg, events, event_id,
    tmin=-0.2, tmax=0.8,
    baseline=None,             # 不做基线校正
    preload=True, verbose=False
)
epochs_no_base.drop_bad(reject={'eeg': 150e-6}, verbose=False)

evoked_with_base = epochs['auditory/left'].average()
evoked_no_base = epochs_no_base['auditory/left'].average()

fig, axes = plt.subplots(2, 1, figsize=(14, 7), sharex=True)
axes[0].plot(times, evoked_no_base.data[ch_idx] * 1e6,
             color='#9E9E9E', linewidth=1.5, label='Without baseline correction')
axes[0].plot(times, evoked_with_base.data[ch_idx] * 1e6,
             color='#2196F3', linewidth=1.5, label='With baseline correction (baseline=None, 0)')
axes[0].axvline(0, color='black', linestyle='--', linewidth=1.5)
axes[0].axhline(0, color='gray', linestyle='-', linewidth=0.5)
axes[0].set_ylabel('Amplitude (μV)')
axes[0].set_title('Effect of Baseline Correction — Auditory Left ERP at C3', fontsize=11)
axes[0].legend()

# 差值（基线校正的影响）
diff = (evoked_no_base.data - evoked_with_base.data)[ch_idx] * 1e6
axes[1].plot(times, diff, color='#FF5722', linewidth=1.5)
axes[1].axvline(0, color='black', linestyle='--', linewidth=1.5)
axes[1].axhline(0, color='gray', linestyle='-', linewidth=0.5)
axes[1].fill_between(times, diff, 0, where=(diff != 0), alpha=0.3, color='#FF5722')
axes[1].set_xlabel('Time (s)')
axes[1].set_ylabel('Difference (μV)')
axes[1].set_title('What Baseline Correction Removed (DC offset & slow drift)', fontsize=11)

plt.tight_layout()
plt.savefig(f'{out_dir}_4_baseline_correction.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图4已保存: {out_dir}_4_baseline_correction.png")

# ============================================================
# 6. Trigger 对齐效果（不同 onset 对齐方式）
# ============================================================
# 演示：同一个事件，不同 tmin/tmax 切分效果
epochs_short = mne.Epochs(
    raw_eeg, events, event_id,
    tmin=-0.05, tmax=0.2,       # 短窗口（早成分）
    baseline=(None, 0),
    preload=True, verbose=False
)
epochs_short.drop_bad(reject={'eeg': 150e-6}, verbose=False)

epochs_long = mne.Epochs(
    raw_eeg, events, event_id,
    tmin=-0.5, tmax=1.5,        # 长窗口（晚成分）
    baseline=(None, 0),
    preload=True, verbose=False
)
epochs_long.drop_bad(reject={'eeg': 150e-6}, verbose=False)

evoked_short = epochs_short['auditory/left'].average()
evoked_long = epochs_long['auditory/left'].average()

fig, axes = plt.subplots(2, 1, figsize=(14, 7), sharex=True)

# 短窗口（看清 N100/P200）
axes[0].plot(epochs_short.times, evoked_short.data[ch_idx] * 1e6,
             color='#2196F3', linewidth=2)
axes[0].axvline(0, color='red', linestyle='--', linewidth=1.5)
axes[0].axhline(0, color='gray', linewidth=0.5)
axes[0].set_ylabel('Amplitude (μV)')
axes[0].set_title(f'Short Window (-50ms ~ 200ms) — N100/P200 visible at C3', fontsize=11)
axes[0].annotate('N100', xy=(0.09, -3), fontsize=10, color='red')
axes[0].annotate('P200', xy=(0.18, 3), fontsize=10, color='red')

# 长窗口（看清 N400/LLP）
axes[1].plot(epochs_long.times, evoked_long.data[ch_idx] * 1e6,
             color='#4CAF50', linewidth=2)
axes[1].axvline(0, color='red', linestyle='--', linewidth=1.5)
axes[1].axhline(0, color='gray', linewidth=0.5)
axes[1].set_xlabel('Time (s)')
axes[1].set_ylabel('Amplitude (μV)')
axes[1].set_title(f'Long Window (-500ms ~ 1500ms) — Late components visible', fontsize=11)

plt.tight_layout()
plt.savefig(f'{out_dir}_5_window_length.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图5已保存: {out_dir}_5_window_length.png")

# ============================================================
# 7. GFP（Global Field Power）— 所有通道总体波动
# ============================================================
gfp_al = evoked_al.data.std(axis=0) * 1e6   # across channels
gfp_vl = evoked_vl.data.std(axis=0) * 1e6

fig, axes = plt.subplots(2, 1, figsize=(14, 7), sharex=True)

axes[0].plot(times, gfp_al, color='#2196F3', linewidth=1.5, label='Aud/L')
axes[0].plot(times, gfp_vl, color='#FF9800', linewidth=1.5, label='Vis/L')
axes[0].axvline(0, color='red', linestyle='--', linewidth=1.5)
axes[0].set_ylabel('GFP (μV)')
axes[0].set_title('Global Field Power — Spatial Standard Deviation across Channels', fontsize=11)
axes[0].legend()

# 差值 GFP
gfp_diff = gfp_al - gfp_vl
axes[1].plot(times, gfp_diff, color='#9C27B0', linewidth=1.5)
axes[1].axvline(0, color='red', linestyle='--', linewidth=1.5)
axes[1].axhline(0, color='gray', linewidth=0.5)
axes[1].fill_between(times, gfp_diff, 0, alpha=0.3, color='#9C27B0')
axes[1].set_xlabel('Time (s)')
axes[1].set_ylabel('GFP difference (μV)')
axes[1].set_title('GFP Difference (Aud/L − Vis/L)', fontsize=11)

plt.tight_layout()
plt.savefig(f'{out_dir}_6_gfp.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图6已保存: {out_dir}_6_gfp.png")

# ============================================================
# 8. 拓扑图时间演变（不同 latency）
# ============================================================
fig, axes = plt.subplots(2, 4, figsize=(16, 7))

latencies = [0.05, 0.1, 0.2, 0.4]  # 事件后 50/100/200/400ms
for row, (evoked, label) in enumerate([(evoked_al, 'Aud/L'), (evoked_vl, 'Vis/L')]):
    for col, lat in enumerate(latencies):
        t_idx = np.argmin(np.abs(evoked.times - lat))
        data_at_t = evoked.data[:, t_idx] * 1e6

        ax = axes[row, col]
        mne.viz.plot_topomap(data_at_t, evoked.info, axes=ax, show=False,
                             sensors=False, contours=0)
        ax.set_title(f'{label} @{int(lat*1000)}ms', fontsize=10)

plt.suptitle('ERP Topography at Different Latencies', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{out_dir}_7_erp_topo.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图7已保存: {out_dir}_7_erp_topo.png")

# ============================================================
# 9. drop_bad 拒绝情况可视化
# ============================================================
reject_log = epochs.drop_log
n_rejected = sum(1 for d in reject_log if len(d) > 0)
n_total = len(epochs)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 各条件剩余 epoch 数量
conditions = ['auditory/left', 'auditory/right', 'visual/left', 'visual/right']
cond_counts = [len(epochs[c]) for c in conditions]
colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0']

axes[0].bar(conditions, cond_counts, color=colors, width=0.6)
axes[0].set_ylabel('Remaining epochs')
axes[0].set_title(f'Epochs After Rejection ({n_total} total → {n_total-n_rejected} kept)', fontsize=11)
axes[0].tick_params(axis='x', rotation=15)
for i, count in enumerate(cond_counts):
    axes[0].text(i, count + 1, str(count), ha='center', fontweight='bold')

# 原始 vs 拒绝分布（模拟）
orig_counts = [np.sum(events[:, 2] == {c: i+1 for i, c in enumerate(['auditory/left',
                                                                       'auditory/right',
                                                                       'visual/left',
                                                                       'visual/right'])}[c])
               for c in conditions]

x = np.arange(len(conditions))
width = 0.35
axes[1].bar(x - width/2, orig_counts, width, label='Original', color='#607D8B', alpha=0.7)
axes[1].bar(x + width/2, cond_counts, width, label='After reject', color='#4CAF50', alpha=0.7)
axes[1].set_xticks(x)
axes[1].set_xticklabels(conditions, rotation=15)
axes[1].set_ylabel('Epoch count')
axes[1].set_title('Original vs Kept Epochs', fontsize=11)
axes[1].legend()

plt.tight_layout()
plt.savefig(f'{out_dir}_8_reject_stats.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图8已保存: {out_dir}_8_reject_stats.png")

print("\n✅ Day 8 所有图表生成完毕!")
print("\n事件 & Epoch 流程总结:")
print("  ① mne.find_events() → 从 stim channel 提取事件")
print("  ② mne.Epochs() → 以事件 onset 为中心切分 epoch")
print("  ③ baseline=(None, 0) → 减去事件前均值（基线校正）")
print("  ④ drop_bad(reject) → 自动拒绝幅值异常 epoch")
print("  ⑤ epochs[condition].average() → Evoked 平均（ERP）")
