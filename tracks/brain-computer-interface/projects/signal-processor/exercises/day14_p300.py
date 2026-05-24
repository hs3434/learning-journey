"""
Day 14: P300 Event-Related Potential
=====================================

Week 5 Day 4: P300 principle, Oddball paradigm, classification methods

Goals:
1. Understand P300 generation mechanism and Oddball paradigm
2. Learn P300 speller (Farwell-Donchin matrix)
3. Implement P300 detection with stepwise LDA
4. Compare P300 with other BCI paradigms
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

out_dir = Path(__file__).parent
out_dir.mkdir(exist_ok=True)

# =============================================================================
# Figure 1: P300 Generation Mechanism — Oddball Paradigm
# =============================================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('P300 & Oddball Paradigm', fontsize=16, fontweight='bold')

fs = 250
t = np.arange(-0.2, 0.8, 1/fs)

# 1a: Oddball stimulus sequence
ax1 = axes[0, 0]
np.random.seed(42)
n_stimuli = 20
is_target = np.random.rand(n_stimuli) < 0.2  # 20% target probability
stim_times = np.arange(n_stimuli)

for i, (ti, tgt) in enumerate(zip(stim_times, is_target)):
    color = 'red' if tgt else 'gray'
    marker = 'v' if tgt else '^'
    size = 120 if tgt else 60
    ax1.scatter(ti, 1, marker=marker, s=size, c=color, zorder=5)

ax1.set_xlabel('Stimulus #')
ax1.set_title('Oddball Sequence (P=0.2 for target)')
ax1.set_ylim(0.5, 1.5)
ax1.set_yticks([])
# Legend
ax1.scatter([], [], marker='v', c='red', s=80, label='Target (rare)')
ax1.scatter([], [], marker='^', c='gray', s=60, label='Standard (frequent)')
ax1.legend(fontsize=9, loc='upper right')
ax1.grid(True, alpha=0.3, axis='x')

# 1b: ERP waveform — target vs standard
ax2 = axes[0, 1]

# Standard stimulus ERP (small N1/P2, no P300)
n1_std = -np.exp(-((t - 0.1)**2) / 0.002) * 2.0
p2_std = np.exp(-((t - 0.18)**2) / 0.003) * 1.5
erp_std = n1_std + p2_std + np.random.randn(len(t)) * 0.3

# Target stimulus ERP (large N1/P2 + P300)
n1_tgt = -np.exp(-((t - 0.1)**2) / 0.002) * 2.5
p2_tgt = np.exp(-((t - 0.18)**2) / 0.003) * 2.0
p300 = np.exp(-((t - 0.30)**2) / 0.008) * 5.0  # P300 at ~300ms
erp_tgt = n1_tgt + p2_tgt + p300 + np.random.randn(len(t)) * 0.3

ax2.plot(t * 1000, erp_tgt, 'r-', linewidth=2, label='Target (oddball)')
ax2.plot(t * 1000, erp_std, 'gray', linewidth=1.5, alpha=0.7, label='Standard')
ax2.axhline(0, color='k', linestyle='-', alpha=0.3)
ax2.axvline(0, color='k', linestyle='--', alpha=0.3, label='Stimulus onset')
ax2.fill_between(t * 1000, 0, erp_tgt, where=(t > 0.25) & (t < 0.45),
                 alpha=0.3, color='red', label='P300 window')
ax2.set_xlabel('Time (ms)')
ax2.set_ylabel('Amplitude (uV)')
ax2.set_title('ERP: Target vs Standard')
ax2.legend(fontsize=8)
ax2.set_xlim(-200, 800)
ax2.grid(True, alpha=0.3)

# 1c: P300 scalp topography (simplified)
ax3 = axes[1, 0]
ax3.set_aspect('equal')
ax3.axis('off')
ax3.set_title('P300 Scalp Distribution (Pz maximum)')

# Head outline
theta = np.linspace(0, 2*np.pi, 100)
ax3.plot(np.cos(theta), np.sin(theta), 'k-', linewidth=2)

# Simulate P300 amplitude distribution (parietal maximum)
electrodes_simplified = {
    'Fz': (0, 0.6, 1.0), 'Cz': (0, 0.15, 3.0), 'Pz': (0, -0.35, 5.0),
    'Oz': (0, -0.75, 2.0), 'F3': (-0.4, 0.45, 0.8), 'F4': (0.4, 0.45, 0.8),
    'C3': (-0.4, 0, 2.0), 'C4': (0.4, 0, 2.0),
    'P3': (-0.4, -0.35, 4.0), 'P4': (0.4, -0.35, 4.0),
    'T3': (-0.85, 0, 0.5), 'T4': (0.85, 0, 0.5),
}

max_amp = 5.0
for name, (x, y, amp) in electrodes_simplified.items():
    intensity = amp / max_amp
    color = plt.cm.RdYlBu_r(intensity)
    circle = plt.Circle((x, y), 0.08, color=color, zorder=5, ec='black', lw=1)
    ax3.add_patch(circle)
    ax3.text(x, y - 0.15, name, ha='center', fontsize=7)

# Colorbar
sm = plt.cm.ScalarMappable(cmap='RdYlBu_r', norm=plt.Normalize(0, 5))
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax3, shrink=0.6, label='P300 Amplitude (uV)')

ax3.set_xlim(-1.3, 1.3)
ax3.set_ylim(-1.1, 1.1)

# 1d: P300 characteristics summary
ax4 = axes[1, 1]
ax4.axis('off')

summary = """P300 Key Characteristics
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Peak latency:  250-400 ms post-stimulus
Peak location: Pz (parietal midline)
Amplitude:     2-10 uV

