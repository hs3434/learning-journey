"""
Week 4 Day 5: Decoding Pipeline
================================
解码流程：特征提取 + 分类器
简单 MI 分类
"""
import numpy as np
import mne
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import cross_val_score, StratifiedKFold
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

out_dir = '/tmp'
mne.set_log_level('WARNING')

# ============================================================
# 1. 加载数据
# ============================================================
print("=" * 60)
print("1. 加载数据")
print("=" * 60)

sample_data_folder = mne.datasets.sample.data_path()
raw_file = sample_data_folder / 'MEG' / 'sample' / 'sample_audvis_raw.fif'

raw = mne.io.read_raw_fif(raw_file, preload=True, verbose=False)
raw.pick('eeg')
raw.filter(l_freq=0.5, h_freq=40, verbose=False)

print(f"数据 shape: {raw.get_data().shape}")
print(f"采样率: {raw.info['sfreq']} Hz")

# ============================================================
# 2. 创建 Epochs
# ============================================================
print("\n" + "=" * 60)
print("2. 创建 Epochs")
print("=" * 60)

events = mne.find_events(raw, stim_channel='STI 014', verbose=False)

event_id = {
    'auditory/left': 1,
    'auditory/right': 2,
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
print(f"数据 shape: {epochs.get_data().shape}")

# ============================================================
# 3. 特征提取
# ============================================================
print("\n" + "=" * 60)
print("3. 特征提取")
print("=" * 60)

X = epochs.get_data()
y = epochs.events[:, 2]

print(f"特征矩阵 X: {X.shape}")
print(f"标签 y: {y.shape}")
print(f"类别分布: {np.bincount(y)}")

def extract_features(epochs_data):
    """提取特征：平均、峰值、频段功率"""
    n_epochs, n_channels, n_times = epochs_data.shape
    features = []

    for epoch in epochs_data:
        epoch_features = []

        epoch_features.append(epoch.mean(axis=1))
        epoch_features.append(epoch.max(axis=1))
        epoch_features.append(epoch.min(axis=1))
        epoch_features.append(np.std(epoch, axis=1))

        psd = []
        for ch_data in epoch:
            freqs, psd_ch = mne.time_frequency.psd_arrayWelch(ch_data, sfreq=256, fmin=8, fmax=30)
            psd.append(psd_ch.mean())
        epoch_features.append(np.array(psd))

        features.append(np.concatenate(epoch_features))

    return np.array(features)

X_features = extract_features(X)
print(f"提取后特征矩阵: {X_features.shape}")

# ============================================================
# 4. 分类
# ============================================================
print("\n" + "=" * 60)
print("4. 分类")
print("=" * 60)

clf = LinearDiscriminantAnalysis()

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(clf, X_features, y, cv=cv)

print(f"5折交叉验证准确率:")
print(f"  各折: {scores}")
print(f"  均值: {scores.mean():.4f}")
print(f"  标准差: {scores.std():.4f}")

# ============================================================
# 5. 可视化
# ============================================================
print("\n" + "=" * 60)
print("5. 可视化")
print("=" * 60)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

axes[0, 0].bar(['Left', 'Right'], [np.sum(y == 1), np.sum(y == 2)])
axes[0, 0].set_title('Class Distribution')
axes[0, 0].set_ylabel('Count')

axes[0, 1].boxplot([X_features[y == 1, 0], X_features[y == 2, 0]], labels=['Left', 'Right'])
axes[0, 1].set_title('Feature Distribution (mean)')
axes[0, 1].set_ylabel('Feature Value')

axes[1, 0].bar(range(5), scores)
axes[1, 0].set_xlabel('Fold')
axes[1, 0].set_ylabel('Accuracy')
axes[1, 0].set_title('Cross-Validation Results')
axes[1, 0].set_ylim(0, 1)
axes[1, 0].axhline(scores.mean(), color='red', linestyle='--', label=f'Mean: {scores.mean():.3f}')
axes[1, 0].legend()

evoked_left = epochs['auditory/left'].average()
evoked_right = epochs['auditory/right'].average()
times = epochs.times * 1e3
axes[1, 1].plot(times, evoked_left.data[0] * 1e6, label='Left')
axes[1, 1].plot(times, evoked_right.data[0] * 1e6, label='Right')
axes[1, 1].axvline(0, color='red', linestyle='--')
axes[1, 1].set_xlabel('Time (ms)')
axes[1, 1].set_ylabel('Amplitude (μV)')
axes[1, 1].set_title('Evoked Response Comparison')
axes[1, 1].legend()

plt.tight_layout()
plt.savefig(f'{out_dir}/day5_decoding.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"图已保存: {out_dir}/day5_decoding.png")

print("\n✅ Day 5 完成! Week 4 全部内容完毕!")