"""
Week 4 Day 10：解码流程 - 特征提取 + 分类器
MNE 解码完整流程：特征提取 + 分类 + 交叉验证
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
import matplotlib.font_manager as fm

for f in fm.fontManager.ttflist:
    if 'Noto' in f.name or 'CJK' in f.name or 'WenQuanYi' in f.name or 'SimHei' in f.name:
        plt.rcParams['font.sans-serif'] = [f.name]
        break
else:
    chinese_fonts = [f.name for f in fm.fontManager.ttflist
                     if any(x in f.name.lower() for x in ['noto', 'cjk', 'wqy', 'wenquanyi', 'droid', 'source han'])]
    if chinese_fonts:
        plt.rcParams['font.sans-serif'] = [chinese_fonts[0]]
    else:
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

import mne
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline as SkPipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay

# ─────────────────────────────────────────
# 0. 加载数据
# ─────────────────────────────────────────
print(">>> 加载 EEG 数据 …")

data_path = mne.datasets.testing.data_path(download=False)
fpath = os.path.join(data_path, 'MEG', 'sample', 'sample_audvis_trunc_raw.fif')

try:
    raw = mne.io.read_raw_fif(fpath, preload=True, verbose=False)
    print(f"  ✓ Testing 数据: {len(raw.ch_names)} 通道, sfreq={raw.info['sfreq']:.1f}Hz")
except Exception:
    from mne.datasets import sample
    data_path = sample.data_path(download=False)
    fpath = os.path.join(data_path, 'MEG', 'sample', 'sample_audvis_raw.fif')
    raw = mne.io.read_raw_fif(fpath, preload=True, verbose=False)
    print(f"  ✓ Sample 数据: {len(raw.ch_names)} 通道, sfreq={raw.info['sfreq']:.1f}Hz")

raw.pick_types(meg=False, eeg=True, eog=True, stim=True, verbose=False)
raw.resample(200, n_jobs=1)
raw.notch_filter(50, n_jobs=1)
raw.set_eeg_reference('average', projection=False, verbose=False)

# ─────────────────────────────────────────
# 1. 事件 + Epochs
# ─────────────────────────────────────────
print(">>> 提取 Epochs …")
events = mne.find_events(raw, stim_channel='STI 014', min_duration=0.005, verbose=False)

# 只保留 event_id 1,2,3,4（听觉/视觉 左右）
# 创建二分类标签：左侧(1,3) vs 右侧(2,4)
event_id = {'left': 1, 'right': 2}
# 筛选前两种事件
mask = np.isin(events[:, 2], [1, 2])
events_filtered = events[mask].copy()
events_filtered[:, 2] = np.where(events_filtered[:, 2] == 1, 1, 2)  # 1→1(left), 2→2(right)

epochs = mne.Epochs(
    raw, events_filtered, event_id,
    tmin=-0.2, tmax=0.5,
    baseline=(None, 0),
    preload=True, verbose=False,
    reject=dict(eeg=150e-6)
)
epochs.drop_bad(verbose=False)
print(f"  ✓ Epochs: {len(epochs)} 个, shape {epochs.get_data().shape}")

# ─────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────
out_dir = '/workspace/learning-journey/tracks/brain-computer-interface/projects/signal-processor/exercises'

def savefig(fig, idx, title):
    path = f'{out_dir}/day10_plot_{idx}.png'
    fig.savefig(path, dpi=120, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ 保存图 {idx}: {path}")
    return path

# ─────────────────────────────────────────
# 图 1：混淆矩阵 - LDA 分类
# ─────────────────────────────────────────
print("\n>>> 图 1：LDA 分类混淆矩阵")

X = epochs.get_data()                    # (n_ep, n_ch, n_times)
y = epochs.events[:, 2]                 # 标签 1=left, 2=right
# 降维：对每个 epoch 做时序均值 → (n_ep, n_ch)
X_mean = X.mean(axis=2)                 # shape: (n_ep, n_ch)
print(f"  特征 shape: {X_mean.shape}, 标签分布: {np.bincount(y)[1:]}")

# 标准化 + LDA
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_mean)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
clf = LinearDiscriminantAnalysis()
clf.fit(X_scaled, y)
scores = cross_val_score(clf, X_scaled, y, cv=cv)
y_pred = clf.predict(X_scaled)

print(f"  5折交叉验证准确率: {scores.mean()*100:.1f}% ± {scores.std()*100:.1f}%")
print(f"  训练集准确率: {(clf.predict(X_scaled) == y).mean()*100:.1f}%")

fig1, ax = plt.subplots(figsize=(6, 5))
cm = confusion_matrix(y, y_pred, labels=[1, 2])
disp = ConfusionMatrixDisplay(cm, display_labels=['Left', 'Right'])
disp.plot(ax=ax, cmap='Blues', values_format='d')
ax.set_title(f'LDA Confusion Matrix\nCV Accuracy: {scores.mean()*100:.1f}% ± {scores.std()*100:.1f}%', fontsize=12)
savefig(fig1, 1, 'LDA 混淆矩阵')

# ─────────────────────────────────────────
# 图 2：不同时间窗口的解码准确率
# ─────────────────────────────────────────
print("\n>>> 图 2：滑动时间窗口解码准确率")

# 时间窗口从 0ms 到 500ms，步长 50ms
t_starts = np.arange(0, 0.50, 0.05)   # 窗口起始时间
t_width = 0.10                          # 窗口宽度 100ms
accuracies = []
stds = []

for t_start in t_starts:
    t_end = t_start + t_width
    # 找对应的时间索引
    t_idx = (epochs.times >= t_start) & (epochs.times < t_end)
    X_win = X[:, :, t_idx].mean(axis=2)  # 时间平均
    X_s = scaler.fit_transform(X_win)
    sc = cross_val_score(LinearDiscriminantAnalysis(), X_s, y, cv=cv)
    accuracies.append(sc.mean())
    stds.append(sc.std())

fig2, ax = plt.subplots(figsize=(12, 5))
x_pos = t_starts * 1000 + t_width * 500  # 窗口中心 ms
ax.errorbar(x_pos, accuracies, yerr=stds, fmt='o-', color='#1f77b4',
            capsize=4, linewidth=2, markersize=6, label='LDA 准确率')
ax.axhline(0.5, color='red', linestyle='--', linewidth=1, label='随机 (50%)')
ax.axhline(accuracies[0], color='gray', linestyle=':', alpha=0.5)

# 标记最佳窗口
best_idx = np.argmax(accuracies)
ax.annotate(f'Best: {accuracies[best_idx]*100:.1f}%\nt={int(t_starts[best_idx]*1000)}ms',
            xy=(x_pos[best_idx], accuracies[best_idx]),
            xytext=(x_pos[best_idx] + 80, accuracies[best_idx] + 0.05),
            fontsize=9, color='darkblue',
            arrowprops=dict(arrowstyle='->', color='darkblue'))

ax.set_xlabel('Time Window Center [ms] (relative to event)', fontsize=11)
ax.set_ylabel('Decoding Accuracy', fontsize=11)
ax.set_title('Fig2: Sliding Window Decoding Accuracy - LDA', fontsize=13)
ax.set_ylim(0.3, 1.0)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
savefig(fig2, 2, '滑动窗口解码准确率')

# ─────────────────────────────────────────
# 图 3：不同分类器对比
# ─────────────────────────────────────────
print("\n>>> 图 3：分类器对比")
X_full = X.mean(axis=2)

classifiers = {
    'LDA': LinearDiscriminantAnalysis(),
    'SVM (RBF)': SVC(kernel='rbf', C=1.0),
    'SVM (Linear)': SVC(kernel='linear', C=1.0),
}
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
means, stds_c = [], []

fig3, axes = plt.subplots(1, 2, figsize=(14, 5))

ax = axes[0]
for (name, clf_item), color in zip(classifiers.items(), colors):
    sc = cross_val_score(clf_item, scaler.fit_transform(X_full), y, cv=cv)
    means.append(sc.mean())
    stds_c.append(sc.std())
    print(f"  {name}: {sc.mean()*100:.1f}% ± {sc.std()*100:.1f}%")
    ax.bar(name, sc.mean(), yerr=sc.std(), color=color, alpha=0.7, capsize=5)

ax.axhline(0.5, color='red', linestyle='--', linewidth=1, label='Random (50%)')
ax.set_ylabel('Accuracy')
ax.set_title('Fig3a: Classifier Comparison (mean ± std)', fontsize=12)
ax.set_ylim(0.3, 1.0)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3, axis='y')

ax = axes[1]
ax.bar(range(len(means)), means, yerr=stds_c, color=colors, alpha=0.7, capsize=5)
ax.set_xticks(range(len(means)))
ax.set_xticklabels(classifiers.keys())
ax.axhline(0.5, color='red', linestyle='--', linewidth=1)
ax.set_ylabel('Accuracy')
ax.set_title('Fig3b: Classifier Rank', fontsize=12)
ax.set_ylim(0.3, 1.0)
ax.grid(True, alpha=0.3, axis='y')
for i, (m, s) in enumerate(zip(means, stds_c)):
    ax.text(i, m + s + 0.02, f'{m*100:.1f}%', ha='center', fontsize=10)

savefig(fig3, 3, '分类器对比')

# ─────────────────────────────────────────
# 图 4：空间模式（CSP 风格可视化）
# ─────────────────────────────────────────
print("\n>>> 图 4：LDA 空间模式")
clf_lda = LinearDiscriminantAnalysis()
clf_lda.fit(scaler.fit_transform(X_full), y)

# LDA 系数 = 空间模式（每个通道的判别权重）
pattern = clf_lda.coef_[0]  # shape: (n_ch,)
# 取绝对值看强度，符号表示方向
ch_names = epochs.ch_names

fig4, axes = plt.subplots(1, 2, figsize=(14, 5))

# 左图：空间模式权重
ax = axes[0]
# 取绝对值排序，显示 Top 通道
sorted_idx = np.argsort(np.abs(pattern))[::-1]
top_n = 15
ax.barh(range(top_n), pattern[sorted_idx[:top_n]], color='steelblue', alpha=0.8)
ax.set_yticks(range(top_n))
ax.set_yticklabels([ch_names[i] for i in sorted_idx[:top_n]], fontsize=9)
ax.set_xlabel('LDA Coefficient (spatial pattern)', fontsize=11)
ax.set_title('Fig4a: LDA Spatial Pattern - Top Channels', fontsize=12)
ax.axvline(0, color='gray', linestyle='--', linewidth=0.8)
ax.grid(True, alpha=0.3, axis='x')
ax.invert_yaxis()

# 右图：Top 通道的权重方向（正值 vs 负值）
ax = axes[1]
pos_ch = [ch_names[i] for i in sorted_idx[:top_n] if pattern[i] > 0]
neg_ch = [ch_names[i] for i in sorted_idx[:top_n] if pattern[i] < 0]
pos_weights = [pattern[i] for i in sorted_idx[:top_n] if pattern[i] > 0]
neg_weights = [pattern[i] for i in sorted_idx[:top_n] if pattern[i] < 0]

y_pos = np.arange(len(pos_ch))
ax.barh(y_pos, pos_weights, color='#e74c3c', alpha=0.8, label=f'→ Left class ({len(pos_ch)} ch)')
ax.set_yticks(y_pos)
ax.set_yticklabels(pos_ch, fontsize=9)
ax.axvline(0, color='gray', linestyle='--', linewidth=0.8)
ax.set_xlabel('LDA Coefficient', fontsize=11)
ax.set_title('Fig4b: Left-class channels (positive weights)', fontsize=12)
ax.grid(True, alpha=0.3, axis='x')
ax.invert_yaxis()

fig4.suptitle('Fig4: LDA Spatial Pattern - Discriminative Channels', fontsize=14, fontweight='bold')
savefig(fig4, 4, 'LDA 空间模式')

# ─────────────────────────────────────────
# 图 5：交叉验证每折的准确率
# ─────────────────────────────────────────
print("\n>>> 图 5：交叉验证折详情")
fig5, ax = plt.subplots(figsize=(8, 4))
ax.bar(range(1, 6), scores * 100, color='#3498db', alpha=0.8)
ax.axhline(scores.mean() * 100, color='red', linestyle='--', linewidth=1.5,
          label=f'Mean: {scores.mean()*100:.1f}%')
ax.set_xlabel('Fold', fontsize=11)
ax.set_ylabel('Accuracy [%]', fontsize=11)
ax.set_title('Fig5: 5-Fold Cross-Validation Scores (LDA)', fontsize=13)
ax.set_xticks(range(1, 6))
ax.set_ylim(0.3, 1.0)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3, axis='y')
for i, s in enumerate(scores):
    ax.text(i + 1, s * 100 + 0.01, f'{s*100:.1f}%', ha='center', fontsize=9)
savefig(fig5, 5, '交叉验证折详情')

# ─────────────────────────────────────────
# 图 6：ERP 地形图差异
# ─────────────────────────────────────────
print("\n>>> 图 6：ERP 地形图差异")
# 左侧 vs 右侧事件 ERP
evoked_left = epochs['left'].average()
evoked_right = epochs['right'].average()
diff = mne.combine_evoked([evoked_left, evoked_right], weights=[1, -1])

# 时间窗口平均 (100-300ms)
t_start_idx = np.argmin(np.abs(epochs.times - 0.1))
t_end_idx = np.argmin(np.abs(epochs.times - 0.3))
diff_crop = diff.copy().crop(tmin=0.1, tmax=0.3)
diff_mean = diff_crop.data.mean(axis=1)

fig6, axes = plt.subplots(1, 3, figsize=(15, 4))

# 截取时间窗口
evoked_left_crop = evoked_left.copy().crop(tmin=0.1, tmax=0.3)
evoked_right_crop = evoked_right.copy().crop(tmin=0.1, tmax=0.3)

evoked_left_crop.plot_topomap(times=0.2, axes=axes[0], show=False, colorbar=False)
axes[0].set_title('Left\n(100-300ms avg)', fontsize=11)

evoked_right_crop.plot_topomap(times=0.2, axes=axes[1], show=False, colorbar=False)
axes[1].set_title('Right\n(100-300ms avg)', fontsize=11)

# 差异图
diff_crop = diff.copy().crop(tmin=0.1, tmax=0.3)
diff_topo = diff_crop.data.mean(axis=1)
vmax = max(abs(diff_topo.min()), abs(diff_topo.max()))
im = axes[2].imshow(diff_topo[:, np.newaxis], cmap='RdBu_r',
                     aspect='auto', vmin=-vmax, vmax=vmax)
axes[2].set_title('Difference\n(Left - Right)', fontsize=11)
plt.colorbar(im, ax=axes[2], shrink=0.8)

fig6.suptitle('Fig6: ERP Topomap - Left vs Right (100-300ms)', fontsize=14, fontweight='bold')
savefig(fig6, 6, 'ERP 地形图差异')

# ─────────────────────────────────────────
# 图 7：时间演化分类（逐时间点）
# ─────────────────────────────────────────
print("\n>>> 图 7：逐时间点分类准确率")
times = epochs.times
accuracies_t = []
stds_t = []

for t_idx in range(0, len(times), 5):   # 每隔 5 个点采样
    X_t = X[:, :, t_idx]
    X_s = scaler.fit_transform(X_t)
    sc = cross_val_score(LinearDiscriminantAnalysis(), X_s, y, cv=cv)
    accuracies_t.append(sc.mean())
    stds_t.append(sc.std())

times_sampled = times[::5]

fig7, ax = plt.subplots(figsize=(12, 5))
ax.fill_between(times_sampled * 1000, np.array(accuracies_t) - np.array(stds_t),
                np.array(accuracies_t) + np.array(stds_t), alpha=0.2, color='#1f77b4')
ax.plot(times_sampled * 1000, accuracies_t, color='#1f77b4', linewidth=1.5, label='LDA')
ax.axhline(0.5, color='red', linestyle='--', linewidth=1, label='Random (50%)')
ax.axvline(0, color='gray', linestyle=':', linewidth=1)
ax.set_xlabel('Time [ms] (relative to event)', fontsize=11)
ax.set_ylabel('Decoding Accuracy', fontsize=11)
ax.set_title('Fig7: Time-resolved Decoding Accuracy (per-time-point LDA)', fontsize=13)
ax.set_ylim(0.3, 1.0)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

# 标记显著超过随机的时间段
sig_mask = np.array(accuracies_t) > 0.5 + np.array(stds_t)
if sig_mask.any():
    sig_times = times_sampled[sig_mask] * 1000
    ax.fill_betweenx([0.3, 1.0], sig_times.min(), sig_times.max(),
                     alpha=0.05, color='green', label='Sig > chance')

savefig(fig7, 7, '逐时间点分类准确率')

# ─────────────────────────────────────────
# 图 8：分类报告 + 总结
# ─────────────────────────────────────────
print("\n>>> 图 8：分类报告")
fig8, axes = plt.subplots(1, 2, figsize=(14, 5))

# 左：精确率/召回率/F1
report = classification_report(y, y_pred, target_names=['Left', 'Right'],
                              output_dict=True, zero_division=0)
metrics = ['precision', 'recall', 'f1-score']
x = np.arange(len(metrics))
width = 0.35
ax = axes[0]
bars1 = ax.bar(x - width/2, [report['Left'][m] for m in metrics], width,
               label='Left', color='#3498db', alpha=0.8)
bars2 = ax.bar(x + width/2, [report['Right'][m] for m in metrics], width,
               label='Right', color='#e74c3c', alpha=0.8)
ax.set_ylabel('Score')
ax.set_title('Fig8a: Precision / Recall / F1', fontsize=12)
ax.set_xticks(x)
ax.set_xticklabels(['Precision', 'Recall', 'F1-Score'])
ax.set_ylim(0, 1.1)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3, axis='y')
for bar in list(bars1) + list(bars2):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
            f'{bar.get_height():.2f}', ha='center', fontsize=8)

# 右：总体统计
ax = axes[1]
summary = {
    'Overall Accuracy': scores.mean(),
    'Chance Level': 0.5,
}
ax.barh(list(summary.keys()), list(summary.values()),
        color=['#2ca02c', '#95a5a6'], alpha=0.8)
for i, v in enumerate(summary.values()):
    ax.text(v + 0.01, i, f'{v*100:.1f}%', va='center', fontsize=11)
ax.set_xlim(0, 1.1)
ax.set_title('Fig8b: Overall Performance Summary', fontsize=12)
ax.grid(True, alpha=0.3, axis='x')

fig8.suptitle('Fig8: Decoding Report - LDA', fontsize=14, fontweight='bold')
savefig(fig8, 8, '分类报告')

# ─────────────────────────────────────────
# 汇总
# ─────────────────────────────────────────
print("\n" + "="*50)
print("汇总")
print("="*50)
print(f"  Epochs: {len(epochs)} 个")
print(f"  特征: 通道时序均值 → {X_mean.shape[1]} 维向量")
print(f"  分类器: LDA, SVM-RBF, SVM-Linear")
print(f"  交叉验证: 5折 StratifiedKFold")
print(f"  LDA CV准确率: {scores.mean()*100:.1f}% ± {scores.std()*100:.1f}%")
print(f"  最佳分类器: {max(zip(classifiers.keys(), means), key=lambda x: x[1])[0]}")
print(f"  图 1-8 已保存")
print("="*50)