Generation conditions:
  1. Rare, task-relevant stimulus (Oddball)
  2. Subject must attend/count targets
  3. Probability P(target) < 0.3

Factors affecting P300:
  • Target probability ↓ → amplitude ↑
  • Attention ↑ → amplitude ↑
  • Task difficulty ↑ → latency ↑
  • Age ↑ → latency ↑, amplitude ↓

Neural source:
  • Posterior cingulate / PCC
  • Temporal-parietal junction
  • Lacaille & Bhatt (2024)
"""
ax4.text(0.05, 0.95, summary, transform=ax4.transAxes,
        fontsize=10, verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='#F5F5F5', edgecolor='#333'))

plt.tight_layout()
path = out_dir / 'day14_plot_1.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 1 saved: {path}')

# =============================================================================
# Figure 2: P300 Speller (Farwell-Donchin Matrix)
# =============================================================================
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle('P300 Speller (Farwell & Donchin, 1988)', fontsize=14, fontweight='bold')

# 2a: 6x6 character matrix
ax1 = axes[0]
chars = list('ABCDEF') + list('GHIJKL') + list('MNOPQR') + \
        list('STUVWX') + list('YZ1234') + list('567890')

ax1.set_xlim(-0.5, 5.5)
ax1.set_ylim(5.5, -0.5)
ax1.set_title('Character Matrix')

for i, ch in enumerate(chars):
    row, col = divmod(i, 6)
    # Highlight target character
    if ch == 'H':
        rect = plt.Rectangle((col-0.45, row-0.45), 0.9, 0.9,
                             facecolor='red', alpha=0.3, zorder=2)
        ax1.add_patch(rect)
    ax1.text(col, row, ch, ha='center', va='center', fontsize=14, fontweight='bold')

ax1.set_xticks([])
ax1.set_yticks([])

# 2b: Flashing sequence (row/column)
ax2 = axes[1]
ax2.set_title('Flash Sequence')

# 12 flashes (6 rows + 6 columns), mark which contain target
target_row = 1  # 'H' is in row 1
target_col = 1  # 'H' is in col 1
flash_labels = [f'Row {i}' for i in range(6)] + [f'Col {i}' for i in range(6)]
is_target_flash = [i == target_row for i in range(6)] + [i == target_col for i in range(6)]

for i, (label, is_tgt) in enumerate(zip(flash_labels, is_target_flash)):
    color = 'red' if is_tgt else 'lightgray'
    ax2.barh(i, 1, color=color, edgecolor='black', height=0.7)
    ax2.text(0.5, i, label, ha='center', va='center', fontsize=9,
            color='white' if is_tgt else 'black')

ax2.set_yticks(range(12))
ax2.set_yticklabels(flash_labels, fontsize=8)
ax2.set_xlabel('Flash Duration')
ax2.invert_yaxis()

# 2c: ERP for target vs non-target flash
ax3 = axes[2]
t_erp = np.arange(-0.1, 0.6, 1/fs)

# Target flash (row/col containing 'H')
erp_target = np.exp(-((t_erp - 0.3)**2) / 0.005) * 6.0 + \
             -np.exp(-((t_erp - 0.15)**2) / 0.002) * 2.0

# Non-target flash
erp_nontarget = -np.exp(-((t_erp - 0.15)**2) / 0.002) * 1.5 + \
                np.exp(-((t_erp - 0.2)**2) / 0.003) * 0.8

ax3.plot(t_erp * 1000, erp_target, 'r-', linewidth=2, label='Target flash')
ax3.plot(t_erp * 1000, erp_nontarget, 'gray', linewidth=1.5, label='Non-target flash')
ax3.axvline(0, color='k', linestyle='--', alpha=0.5)
ax3.fill_between(t_erp * 1000, 0, erp_target, where=(t_erp > 0.25) & (t_erp < 0.4),
                 alpha=0.3, color='red')
ax3.set_xlabel('Time (ms)')
ax3.set_ylabel('Amplitude (uV)')
ax3.set_title('ERP at Pz (flash-locked)')
ax3.legend(fontsize=8)
ax3.set_xlim(-100, 600)
ax3.grid(True, alpha=0.3)

plt.tight_layout()
path = out_dir / 'day14_plot_2.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 2 saved: {path}')

# =============================================================================
# Figure 3: P300 Speller Timing Diagram
# =============================================================================
fig, ax = plt.subplots(figsize=(14, 6))
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.axis('off')
ax.set_title('P300 Speller Timing: One Character Selection', fontsize=14, fontweight='bold')

# Timeline
ax.annotate('', xy=(13.5, 0.5), xytext=(0.5, 0.5),
           arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(7, 0.2, 'Time', ha='center', fontsize=10)

# Flash intervals
flash_duration = 0.125  # 125ms
isi = 0.075  # 75ms inter-stimulus interval
total_flash = flash_duration + isi  # 200ms per flash
n_repeats = 15  # 15 repetitions for reliable detection
n_flashes_per_rep = 12  # 6 rows + 6 columns

# Draw a few representative flashes
colors_flash = []
for rep in range(3):  # Show 3 repetitions
    for i in range(12):
        x_start = 1 + rep * 3.5 + i * 0.25
        if x_start > 13:
            break
        is_tgt = (i == target_row or i == target_col)
        color = '#FFCDD2' if is_tgt else '#E0E0E0'
        rect = plt.Rectangle((x_start, 2), 0.2, 1.5,
                             facecolor=color, edgecolor='gray', linewidth=0.5)
        ax.add_patch(rect)

# Labels for repetitions
for rep in range(3):
    x_center = 1 + rep * 3.5 + 12 * 0.25 / 2
    ax.text(x_center, 3.8, f'Rep {rep+1}/{n_repeats}', ha='center', fontsize=9)

ax.text(1 - 0.3, 2.75, 'Flashes', ha='right', va='center', fontsize=10, rotation=90)

# ERP extraction windows
for rep in range(3):
    for i in [target_row, target_col]:
        x_start = 1 + rep * 3.5 + i * 0.25
        if x_start > 13:
            continue
        # Small P300 icon
        ax.annotate('P3', xy=(x_start + 0.1, 5), xytext=(x_start + 0.1, 5.8),
                   fontsize=7, color='red', ha='center',
                   arrowprops=dict(arrowstyle='->', color='red', lw=1))

# Processing pipeline
steps = [
    (3, 6.5, 'Epoch\nExtraction', '#E3F2FD'),
    (6, 6.5, 'Averaging\n(across reps)', '#E8F5E9'),
    (9, 6.5, 'Feature\nExtraction', '#FFF3E0'),
    (12, 6.5, 'LDA\nClassification', '#F3E5F5'),
]

for x, y, text, color in steps:
    rect = plt.Rectangle((x-0.8, y-0.7), 1.6, 1.4,
                         facecolor=color, edgecolor='#333', linewidth=2)
    ax.add_patch(rect)
    ax.text(x, y, text, ha='center', va='center', fontsize=9, fontweight='bold')

for i in range(len(steps)-1):
    x1 = steps[i][0] + 0.8
    x2 = steps[i+1][0] - 0.8
    ax.annotate('', xy=(x2, 6.5), xytext=(x1, 6.5),
               arrowprops=dict(arrowstyle='->', color='green', lw=2))

# Timing info
info = f'Flash: {flash_duration*1000:.0f}ms on + {isi*1000:.0f}ms off = {total_flash*1000:.0f}ms/trial\n' \
       f'12 flashes/rep x {n_repeats} reps = {12*n_repeats} flashes total\n' \
       f'Total time: {12 * n_repeats * total_flash:.1f}s per character\n' \
       f'ITR: ~{60 / (12 * n_repeats * total_flash) * np.log2(36):.1f} bits/min (36 chars)'

ax.text(7, 0.9, info, ha='center', va='center', fontsize=9,
       bbox=dict(boxstyle='round', facecolor='#FFF9C4', edgecolor='#F9A825'))

plt.tight_layout()
path = out_dir / 'day14_plot_3.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 3 saved: {path}')

# =============================================================================
# Figure 4: P300 Detection — Feature Extraction & Classification
# =============================================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('P300 Detection: Feature Extraction & Classification', fontsize=14, fontweight='bold')

# 4a: Single-trial vs averaged ERP
ax1 = axes[0, 0]
t_epoch = np.arange(-0.1, 0.6, 1/fs)
np.random.seed(42)

# Single trials (noisy)
for trial in range(10):
    noise = np.random.randn(len(t_epoch)) * 3.0
    p300_sig = np.exp(-((t_epoch - 0.3)**2) / 0.005) * 5.0
    single = p300_sig + noise - 1.5
    ax1.plot(t_epoch * 1000, single, 'r-', alpha=0.15, linewidth=0.5)

# Averaged (10 trials)
avg_noise = np.random.randn(len(t_epoch)) * 3.0 / np.sqrt(10)
avg_signal = np.exp(-((t_epoch - 0.3)**2) / 0.005) * 5.0 + avg_noise - 1.5
ax1.plot(t_epoch * 1000, avg_signal, 'r-', linewidth=2, label='Average (10 trials)')

ax1.axhline(0, color='k', linestyle='-', alpha=0.3)
ax1.axvline(0, color='k', linestyle='--', alpha=0.3)
ax1.set_xlabel('Time (ms)')
ax1.set_ylabel('Amplitude (uV)')
ax1.set_title('Single-trial vs Averaged ERP (target)')
ax1.legend(fontsize=9)
ax1.set_xlim(-100, 600)
ax1.grid(True, alpha=0.3)

# 4b: Feature extraction — all time window amplitudes (grouped boxplot)
ax2 = axes[0, 1]

# Define time windows for feature extraction
windows = [
    ('N1 (100-150ms)', 0.1, 0.15),
    ('P2 (150-250ms)', 0.15, 0.25),
    ('P3a (250-350ms)', 0.25, 0.35),
    ('P3b (300-400ms)', 0.30, 0.40),
    ('SW (400-550ms)', 0.40, 0.55),
]

# Generate features for target and non-target
n_trials = 50
features_target = []
features_nontarget = []

for _ in range(n_trials):
    feat_t = []
    feat_nt = []
    for name, t_start, t_end in windows:
        mask = (t_epoch >= t_start) & (t_epoch < t_end)
        # Target: P300 present
        sig_t = np.exp(-((t_epoch - 0.3)**2) / 0.005) * 5.0
        feat_t.append(np.mean(sig_t[mask]) + np.random.randn() * 1.0)
        # Non-target: no P300
        feat_nt.append(np.random.randn() * 1.0)
    features_target.append(feat_t)
    features_nontarget.append(feat_nt)

features_target = np.array(features_target)
features_nontarget = np.array(features_nontarget)

p3b_idx = 3  # P3b window index

window_labels = [name.split(' ')[0] for name, _, _ in windows]  # N1, P2, P3a, P3b, SW
x_pos = np.arange(len(windows))
width = 0.35

# Boxplot for each window: target vs non-target
bp_target = ax2.boxplot([features_target[:, i] for i in range(len(windows))],
                        positions=x_pos - width/2, widths=width,
                        patch_artist=True, showfliers=False,
                        medianprops=dict(color='darkred', linewidth=2),
                        whiskerprops=dict(color='red'),
                        capprops=dict(color='red'))
bp_nontarget = ax2.boxplot([features_nontarget[:, i] for i in range(len(windows))],
                           positions=x_pos + width/2, widths=width,
                           patch_artist=True, showfliers=False,
                           medianprops=dict(color='dimgray', linewidth=2),
                           whiskerprops=dict(color='gray'),
                           capprops=dict(color='gray'))

for box in bp_target['boxes']:
    box.set_facecolor('#FFCDD2')
    box.set_edgecolor('red')
for box in bp_nontarget['boxes']:
    box.set_facecolor('#E0E0E0')
    box.set_edgecolor('gray')

# Overlay individual points with jitter
for i in range(len(windows)):
    jitter_t = np.random.randn(n_trials) * 0.06
    jitter_nt = np.random.randn(n_trials) * 0.06
    ax2.scatter(x_pos[i] - width/2 + jitter_t, features_target[:, i],
               c='red', alpha=0.3, s=12, zorder=5)
    ax2.scatter(x_pos[i] + width/2 + jitter_nt, features_nontarget[:, i],
               c='gray', alpha=0.3, s=12, zorder=5)

ax2.set_xticks(x_pos)
ax2.set_xticklabels(window_labels)
ax2.set_ylabel('Window Mean Amplitude (uV)')
ax2.set_title('Feature by Time Window: Target vs Non-target')
ax2.legend([bp_target['boxes'][0], bp_nontarget['boxes'][0]],
           ['Target', 'Non-target'], fontsize=9)
ax2.axhline(0, color='k', linestyle='-', alpha=0.3)
ax2.grid(True, alpha=0.3, axis='y')

# Annotate the discriminative P3b window
ax2.annotate('Best\ndiscriminator',
            xy=(x_pos[p3b_idx], features_target[:, p3b_idx].max()),
            xytext=(x_pos[p3b_idx] + 0.8, features_target[:, p3b_idx].max() + 1.0),
            fontsize=8, color='red', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='red', lw=1.5))

# 4c: Stepwise LDA classification
ax3 = axes[1, 0]

# Simulate classification accuracy with different number of channels
n_channels = [1, 3, 5, 8, 12, 16]
acc_single = [72, 80, 85, 88, 90, 91]
acc_averaged = [78, 86, 91, 94, 96, 97]

ax3.plot(n_channels, acc_single, 'o-', color='blue', linewidth=2, label='Single-trial')
ax3.plot(n_channels, acc_averaged, 's-', color='red', linewidth=2, label='Averaged (10 reps)')
ax3.axhline(100/6, color='gray', linestyle='--', alpha=0.5, label='Chance (1/6)')
ax3.set_xlabel('Number of Channels')
ax3.set_ylabel('Accuracy (%)')
ax3.set_title('P300 Classification Accuracy')
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.set_ylim(0, 100)

# 4d: ROC curve
ax4 = axes[1, 1]

# Simulate ROC curves
fpr = np.linspace(0, 1, 100)
# Different classifiers
tpr_lda = 1 - (1 - fpr**0.5) * 0.85  # LDA
tpr_svm = 1 - (1 - fpr**0.5) * 0.88  # SVM
tpr_xgb = 1 - (1 - fpr**0.5) * 0.82  # XGBoost

ax4.plot(fpr, tpr_lda, 'b-', linewidth=2, label=f'LDA (AUC=0.92)')
ax4.plot(fpr, tpr_svm, 'r-', linewidth=2, label=f'SVM (AUC=0.95)')
ax4.plot(fpr, tpr_xgb, 'g--', linewidth=2, label=f'XGBoost (AUC=0.89)')
ax4.plot([0, 1], [0, 1], 'k--', alpha=0.5, label='Chance')
ax4.set_xlabel('False Positive Rate')
ax4.set_ylabel('True Positive Rate')
ax4.set_title('ROC Curve: P300 Detection')
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.3)

plt.tight_layout()
path = out_dir / 'day14_plot_4.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 4 saved: {path}')

# =============================================================================
# Figure 5: P300 vs Other BCI Paradigms Comparison
# =============================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('BCI Paradigms Comparison', fontsize=14, fontweight='bold')

# 5a: Multi-dimensional comparison (radar chart style → bar chart)
ax1 = axes[0]

paradigms = ['P300\nSpeller', 'SSVEP', 'Motor\nImagery', 'SCP']
metrics = ['Accuracy', 'ITR', 'Training\nTime', 'Comfort']
# Scores (1-10)
scores = {
    'P300\nSpeller': [9, 6, 9, 5],  # high accuracy, moderate ITR, minimal training, moderate comfort
    'SSVEP':        [9, 9, 9, 3],  # high accuracy, highest ITR, no training, visual fatigue
    'Motor\nImagery': [7, 4, 3, 8],  # moderate accuracy, low ITR, long training, comfortable
    'SCP':          [6, 2, 4, 7],  # lower accuracy, lowest ITR, some training, comfortable
}

x = np.arange(len(metrics))
width = 0.2
colors = ['#E53935', '#1E88E5', '#43A047', '#FB8C00']

for i, (paradigm, sc) in enumerate(scores.items()):
    ax1.bar(x + i*width, sc, width, label=paradigm, color=colors[i], alpha=0.8)

ax1.set_xticks(x + width * 1.5)
ax1.set_xticklabels(metrics)
ax1.set_ylabel('Score (1-10)')
ax1.set_title('Paradigm Comparison')
ax1.legend(fontsize=8, loc='upper right')
ax1.set_ylim(0, 11)
ax1.grid(True, alpha=0.3, axis='y')

# 5b: ITR and Accuracy scatter
ax2 = axes[1]

data = {
    'P300 Speller':  (90, 25, '#E53935', 200),
    'SSVEP (CCA)':   (92, 50, '#1E88E5', 200),
    'SSVEP (FBCCA)': (95, 60, '#1565C0', 200),
    'MI (CSP+LDA)':  (80, 15, '#43A047', 200),
    'MI (FBCSP)':    (85, 20, '#2E7D32', 200),
    'MI (EEGNet)':   (88, 22, '#66BB6A', 150),
    'SCP':           (75, 8,  '#FB8C00', 150),
}

for name, (acc, itr, color, size) in data.items():
    ax2.scatter(itr, acc, s=size, c=color, alpha=0.8, edgecolors='black', zorder=5)
    ax2.annotate(name, (itr, acc), textcoords="offset points", xytext=(8, 5),
                fontsize=8, color=color)

ax2.set_xlabel('ITR (bits/min)')
ax2.set_ylabel('Accuracy (%)')
ax2.set_title('Accuracy vs ITR by Paradigm')
ax2.grid(True, alpha=0.3)
ax2.set_xlim(0, 70)
ax2.set_ylim(65, 100)

plt.tight_layout()
path = out_dir / 'day14_plot_5.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 5 saved: {path}')

# =============================================================================
# Figure 6: P300 Signal Processing Pipeline Summary
# =============================================================================
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_title('P300 BCI Signal Processing Pipeline', fontsize=14, fontweight='bold')

# Pipeline stages
stages = [
    (2, 8, '1. Data\nAcquisition', 'EEG (8-16 ch)\nfs=250Hz\nPz, Cz, Oz', '#E3F2FD'),
    (5, 8, '2. Pre-\nprocessing', 'Bandpass 0.1-30Hz\nNotch 50Hz\nBaseline correction', '#BBDEFB'),
    (8, 8, '3. Epoch\nExtraction', 'Flash-locked\n-100~600ms\nBaseline: -100~0ms', '#90CAF9'),
    (11, 8, '4. Feature\nExtraction', 'Time-window amp\nPCA (optional)\nDownsampling', '#64B5F6'),
]

for x, y, title, detail, color in stages:
    # Main box
    rect = plt.Rectangle((x-1.2, y-0.8), 2.4, 1.6,
                         facecolor=color, edgecolor='#1976D2', linewidth=2, zorder=3)
    ax.add_patch(rect)
    ax.text(x, y+0.2, title, ha='center', va='center', fontsize=10, fontweight='bold')
    # Detail box
    rect2 = plt.Rectangle((x-1.2, y-2.5), 2.4, 1.5,
                          facecolor='white', edgecolor='gray', linewidth=1, zorder=2)
    ax.add_patch(rect2)
    ax.text(x, y-1.75, detail, ha='center', va='center', fontsize=8)
    # Arrow down
    ax.annotate('', xy=(x, y-0.8), xytext=(x, y-1.0),
               arrowprops=dict(arrowstyle='->', color='gray', lw=1))

# Arrows between stages
for i in range(len(stages)-1):
    x1 = stages[i][0] + 1.2
    x2 = stages[i+1][0] - 1.2
    ax.annotate('', xy=(x2, stages[i][1]), xytext=(x1, stages[i][1]),
               arrowprops=dict(arrowstyle='->', color='#1976D2', lw=2))

# Classification stage (second row)
class_stages = [
    (3, 4, '5. Classification', 'Stepwise LDA\nSVM\nBayesian', '#E8F5E9'),
    (7, 4, '6. Decision', 'Accumulate scores\nacross repetitions\nMax score = target', '#FFF3E0'),
    (11, 4, '7. Output', 'Character selected\nFeedback to user\nNext char starts', '#F3E5F5'),
]

for x, y, title, detail, color in class_stages:
    rect = plt.Rectangle((x-1.2, y-0.8), 2.4, 1.6,
                         facecolor=color, edgecolor='#333', linewidth=2, zorder=3)
    ax.add_patch(rect)
    ax.text(x, y+0.2, title, ha='center', va='center', fontsize=10, fontweight='bold')
    # Detail
    rect2 = plt.Rectangle((x-1.2, y-2.5), 2.4, 1.5,
                          facecolor='white', edgecolor='gray', linewidth=1, zorder=2)
    ax.add_patch(rect2)
    ax.text(x, y-1.75, detail, ha='center', va='center', fontsize=8)
    ax.annotate('', xy=(x, y-0.8), xytext=(x, y-1.0),
               arrowprops=dict(arrowstyle='->', color='gray', lw=1))

# Arrows
ax.annotate('', xy=(3-1.2, 4), xytext=(8+1.2, 5.5),
           arrowprops=dict(arrowstyle='->', color='green', lw=2))
for i in range(len(class_stages)-1):
    x1 = class_stages[i][0] + 1.2
    x2 = class_stages[i+1][0] - 1.2
    ax.annotate('', xy=(x2, class_stages[i][1]), xytext=(x1, class_stages[i][1]),
               arrowprops=dict(arrowstyle='->', color='#333', lw=2))

# Key insight box
insight_box = plt.Rectangle((1, 0.3), 12, 1.5,
                            facecolor='#FFF9C4', edgecolor='#F9A825', linewidth=2)
ax.add_patch(insight_box)
ax.text(7, 1.05,
        'Key Insight: P300 detection relies on signal averaging to boost SNR.\n'
        'More repetitions → higher accuracy but lower ITR. Trade-off: accuracy vs speed.',
        ha='center', va='center', fontsize=10, fontweight='bold')

plt.tight_layout()
path = out_dir / 'day14_plot_6.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 6 saved: {path}')

print('\n' + '='*60)
print('Day 14 Complete! Generated 6 figures.')
print('='*60)
