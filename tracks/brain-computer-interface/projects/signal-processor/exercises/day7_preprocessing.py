"""
Week 4 Day 2 练习：EEG 预处理三步曲
坏通道处理 + 重参考 + ICA 伪迹去除
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

out_dir = '/tmp/day7_plots'

import mne
mne.set_log_level('WARNING')

# ============================================================
# 1. 加载 MNE 示例数据
# ============================================================
sample_data_folder = mne.datasets.sample.data_path()
sample_data_raw_file = (sample_data_folder / 'MEG' / 'sample' /
                        'sample_audvis_raw.fif')

raw = mne.io.read_raw_fif(sample_data_raw_file, preload=True, verbose=False)

# 保留 EEG + EOG 通道（EOG 用于 ICA 伪迹检测，ICA 完成后再去掉）
raw_work = raw.copy().pick(['eeg', 'eog'])

eeg_ch_names = [ch for ch in raw_work.ch_names
                if mne.channel_type(raw_work.info, raw_work.ch_names.index(ch)) == 'eeg']
eog_ch_names = [ch for ch in raw_work.ch_names
                if mne.channel_type(raw_work.info, raw_work.ch_names.index(ch)) == 'eog']

print(f"原始数据: {len(eeg_ch_names)} EEG 通道 + {len(eog_ch_names)} EOG 通道, "
      f"{raw_work.info['sfreq']} Hz, {raw_work.times[-1]:.1f} 秒")

# ============================================================
# 2. 坏通道处理
# ============================================================
# --- 2.1 自动检测坏通道（高标准差 + 低标准差） ---
# 坏通道检测只在 EEG 通道上进行（EOG 通道标准差天然不同）
data_eeg = raw_work.get_data(picks='eeg')
ch_std = np.std(data_eeg, axis=1)
mean_std = np.mean(ch_std)
std_of_std = np.std(ch_std)
high_threshold = mean_std + 3 * std_of_std   # 异常噪声
low_threshold = mean_std - 3 * std_of_std     # 平坦信号

bad_by_high = [eeg_ch_names[i] for i, s in enumerate(ch_std)
               if s > high_threshold]
bad_by_low = [eeg_ch_names[i] for i, s in enumerate(ch_std)
              if s < low_threshold]
bad_auto = bad_by_high + bad_by_low

print(f"\n--- 坏通道检测 ---")
print(f"EEG 通道标准差均值: {mean_std * 1e6:.2f} μV")
print(f"高标准差阈值 (>3σ): {high_threshold * 1e6:.2f} μV → 检测到: {bad_by_high if bad_by_high else '无'}")
print(f"低标准差阈值 (<3σ): {low_threshold * 1e6:.2f} μV → 检测到: {bad_by_low if bad_by_low else '无'}")

# 标记坏通道（只标记 EEG 通道）
raw_work.info['bads'] = bad_auto
print(f"标记的坏通道: {raw_work.info['bads']}")

# --- 2.2 画通道标准差分布图（高+低双阈值，仅 EEG） ---
fig, ax = plt.subplots(1, 1, figsize=(14, 5))
colors = []
for i, ch_name in enumerate(eeg_ch_names):
    if ch_name in bad_by_high:
        colors.append('red')       # 高噪声 → 红色
    elif ch_name in bad_by_low:
        colors.append('orange')    # 平坦信号 → 橙色
    else:
        colors.append('#2196F3')   # 正常 → 蓝色
ax.bar(range(len(ch_std)), ch_std * 1e6, color=colors, width=0.8)
ax.axhline(y=high_threshold * 1e6, color='red', linestyle='--', linewidth=1.5,
           label=f'High 3σ = {high_threshold * 1e6:.1f} μV (noise)')
ax.axhline(y=low_threshold * 1e6, color='orange', linestyle='--', linewidth=1.5,
           label=f'Low 3σ = {low_threshold * 1e6:.1f} μV (flat)')
ax.axhline(y=mean_std * 1e6, color='gray', linestyle='-', linewidth=1,
           label=f'Mean = {mean_std * 1e6:.1f} μV')
ax.set_xlabel('Channel Index')
ax.set_ylabel('Std Dev (μV)')
ax.set_title('Bad Channel Detection — High (noise) & Low (flat) Std Dev', fontsize=12)
# 自定义图例
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='red', label=f'High std (>3σ): noise'),
    Patch(facecolor='orange', label=f'Low std (<3σ): flat'),
    Patch(facecolor='#2196F3', label='Normal'),
]
ax.legend(handles=legend_elements)
plt.tight_layout()
plt.savefig(f'{out_dir}_1_bad_channels.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图1已保存: {out_dir}_1_bad_channels.png")

# --- 2.3 插值坏通道 ---
if raw_work.info['bads']:
    raw_work.interpolate_bads(reset_bads=True)
    print(f"插值完成，坏通道已修复")
else:
    print("无坏通道需要插值")

# ============================================================
# 3. 重参考
# ============================================================
# --- 3.1 查看当前参考 ---
print(f"\n--- 重参考 ---")
print(f"当前参考: {raw_work.info.get('custom_ref_applied', 'default')}")

# 记录重参考前的数据（多通道对比）
demo_channels = ['EEG 021', 'EEG 001', 'EEG 056']  # C3, Fp1, Pz 附近
demo_labels = ['~C3 (central)', '~Fp1 (frontal)', '~Pz (parietal)']
data_before_ref = {ch: raw_work.get_data(picks=[ch])[0].copy() for ch in demo_channels}

# --- 3.2 应用平均参考（仅对 EEG 通道，EOG 不参与） ---
raw_work.set_eeg_reference('average', verbose=False)
print("已应用平均参考（仅 EEG 通道）")

data_after_ref = {ch: raw_work.get_data(picks=[ch])[0] for ch in demo_channels}

# --- 3.3 画重参考前后对比（多通道） ---
fig, axes = plt.subplots(len(demo_channels), 2, figsize=(16, 4 * len(demo_channels)),
                         sharex=True, sharey=True)

t = raw_work.times
mask = t <= 3  # 前3秒

for row, (ch, label) in enumerate(zip(demo_channels, demo_labels)):
    # 重参考前
    axes[row, 0].plot(t[mask], data_before_ref[ch][mask] * 1e6,
                       color='#F44336', linewidth=0.5)
    axes[row, 0].axhline(0, color='gray', linewidth=0.5)
    axes[row, 0].set_ylabel('μV')
    axes[row, 0].set_title(f'{ch} ({label}) — Before', fontsize=10)

    # 重参考后
    axes[row, 1].plot(t[mask], data_after_ref[ch][mask] * 1e6,
                       color='#2196F3', linewidth=0.5)
    axes[row, 1].axhline(0, color='gray', linewidth=0.5)
    axes[row, 1].set_title(f'{ch} ({label}) — After avg ref', fontsize=10)

axes[-1, 0].set_xlabel('Time (s)')
axes[-1, 1].set_xlabel('Time (s)')
plt.suptitle('Re-referencing Effect: Before vs Average Reference', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{out_dir}_2_rereference.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图2已保存: {out_dir}_2_rereference.png")

# ============================================================
# 4. ICA 伪迹去除
# ============================================================
# --- 4.1 ICA 前滤波（高通 1Hz 让 ICA 更稳定） ---
raw_work.filter(l_freq=1.0, h_freq=40.0, verbose=False)
raw_work.notch_filter(freqs=50, verbose=False)
print(f"\n--- ICA ---")
print("滤波完成: 1-40Hz 带通 + 50Hz Notch")

# --- 4.2 拟合 ICA ---
from mne.preprocessing import ICA

ica = ICA(
    n_components=20,
    method='fastica',
    random_state=42,
    max_iter=800,
    verbose=False
)
ica.fit(raw_work)
print(f"ICA 拟合完成: {ica.n_components_} 个成分")

# --- 4.3 自动检测 EOG 伪迹成分 ---
# 直接使用数据中的 EOG 通道（不需要额极区 EEG 代理）
if eog_ch_names:
    print(f"使用真实 EOG 通道: {eog_ch_names}")
    eog_indices, eog_scores = ica.find_bads_eog(raw_work, verbose=False)
else:
    # 如果没有 EOG 通道，退回到用额极区 EEG 通道做代理
    eog_proxy = [ch for ch in raw_work.ch_names if 'Fp' in ch or '011' in ch or '012' in ch]
    if not eog_proxy:
        eog_proxy = [raw_work.ch_names[0], raw_work.ch_names[1]]
    print(f"无 EOG 通道，使用额极区代理: {eog_proxy}")
    eog_indices, eog_scores = ica.find_bads_eog(raw_work, ch_name=eog_proxy, verbose=False)
print(f"自动检测到的 EOG 成分: {eog_indices}")

# 设置排除列表
ica.exclude = eog_indices

# --- 4.4 画 ICA 成分拓扑图 ---
fig = ica.plot_components(
    title='ICA Components — Topographic Maps',
    show=False,
    colorbar=True
)
fig.savefig(f'{out_dir}_3_ica_components.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"图3已保存: {out_dir}_3_ica_components.png")

# --- 4.5 画 EOG 成分得分 ---
# 无论是否自动检测到，都画得分图
fig, ax = plt.subplots(1, 1, figsize=(14, 5))
if eog_scores is not None:
    ica_scores = np.atleast_2d(eog_scores)
    # 取多个 EOG 代理通道的最大绝对值
    ica_scores = np.max(np.abs(ica_scores), axis=0)
else:
    ica_scores = np.zeros(ica.n_components_)
component_indices = np.arange(len(ica_scores))
colors = ['#F44336' if i in eog_indices else '#2196F3'
          for i in component_indices]
ax.bar(component_indices, np.abs(ica_scores), color=colors)
ax.axhline(y=0, color='gray', linewidth=0.5)
ax.set_xlabel('ICA Component')
ax.set_ylabel('|EOG Correlation Score|')
title = 'EOG Artifact Detection — Component Scores'
if eog_indices:
    title += f' (Detected: {eog_indices})'
else:
    title += ' (No EOG detected automatically — low correlation with frontal channels)'
ax.set_title(title, fontsize=11)
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#F44336', label='Detected EOG'),
                   Patch(facecolor='#2196F3', label='Neural')]
ax.legend(handles=legend_elements)
plt.tight_layout()
plt.savefig(f'{out_dir}_4_ica_eog_scores.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图4已保存: {out_dir}_4_ica_eog_scores.png")

# --- 4.6 应用 ICA ---
raw_clean = ica.apply(raw_work.copy())
print(f"\nICA 应用完成，排除了 {len(ica.exclude)} 个成分: {ica.exclude}")

# --- 4.7 ICA 完成后去掉 EOG 通道（后续分析只需 EEG） ---
raw_clean = raw_clean.pick('eeg')
print(f"去掉 EOG 通道后: {len(raw_clean.ch_names)} 个 EEG 通道")

# --- 4.8 对比 ICA 前后 ---
fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharex=True)

ch_name = 'EEG 021'
data_before_ica = raw_work.get_data(picks=[ch_name])[0]
data_after_ica = raw_clean.get_data(picks=[ch_name])[0]

t = raw_work.times
mask = t <= 5  # 前5秒

axes[0].plot(t[mask], data_before_ica[mask] * 1e6, color='#F44336', linewidth=0.5)
axes[0].set_title(f'Before ICA — {ch_name} (~C3)', fontsize=11)
axes[0].set_ylabel('μV')

axes[1].plot(t[mask], data_after_ica[mask] * 1e6, color='#4CAF50', linewidth=0.5)
axes[1].set_title(f'After ICA — {ch_name} (~C3)', fontsize=11)
axes[1].set_ylabel('μV')
axes[1].set_xlabel('Time (s)')

plt.suptitle('ICA Artifact Removal Effect', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{out_dir}_5_ica_before_after.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图5已保存: {out_dir}_5_ica_before_after.png")

# ============================================================
# 5. 完整流程：创建 Epochs + Evoked
# ============================================================
events = mne.find_events(raw, stim_channel='STI 014', verbose=False)
event_id = {
    'auditory/left': 1,
    'auditory/right': 2,
    'visual/left': 3,
    'visual/right': 4,
}

epochs = mne.Epochs(
    raw_clean, events, event_id,
    tmin=-0.2, tmax=0.8,
    baseline=(-0.2, 0),
    preload=True, verbose=False
)
epochs.drop_bad(reject={'eeg': 150e-6}, verbose=False)

print(f"\n--- 完整流程结果 ---")
print(f"有效 epochs: {len(epochs)}")
for cond in event_id:
    n = len(epochs[cond])
    print(f"  {cond}: {n} epochs")

evoked_al = epochs['auditory/left'].average()
evoked_vl = epochs['visual/left'].average()

# --- 5.1 听觉 vs 视觉 Evoked 对比 ---
fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

ch_idx = epochs.info['ch_names'].index('EEG 021')
times = epochs.times

axes[0].plot(times, evoked_al.data[ch_idx] * 1e6,
             color='#2196F3', linewidth=1.5, label='Auditory Left')
axes[0].plot(times, evoked_vl.data[ch_idx] * 1e6,
             color='#F44336', linewidth=1.5, label='Visual Left')
axes[0].axvline(0, color='red', linestyle='--', linewidth=1)
axes[0].axhline(0, color='gray', linewidth=0.5)
axes[0].set_title(f'Evoked Comparison at {ch_name} (~C3) — After Full Preprocessing',
                  fontsize=11)
axes[0].set_ylabel('μV')
axes[0].legend()

# 听觉 Evoked 拓扑图（关键时间点）
for t_point in [0.1, 0.2]:
    pass  # topo 图用 MNE 自带方法

axes[1].set_xlabel('Time (s)')
plt.tight_layout()
plt.savefig(f'{out_dir}_6_evoked_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图6已保存: {out_dir}_6_evoked_comparison.png")

# --- 5.2 预处理后 Evoked topo ---
fig = evoked_al.plot_joint(
    title='Auditory Left Evoked (after preprocessing)',
    show=False
)
fig.savefig(f'{out_dir}_7_evoked_topo_clean.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图7已保存: {out_dir}_7_evoked_topo_clean.png")

print("\n✅ Day 7 所有图表生成完毕!")
print("\n预处理流程总结:")
print("  ① 坏通道检测 → 标记/插值")
print("  ② 重参考 → 平均参考")
print("  ③ ICA → 自动检测 EOG → 去除伪迹")
print("  ④ 干净数据 → Epochs → Evoked")
