"""
Week 1 Day 5: Comprehensive EEG Data Processing
===============================================
综合练习：读取 EEG 数据并可视化
使用 MNE 加载真实 EEG 数据进行完整处理
"""
import numpy as np
import mne
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

out_dir = '/tmp'
mne.set_log_level('WARNING')

# ============================================================
# 1. 加载 MNE 示例数据
# ============================================================
print("=" * 60)
print("1. 加载 MNE 示例数据")
print("=" * 60)

sample_data_folder = mne.datasets.sample.data_path()
raw_file = sample_data_folder / 'MEG' / 'sample' / 'sample_audvis_raw.fif'

raw = mne.io.read_raw_fif(raw_file, preload=True, verbose=False)
raw.pick('eeg')

print(f"数据 shape: {raw.get_data().shape}")
print(f"采样率: {raw.info['sfreq']} Hz")
print(f"通道数: {len(raw.ch_names)}")
print(f"时长: {raw.times[-1]:.1f} 秒")

# ============================================================
# 2. 预处理
# ============================================================
print("\n" + "=" * 60)
print("2. 预处理")
print("=" * 60)

raw.filter(l_freq=0.5, h_freq=40, verbose=False)
raw.notch_filter(freqs=50, verbose=False)

print("滤波完成: 0.5-40Hz 带通 + 50Hz Notch")

# ============================================================
# 3. 事件与 Epochs
# ============================================================
print("\n" + "=" * 60)
print("3. 事件与 Epochs")
print("=" * 60)

events = mne.find_events(raw, stim_channel='STI 014', verbose=False)
event_id = {
    'auditory/left': 1,
    'auditory/right': 2,
    'visual/left': 3,
    'visual/right': 4
}

epochs = mne.Epochs(
    raw, events, event_id,
    tmin=-0.2, tmax=0.5,
    baseline=(-0.2, 0),
    preload=True,
    verbose=False
)

epochs.drop_bad(reject={'eeg': 150e-6}, verbose=False)

print(f"Epochs 数量: {len(epochs)}")
print(f"各条件 epoch 数:")
for name in event_id:
    print(f"  {name}: {len(epochs[name])}")

# ============================================================
# 4. 可视化
# ============================================================
print("\n" + "=" * 60)
print("4. 可视化")
print("=" * 60)

evoked_aud_left = epochs['auditory/left'].average()
evoked_vis_left = epochs['visual/left'].average()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# PSD
axes[0, 0].psd = raw.compute_psd(fmax=50, verbose=False).plot(axes=axes[0, 0], show=False)[0]
axes[0, 0].set_title('Raw EEG Power Spectrum')

# Epochs average
times = epochs.times * 1e3
ch_idx = 0
evoked_data = evoked_aud_left.data[ch_idx] * 1e6
axes[0, 1].plot(times, evoked_data)
axes[0, 1].axvline(0, color='red', linestyle='--')
axes[0, 1].set_title('Evoked (Auditory Left)')
axes[0, 1].set_xlabel('Time (ms)')
axes[0, 1].set_ylabel('Amplitude (μV)')

# Comparison
axes[1, 0].plot(times, evoked_aud_left.data[ch_idx] * 1e6, label='Auditory')
axes[1, 0].plot(times, evoked_vis_left.data[ch_idx] * 1e6, label='Visual')
axes[1, 0].axvline(0, color='red', linestyle='--')
axes[1, 0].set_title('Auditory vs Visual')
axes[1, 0].set_xlabel('Time (ms)')
axes[1, 0].legend()

# Topomap
axes[1, 1].set_title('Evoked Topomap at 0ms')
evoked_aud_left.plot_topomap(times=[0.1], axes=axes[1, 1], show=False)

plt.tight_layout()
plt.savefig(f'{out_dir}/day5_comprehensive.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图已保存: {out_dir}/day5_comprehensive.png")

# ============================================================
# 5. 数据导出
# ============================================================
print("\n" + "=" * 60)
print("5. 数据导出")
print("=" * 60)

import pandas as pd

df = raw.to_data_frame()
print(f"导出 DataFrame shape: {df.shape}")

evoked_df = evoked_aud_left.to_data_frame()
print(f"导出 Evoked DataFrame shape: {evoked_df.shape}")

print("\n✅ Day 5 完成! Week 1 综合练习完毕")