"""
Day 11: BCI System Architecture
================================

Week 5 Day 1: BCI System Architecture, Signal Acquisition, Protocols

Goals:
1. Understand the complete BCI workflow
2. Master EEG signal characteristics
3. Learn different BCI paradigms
4. Calculate ITR (Information Transfer Rate)
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

out_dir = Path(__file__).parent
out_dir.mkdir(exist_ok=True)

# =============================================================================
# Figure 1: BCI System Architecture Flowchart
# =============================================================================
fig, ax = plt.subplots(figsize=(14, 5))
ax.set_xlim(0, 14)
ax.set_ylim(0, 6)
ax.axis('off')
ax.set_title('BCI System Architecture', fontsize=16, fontweight='bold', pad=20)

# Stage boxes
stages = [
    (1.5, 'Neural\nActivity', '#E3F2FD'),
    (4.5, 'Signal\nAcquisition', '#BBDEFB'),
    (7.5, 'Preprocessing', '#90CAF9'),
    (10.5, 'Feature\nExtraction', '#64B5F6'),
    (13.5, 'Classification', '#42A5F5'),
]

for x, text, color in stages:
    rect = plt.Rectangle((x-1.2, 2.5), 2.4, 1.8, 
                         facecolor=color, edgecolor='#1976D2', linewidth=2, zorder=3)
    ax.add_patch(rect)
    ax.text(x, 3.4, text, ha='center', va='center', fontsize=11, fontweight='bold')
    # Arrow
    if x < 13.5:
        ax.annotate('', xy=(x+1.3, 3.4), xytext=(x+1.2, 3.4),
                   arrowprops=dict(arrowstyle='->', color='#1976D2', lw=2))

# Bottom details
details = [
    (1.5, 'Imagined\nLeft/Right', '#FFF3E0'),
    (4.5, 'EEG/MEG\n250-1000Hz', '#E3F2FD'),
    (7.5, 'Filter/Reref\nArtifact', '#E8F5E9'),
    (10.5, 'PSD/ERP\nTopomap', '#F3E5F5'),
    (13.5, 'Prosthetic\nSpeller', '#E0F7FA'),
]

for x, text, color in details:
    ax.text(x, 1.5, text, ha='center', va='center', fontsize=9,
           bbox=dict(boxstyle='round', facecolor=color, edgecolor='gray', alpha=0.8))
    ax.plot([x, x], [2.5, 2.2], 'k--', alpha=0.3, linewidth=1)

# Arrows down from stages to details
for x, _, _ in stages:
    ax.annotate('', xy=(x, 2.3), xytext=(x, 2.5),
               arrowprops=dict(arrowstyle='->', color='gray', lw=1, ls='--'))

plt.tight_layout()
path = out_dir / 'day11_plot_1.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 1 saved: {path}')

# =============================================================================
# Figure 2: BCI Paradigm Signal Characteristics
# =============================================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('BCI Paradigm Signal Characteristics', fontsize=16, fontweight='bold')

fs = 250
t = np.arange(0, 2, 1/fs)

# 2a: SSVEP
ax1 = axes[0, 0]
ssvep_freq = 12
ssvep = np.sin(2 * np.pi * ssvep_freq * t) * 0.5
ssvep += np.sin(2 * np.pi * ssvep_freq * 2 * t) * 0.2
ssvep += np.random.normal(0, 0.1, len(t))
ax1.plot(t, ssvep, 'b-', linewidth=0.8)
ax1.set_title('SSVEP (12 Hz Visual Stimulus)')
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Amplitude (uV)')
ax1.set_xlim(0, 0.5)
ax1.text(0.55, 0.5, '~12 Hz periodic\nresponse', transform=ax1.transAxes, fontsize=9)

# 2b: Motor Imagery (ERD/ERS)
ax2 = axes[0, 1]
t_event = np.arange(-1, 3, 1/fs)
mu_power = np.exp(-(t_event + 0.5)**2 / 0.5) * 0.8
baseline = np.ones_like(t_event) * 0.3

ax2.fill_between(t_event, baseline, baseline - mu_power * baseline, 
                 alpha=0.5, color='red', label='ERD (mu suppression)')
ax2.fill_between(t_event, baseline, baseline + 0.1 * baseline, 
                 alpha=0.5, color='green', label='ERS (beta rebound)')
ax2.axhline(y=baseline[0], color='k', linestyle='--', alpha=0.5)
ax2.axvline(x=0, color='r', linestyle='-', alpha=0.5, label='Movement onset')
ax2.set_title('Motor Imagery (MI) - ERD/ERS')
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('Relative Power Change (%)')
ax2.legend(fontsize=8)
ax2.set_xlim(-1, 3)

# 2c: P300
ax3 = axes[1, 0]
t_p3 = np.arange(-0.2, 0.8, 1/fs)
p300 = np.exp(-(t_p3 - 0.3)**2 / 0.02) * 5
n200 = -np.exp(-(t_p3 - 0.2)**2 / 0.01) * 2
erp = n200 + p300 + np.sin(2 * np.pi * 10 * t_p3) * 0.3

ax3.plot(t_p3 * 1000, erp, 'b-', linewidth=1.5)
ax3.axhline(y=0, color='k', linestyle='--', alpha=0.5)
ax3.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
ax3.axvline(x=300, color='r', linestyle='-', alpha=0.7, label='P300 peak ~300ms')
ax3.fill_between(t_p3 * 1000, 0, erp, where=(erp > 0), alpha=0.3, color='blue')
ax3.set_title('P300 Event-Related Potential')
ax3.set_xlabel('Time (ms)')
ax3.set_ylabel('Amplitude (uV)')
ax3.legend(fontsize=8)
ax3.set_xlim(-200, 800)

# 2d: SCP
ax4 = axes[1, 1]
t_scp = np.arange(0, 10, 1/fs)
scp = np.cumsum(np.random.randn(len(t_scp))) * 0.5
scp = np.convolve(scp, np.ones(250)/250, mode='same')
scp[int(2*fs):int(5*fs)] -= 10
scp[int(7*fs):int(9*fs)] += 8

ax4.plot(t_scp, scp, 'b-', linewidth=1)
ax4.axhline(y=0, color='k', linestyle='--', alpha=0.5)
ax4.fill_between(t_scp, 0, scp, where=(scp < 0), alpha=0.3, color='red', label='Negative SCP')
ax4.fill_between(t_scp, 0, scp, where=(scp > 0), alpha=0.3, color='green', label='Positive SCP')
ax4.set_title('SCP (Slow Cortical Potential)')
ax4.set_xlabel('Time (s)')
ax4.set_ylabel('Amplitude (uV)')
ax4.legend(fontsize=8)

plt.tight_layout()
path = out_dir / 'day11_plot_2.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 2 saved: {path}')

# =============================================================================
# Figure 3: EEG Frequency Bands
# =============================================================================
fig, ax = plt.subplots(figsize=(14, 6))

bands = [
    ('Delta', 0.5, 4, '#FF5722', 'Deep sleep'),
    ('Theta', 4, 8, '#2196F3', 'Drowsiness, memory'),
    ('Alpha', 8, 13, '#4CAF50', 'Relaxation, eyes closed'),
    ('Mu', 8, 13, '#9C27B0', 'Sensorimotor cortex'),
    ('Beta', 13, 30, '#FF9800', 'Alertness, active thinking'),
    ('Gamma', 30, 100, '#F44336', 'High-order cognition'),
]

for i, (name, f_low, f_high, color, desc) in enumerate(bands):
    width = f_high - f_low
    ax.barh(i, width, left=f_low, height=0.6, color=color, alpha=0.7, edgecolor='black')
    ax.text((f_low + f_high)/2, i, name, 
            ha='center', va='center', fontsize=11, fontweight='bold', color='white')
    ax.text(f_high + 2, i, f'{f_low}-{f_high} Hz: {desc}', 
            ha='left', va='center', fontsize=10)

ax.set_yticks([])
ax.set_xlabel('Frequency (Hz)', fontsize=12)
ax.set_title('EEG Frequency Bands and Their Functions', fontsize=14, fontweight='bold')
ax.set_xlim(0, 110)
ax.set_ylim(-0.5, len(bands) - 0.5)

for f in [4, 8, 13, 30]:
    ax.axvline(x=f, color='gray', linestyle='--', alpha=0.5)

plt.tight_layout()
path = out_dir / 'day11_plot_3.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 3 saved: {path}')

# =============================================================================
# Figure 4: ITR Calculation
# =============================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 4a: ITR vs Accuracy
ax1 = axes[0]
T = 2
N_values = [2, 4, 8, 10]
P = np.linspace(0.5, 1, 50)

for N in N_values:
    with np.errstate(divide='ignore', invalid='ignore'):
        itrs = (60 / T) * (
            np.log2(N) + 
            P * np.log2(P) + 
            (1 - P) * np.log2((1 - P) / (N - 1))
        )
        itrs = np.nan_to_num(itrs, nan=0)
    ax1.plot(P * 100, itrs, label=f'N={N}', linewidth=2)

ax1.set_xlabel('Accuracy (%)', fontsize=12)
ax1.set_ylabel('ITR (bits/min)', fontsize=12)
ax1.set_title(f'ITR vs Accuracy (T={T}s)', fontsize=12)
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_xlim(50, 100)

# 4b: ITR vs Selection Time
ax2 = axes[1]
N = 4
P_values = [0.7, 0.8, 0.9, 1.0]
T_range = np.linspace(0.5, 10, 50)

for P_val in P_values:
    with np.errstate(divide='ignore', invalid='ignore'):
        itrs = (60 / T_range) * (
            np.log2(N) + 
            P_val * np.log2(P_val) + 
            (1 - P_val) * np.log2((1 - P_val) / (N - 1))
        )
        itrs = np.nan_to_num(itrs, nan=0)
    ax2.plot(T_range, itrs, label=f'P={P_val*100:.0f}%', linewidth=2)

ax2.set_xlabel('Selection Time T (s)', fontsize=12)
ax2.set_ylabel('ITR (bits/min)', fontsize=12)
ax2.set_title(f'ITR vs Selection Time (N={N})', fontsize=12)
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_xlim(0.5, 10)

plt.tight_layout()
path = out_dir / 'day11_plot_4.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 4 saved: {path}')

# =============================================================================
# Figure 5: 10-20 Electrode System
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 8))
ax.set_aspect('equal')
ax.axis('off')
ax.set_title('10-20 International Electrode System', fontsize=14, fontweight='bold')

# Head outline
theta = np.linspace(0, 2*np.pi, 100)
head_x = np.cos(theta)
head_y = np.sin(theta)
ax.plot(head_x, head_y, 'k-', linewidth=2)
ax.plot([-1.05, 1.05], [0, 0], 'k-', linewidth=1.5)  # Line through ears
ax.plot([0, 0], [-1.05, 1.05], 'k-', linewidth=1.5)  # Line through nose

# Electrode positions
electrodes = {
    'Fp1': (-0.45, 0.75), 'Fpz': (0, 0.85), 'Fp2': (0.45, 0.75),
    'F7': (-0.82, 0.4), 'F3': (-0.48, 0.42), 'Fz': (0, 0.52), 
    'F4': (0.48, 0.42), 'F8': (0.82, 0.4),
    'T3': (-0.95, 0), 'C3': (-0.48, 0), 'Cz': (0, 0.08), 
    'C4': (0.48, 0), 'T4': (0.95, 0),
    'T5': (-0.82, -0.42), 'P3': (-0.48, -0.42), 'Pz': (0, -0.52), 
    'P4': (0.48, -0.42), 'T6': (0.82, -0.42),
    'O1': (-0.45, -0.75), 'Oz': (0, -0.85), 'O2': (0.45, -0.75),
}

for name, (x, y) in electrodes.items():
    circle = plt.Circle((x, y), 0.035, color='#2196F3', zorder=5)
    ax.add_patch(circle)
    offset_y = 0.08 if y > 0 else -0.08
    ax.text(x, y + offset_y, name, ha='center', va='center', fontsize=8)

# Nose indicator
ax.annotate('Nose', xy=(0, 1.08), fontsize=10, ha='center', fontweight='bold')

# Region labels
ax.text(-0.7, 0.25, 'Frontal', ha='center', va='center', fontsize=9, color='gray', style='italic')
ax.text(-0.7, -0.25, 'Temporal', ha='center', va='center', fontsize=9, color='gray', style='italic')
ax.text(0, 0.3, 'Central', ha='center', va='center', fontsize=9, color='gray', style='italic')
ax.text(0, -0.3, 'Parietal', ha='center', va='center', fontsize=9, color='gray', style='italic')
ax.text(0, -0.7, 'Occipital', ha='center', va='center', fontsize=9, color='gray', style='italic')

plt.tight_layout()
path = out_dir / 'day11_plot_5.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 5 saved: {path}')

# =============================================================================
# Figure 6: Real-time BCI Pipeline
# =============================================================================
fig, ax = plt.subplots(figsize=(14, 6))
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.axis('off')
ax.set_title('Real-time BCI Processing Pipeline', fontsize=14, fontweight='bold')

# Timeline
t_start = 1
total_time = 11
ax.annotate('', xy=(t_start + total_time, 0.5), xytext=(t_start, 0.5),
           arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(t_start + total_time/2, 0.2, 'Time', ha='center', fontsize=10)

# Sliding windows
window_duration = 2
window_step = 0.8
for i in range(5):
    w_start = t_start + i * window_step
    w_end = w_start + window_duration
    color = '#E3F2FD' if i % 2 == 0 else '#BBDEFB'
    rect = plt.Rectangle((w_start, 1.2), w_end - w_start, 2.5, 
                         facecolor=color, edgecolor='#1976D2', linewidth=1, alpha=0.8)
    ax.add_patch(rect)
    ax.text((w_start + w_end)/2, 2.45, f'Win {i+1}', ha='center', va='center', fontsize=9)

ax.text(t_start - 0.3, 2.45, 'Sliding\nWindow', ha='right', va='center', fontsize=9)
ax.text(t_start + 2.4, 3.9, 'Window Size = 2s', ha='center', fontsize=9)

# Processing stages
stages = [
    (2.5, 5.5, 'Preprocessing\nFilter/Reref', '#E8F5E9'),
    (5.5, 5.5, 'Feature\nExtraction', '#FFF3E0'),
    (8.5, 5.5, 'Classification\nLDA/SVM', '#F3E5F5'),
    (11.5, 5.5, 'Output\nControl', '#E0F7FA'),
]

for x, y, text, color in stages:
    rect = plt.Rectangle((x-1.2, y-0.8), 2.4, 1.6, 
                         facecolor=color, edgecolor='#333', linewidth=2)
    ax.add_patch(rect)
    ax.text(x, y, text, ha='center', va='center', fontsize=10, fontweight='bold')

# Arrows between stages
for i, (x, _, _, _) in enumerate(stages[:-1]):
    ax.annotate('', xy=(stages[i+1][0]-1.2, stages[i+1][1]), 
               xytext=(x+1.2, stages[i][1]),
               arrowprops=dict(arrowstyle='->', color='green', lw=2))

# Arrows from windows to stages
for i in range(4):
    ax.annotate('', xy=(stages[i][0], 4.7), xytext=(stages[i][0], 3.7),
               arrowprops=dict(arrowstyle='->', color='gray', lw=1))

# Latency note
ax.text(7, 7.2, 'Total Latency < 300ms', ha='center', 
        fontsize=12, fontweight='bold', color='red',
        bbox=dict(boxstyle='round', facecolor='#FFEBEE', edgecolor='red'))

plt.tight_layout()
path = out_dir / 'day11_plot_6.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 6 saved: {path}')

print('\n' + '='*60)
print('Day 11 Complete! Generated 6 figures.')
print('='*60)
