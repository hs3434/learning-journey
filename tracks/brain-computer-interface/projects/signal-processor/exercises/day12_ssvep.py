"""
Day 12: SSVEP - Steady-State Visual Evoked Potential
======================================================

Week 5 Day 2: SSVEP principles, frequency domain analysis, CCA/FBCCA

Goals:
1. Understand SSVEP signal generation mechanism
2. Learn CCA (Canonical Correlation Analysis) for SSVEP detection
3. Implement FBCCA (Filter Bank CCA) for improved performance
4. Calculate SSVEP detection accuracy
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import signal

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

out_dir = Path(__file__).parent
out_dir.mkdir(exist_ok=True)

# =============================================================================
# Figure 1: SSVEP Signal Generation Mechanism
# =============================================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('SSVEP Signal Generation Mechanism', fontsize=16, fontweight='bold')

fs = 250  # Sampling rate
t = np.arange(0, 3, 1/fs)

# 1a: Visual stimulus (flickering LED)
ax1 = axes[0, 0]
freq_stim = 12  # Hz - stimulation frequency
stimulus = np.sin(2 * np.pi * freq_stim * t) > 0  # Square wave
ax1.fill_between(t, 0, stimulus.astype(float), alpha=0.7, color='yellow')
ax1.set_title(f'Visual Stimulus ({freq_stim} Hz flickering)')
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Stimulus ON/OFF')
ax1.set_xlim(0, 0.5)
ax1.set_ylim(-0.1, 1.1)

# 1b: EEG response (simulated SSVEP)
ax2 = axes[0, 1]
# Primary response at stimulation frequency
eeg = np.sin(2 * np.pi * freq_stim * t) * 0.5
# Second harmonic
eeg += np.sin(2 * np.pi * freq_stim * 2 * t) * 0.25
# Third harmonic
eeg += np.sin(2 * np.pi * freq_stim * 3 * t) * 0.1
# Add noise
eeg += np.random.randn(len(t)) * 0.1

ax2.plot(t, eeg, 'b-', linewidth=0.8)
ax2.set_title(f'SSVEP EEG Response (with harmonics)')
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('Amplitude (uV)')
ax2.set_xlim(0, 0.5)

# 1c: Frequency spectrum
ax3 = axes[1, 0]
freqs, psd = signal.welch(eeg, fs, nperseg=512)
ax3.semilogy(freqs, psd, 'b-', linewidth=1)
ax3.axvline(x=freq_stim, color='r', linestyle='--', label=f'{freq_stim} Hz (fundamental)')
ax3.axvline(x=freq_stim*2, color='orange', linestyle='--', label=f'{freq_stim*2} Hz (2nd harmonic)')
ax3.axvline(x=freq_stim*3, color='green', linestyle='--', label=f'{freq_stim*3} Hz (3rd harmonic)')
ax3.set_title('Power Spectral Density')
ax3.set_xlabel('Frequency (Hz)')
ax3.set_ylabel('Power (log scale)')
ax3.set_xlim(0, 60)
ax3.legend(fontsize=8)
ax3.grid(True, alpha=0.3)

# 1d: Harmonic amplitudes
ax4 = axes[1, 1]
harmonics = [1, 2, 3, 4]
amplitudes = [0.5, 0.25, 0.1, 0.05]
colors = ['red', 'orange', 'green', 'purple']
bars = ax4.bar(harmonics, amplitudes, color=colors, alpha=0.7, edgecolor='black')
ax4.set_title('Harmonic Amplitude Distribution')
ax4.set_xlabel('Harmonic Number')
ax4.set_ylabel('Relative Amplitude')
ax4.set_xticks(harmonics)
for bar, amp in zip(bars, amplitudes):
    ax4.text(bar.get_x() + bar.get_width()/2, amp + 0.02, f'{amp:.2f}', 
             ha='center', fontsize=9)

plt.tight_layout()
path = out_dir / 'day12_plot_1.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 1 saved: {path}')

# =============================================================================
# Figure 2: CCA (Canonical Correlation Analysis) Principle
# =============================================================================
fig, ax = plt.subplots(figsize=(14, 6))
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.axis('off')
ax.set_title('CCA-based SSVEP Detection', fontsize=14, fontweight='bold')

# EEG signal box
rect = plt.Rectangle((1, 4), 3, 2.5, facecolor='#E3F2FD', edgecolor='#1976D2', linewidth=2)
ax.add_patch(rect)
ax.text(2.5, 5.25, 'EEG Signal X\n(Channels x Time)', ha='center', va='center', fontsize=10)

# Reference signals (Y)
for i, freq in enumerate([10, 12, 15]):
    rect = plt.Rectangle((10, 1.5 + i*1.2), 2.5, 0.8, 
                         facecolor='#FFF3E0', edgecolor='#FF9800', linewidth=2)
    ax.add_patch(rect)
    ax.text(11.25, 1.9 + i*1.2, f'{freq} Hz ref', ha='center', va='center', fontsize=9)

# Correlation computation
ax.text(7, 5.5, 'CCA\nCorrelation\nAnalysis', ha='center', va='center', fontsize=10,
       bbox=dict(boxstyle='round', facecolor='#E8F5E9', edgecolor='#4CAF50'))

# Arrows
ax.annotate('', xy=(6, 5.25), xytext=(4.1, 5.25),
           arrowprops=dict(arrowstyle='->', color='#1976D2', lw=2))
for i in range(3):
    ax.annotate('', xy=(8.9, 1.9 + i*1.2), xytext=(8, 5.5),
               arrowprops=dict(arrowstyle='->', color='#FF9800', lw=1.5, ls='--'))

# Result
rect = plt.Rectangle((11, 4), 2.5, 2.5, facecolor='#F3E5F5', edgecolor='#9C27B0', linewidth=2)
ax.add_patch(rect)
ax.text(12.25, 5.25, 'Correlation\nCoefficients\n\nMax = Target', ha='center', va='center', fontsize=9)

ax.annotate('', xy=(11, 5.25), xytext=(8, 5.25),
           arrowprops=dict(arrowstyle='->', color='#9C27B0', lw=2))

# Mathematical formula
ax.text(7, 1.5, 
        'CCA finds W_x, W_y to maximize:\n'
        r'$\rho = \frac{w_x^T X Y^T w_y}{\sqrt{w_x^T X X^T w_x \cdot w_y^T Y Y^T w_y}}$',
        ha='center', va='center', fontsize=10,
        bbox=dict(boxstyle='round', facecolor='white', edgecolor='gray'))

plt.tight_layout()
path = out_dir / 'day12_plot_2.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 2 saved: {path}')

# =============================================================================
# Figure 3: Filter Bank CCA (FBCCA)
# =============================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Filter Bank CCA (FBCCA)', fontsize=14, fontweight='bold')

# 3a: Filter bank concept
ax1 = axes[0]
# Define frequency bands for each sub-band
sub_bands = [
    ('SB1', 6, 15, '#FF5722'),
    ('SB2', 15, 30, '#2196F3'),
    ('SB3', 30, 45, '#4CAF50'),
    ('SB4', 45, 60, '#9C27B0'),
    ('SB5', 60, 90, '#FF9800'),
]

for name, f_low, f_high, color in sub_bands:
    ax1.barh(name, f_high - f_low, left=f_low, height=0.6, 
            color=color, alpha=0.7, edgecolor='black')
    ax1.text((f_low + f_high)/2, name, f'{f_low}-{f_high} Hz', 
             ha='center', va='center', fontsize=9, color='white', fontweight='bold')

ax1.set_xlabel('Frequency (Hz)')
ax1.set_title('Sub-band Decomposition')
ax1.set_xlim(0, 100)

# 3b: FBCCA processing flow
ax2 = axes[1]
ax2.set_xlim(0, 12)
ax2.set_ylim(0, 6)
ax2.axis('off')

# Input EEG
rect = plt.Rectangle((0.5, 3.5), 2, 1.5, facecolor='#E3F2FD', edgecolor='#1976D2', linewidth=2)
ax2.add_patch(rect)
ax2.text(1.5, 4.25, 'Raw EEG', ha='center', va='center', fontsize=10)

# Filter bank
for i, (name, f_low, f_high, _) in enumerate(sub_bands):
    y = 2.5 - i * 0.45
    rect = plt.Rectangle((3.5, y), 1.8, 0.35, 
                         facecolor='#FFF3E0', edgecolor='#FF9800', linewidth=1)
    ax2.add_patch(rect)
    ax2.text(4.4, y + 0.175, f'BP {f_low}-{f_high}', ha='center', va='center', fontsize=7)

ax2.text(4.4, 3.3, 'Filter\nBank', ha='center', va='center', fontsize=8)

# CCA for each sub-band
for i in range(len(sub_bands)):
    y = 2.5 - i * 0.45
    rect = plt.Rectangle((6, y), 1.5, 0.35, 
                         facecolor='#E8F5E9', edgecolor='#4CAF50', linewidth=1)
    ax2.add_patch(rect)
    ax2.text(6.75, y + 0.175, 'CCA', ha='center', va='center', fontsize=7)

ax2.text(6.75, 3.3, 'CCA\n(k times)', ha='center', va='center', fontsize=8)

# Correlation + weighting
rect = plt.Rectangle((8.2, 2.5), 1.8, 2, facecolor='#F3E5F5', edgecolor='#9C27B0', linewidth=2)
ax2.add_patch(rect)
ax2.text(9.1, 3.8, 'rho_1', ha='center', va='center', fontsize=8)
ax2.text(9.1, 3.4, 'rho_2', ha='center', va='center', fontsize=8)
ax2.text(9.1, 3.0, '...', ha='center', va='center', fontsize=8)
ax2.text(9.1, 2.7, 'rho_k', ha='center', va='center', fontsize=8)

# Weighted sum
rect = plt.Rectangle((10.5, 2.8), 1.2, 1.4, facecolor='#E0F7FA', edgecolor='#00BCD4', linewidth=2)
ax2.add_patch(rect)
ax2.text(11.1, 3.5, 'Weighted\nSum', ha='center', va='center', fontsize=9)

# Arrows
ax2.annotate('', xy=(3.5, 4.25), xytext=(2.5, 4.25),
            arrowprops=dict(arrowstyle='->', color='#1976D2', lw=2))
for i in range(len(sub_bands)):
    y = 2.5 - i * 0.45 + 0.175
    ax2.annotate('', xy=(6, y), xytext=(5.3, 4.25),
                arrowprops=dict(arrowstyle='->', color='#FF9800', lw=1))
ax2.annotate('', xy=(8.2, 3.5), xytext=(7.5, 3.5),
            arrowprops=dict(arrowstyle='->', color='#4CAF50', lw=1.5))
ax2.annotate('', xy=(10.5, 3.5), xytext=(10, 3.5),
            arrowprops=dict(arrowstyle='->', color='#9C27B0', lw=2))

plt.tight_layout()
path = out_dir / 'day12_plot_3.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 3 saved: {path}')

# =============================================================================
# Figure 4: CCA Implementation
# =============================================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('CCA Implementation for SSVEP', fontsize=16, fontweight='bold')

# Generate sample EEG data
np.random.seed(42)
fs = 250
t = np.arange(0, 3, 1/fs)
n_channels = 8
n_samples = len(t)

# Simulate EEG with SSVEP component at 12 Hz
eeg = np.zeros((n_channels, n_samples))
for i in range(n_channels):
    # SSVEP at 12 Hz
    eeg[i] += np.sin(2 * np.pi * 12 * t + i * 0.1) * 0.5
    # Noise
    eeg[i] += np.random.randn(n_samples) * 0.3

# 4a: Original EEG (one channel)
ax1 = axes[0, 0]
ax1.plot(t, eeg[0], 'b-', linewidth=0.5)
ax1.set_title('Simulated EEG with SSVEP (12 Hz)')
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Amplitude (uV)')
ax1.set_xlim(0, 1)

# 4b: Reference signals
ax2 = axes[0, 1]
target_freqs = [10, 12, 15, 8]
colors = ['red', 'blue', 'green', 'orange']
for freq, color in zip(target_freqs, colors):
    ref = np.sin(2 * np.pi * freq * t)
    ax2.plot(t, ref, color=color, linewidth=0.8, label=f'{freq} Hz')
ax2.set_title('Reference Signals (Sine/Cosine pairs)')
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('Amplitude')
ax2.set_xlim(0, 0.5)
ax2.legend()
ax2.grid(True, alpha=0.3)

# 4c: CCA correlation for each frequency
ax3 = axes[1, 0]
def compute_cca(X, Y):
    """Simple CCA implementation"""
    # X: (n_channels, n_samples), Y: (n_harmonics*2, n_samples)
    # Compute canonical correlation
    n_samples = X.shape[1]
    
    # Center the data
    X_centered = X - X.mean(axis=1, keepdims=True)
    Y_centered = Y - Y.mean(axis=1, keepdims=True)
    
    # Compute covariance matrices
    C_xx = np.dot(X_centered, X_centered.T) / (n_samples - 1)
    C_yy = np.dot(Y_centered, Y_centered.T) / (n_samples - 1)
    C_xy = np.dot(X_centered, Y_centered.T) / (n_samples - 1)
    
    # Solve eigenvalue problem
    try:
        C_xx_inv = np.linalg.inv(C_xx + 1e-6 * np.eye(C_xx.shape[0]))
        T = np.dot(np.dot(C_xx_inv, C_xy), np.linalg.inv(C_yy + 1e-6 * np.eye(C_yy.shape[0])))
        T = np.dot(T, C_xy.T)
        eigenvalues = np.linalg.eigvalsh(T)
        rho = np.sqrt(np.max(eigenvalues))
    except:
        rho = 0
    return rho

# Generate reference signals for CCA
correlations = []
for freq in np.linspace(5, 20, 50):
    Y = np.vstack([
        np.sin(2 * np.pi * freq * t),
        np.cos(2 * np.pi * freq * t),
        np.sin(2 * np.pi * freq * 2 * t),
        np.cos(2 * np.pi * freq * 2 * t),
    ])
    rho = compute_cca(eeg, Y)
    correlations.append(rho)

freqs = np.linspace(5, 20, 50)
ax3.plot(freqs, correlations, 'b-', linewidth=2)
ax3.axvline(x=12, color='r', linestyle='--', label='True freq: 12 Hz')
ax3.set_title('CCA Correlation vs Frequency')
ax3.set_xlabel('Frequency (Hz)')
ax3.set_ylabel('Correlation (rho)')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 4d: Bar chart of correlations at target frequencies
ax4 = axes[1, 1]
target_freqs = [8, 10, 12, 15]
bar_colors = ['orange', 'green', 'red', 'purple']
corr_values = []
for freq in target_freqs:
    Y = np.vstack([
        np.sin(2 * np.pi * freq * t),
        np.cos(2 * np.pi * freq * t),
        np.sin(2 * np.pi * freq * 2 * t),
        np.cos(2 * np.pi * freq * 2 * t),
    ])
    rho = compute_cca(eeg, Y)
    corr_values.append(rho)

bars = ax4.bar(range(len(target_freqs)), corr_values, color=bar_colors, alpha=0.7, edgecolor='black')
ax4.set_xticks(range(len(target_freqs)))
ax4.set_xticklabels([f'{f} Hz' for f in target_freqs])
ax4.set_title('CCA Correlation at Target Frequencies')
ax4.set_ylabel('Correlation (rho)')
ax4.set_ylim(0, 1)

# Highlight the max
max_idx = np.argmax(corr_values)
ax4.bar(max_idx, corr_values[max_idx], color='red', alpha=0.9, edgecolor='black', linewidth=2)

for i, v in enumerate(corr_values):
    ax4.text(i, v + 0.02, f'{v:.3f}', ha='center', fontsize=9)

plt.tight_layout()
path = out_dir / 'day12_plot_4.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 4 saved: {path}')

# =============================================================================
# Figure 5: SSVEP Performance Comparison
# =============================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('SSVEP Detection Performance', fontsize=14, fontweight='bold')

# 5a: Accuracy vs Number of Targets
ax1 = axes[0]
methods = ['CCA', 'FBCCA', 'SSVEP-CNN', 'EEGNet']
n_targets = [4, 8, 12, 20]

# Simulate performance data
np.random.seed(42)
for method, color in zip(methods, ['blue', 'green', 'red', 'purple']):
    if method == 'EEGNet':
        accs = [95, 92, 88, 82]  # Deep learning degrades with more targets
    elif method == 'SSVEP-CNN':
        accs = [96, 94, 91, 87]
    else:
        base = 85 if method == 'CCA' else 92
        accs = [base - i*0.5 + np.random.randn()*2 for i in range(4)]
        accs = np.clip(accs, 60, 100)
    ax1.plot(n_targets, accs, 'o-', color=color, linewidth=2, label=method)

ax1.set_xlabel('Number of Targets')
ax1.set_ylabel('Accuracy (%)')
ax1.set_title('Accuracy vs Number of Targets')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_ylim(60, 100)

# 5b: ITR Comparison
ax2 = axes[1]
# Calculate ITR for each method at 8 targets
T = 2  # selection time
accs_8 = [88, 94, 92, 85]  # accuracy at 8 targets

itr_values = []
for acc in accs_8:
    P = acc / 100
    N = 8
    # ITR formula
    if P > 0 and P < 1:
        itr = (60 / T) * (np.log2(N) + P * np.log2(P) + (1-P) * np.log2((1-P)/(N-1)))
    else:
        itr = (60 / T) * np.log2(N)
    itr_values.append(itr)

bars = ax2.bar(methods, itr_values, color=['blue', 'green', 'red', 'purple'], alpha=0.7, edgecolor='black')
ax2.set_ylabel('ITR (bits/min)')
ax2.set_title(f'ITR Comparison (N=8 targets, T={T}s)')
for bar, itr in zip(bars, itr_values):
    ax2.text(bar.get_x() + bar.get_width()/2, itr + 1, f'{itr:.1f}', 
             ha='center', fontsize=10)

plt.tight_layout()
path = out_dir / 'day12_plot_5.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 5 saved: {path}')

# =============================================================================
# Figure 6: SSVEP Experimental Setup
# =============================================================================
fig, ax = plt.subplots(figsize=(12, 8))
ax.set_aspect('equal')
ax.axis('off')
ax.set_title('SSVEP BCI Experimental Setup', fontsize=14, fontweight='bold')

# User head
head = plt.Circle((0, 0), 0.8, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(head)
ax.text(0, 0, 'User', ha='center', va='center', fontsize=12)

# Screen with flickering targets
screen = plt.Rectangle((1.5, -1), 2, 2, facecolor='#F5F5F5', edgecolor='black', linewidth=2)
ax.add_patch(screen)

# Flickering targets
freqs = [8, 10, 12, 15]
positions = [(-0.6, 0.6), (0.6, 0.6), (-0.6, -0.4), (0.6, -0.4)]
colors = ['red', 'blue', 'green', 'orange']

for (x, y), freq, color in zip(positions, freqs, colors):
    circle = plt.Circle((1.5 + x, y), 0.3, facecolor=color, edgecolor='black', linewidth=1)
    ax.add_patch(circle)
    ax.text(1.5 + x, y, f'{freq}\nHz', ha='center', va='center', fontsize=8, color='white')

ax.text(2.5, 1.2, 'SSVEP Stimulus\nScreen', ha='center', va='center', fontsize=10)

# Arrow: visual stimulus
ax.annotate('', xy=(0.85, 0.2), xytext=(1.5, 0.2),
           arrowprops=dict(arrowstyle='->', color='blue', lw=2))

# EEG cap
cap = plt.Circle((0, 0), 0.75, fill=False, edgecolor='#2196F3', linewidth=2, linestyle='--')
ax.add_patch(cap)

# Cable
ax.plot([0, -1.5], [0.5, 1.5], 'k-', linewidth=2)
ax.text(-1.2, 1.3, 'EEG Cable', fontsize=9)

# Amplifier
amp = plt.Rectangle((-2.5, 1), 1.5, 1, facecolor='#E0E0E0', edgecolor='black', linewidth=2)
ax.add_patch(amp)
ax.text(-1.75, 1.5, 'EEG\nAmplifier', ha='center', va='center', fontsize=8)

# Computer
comp = plt.Rectangle((-3.5, -0.5), 1.5, 2, facecolor='#E3F2FD', edgecolor='black', linewidth=2)
ax.add_patch(comp)
ax.text(-2.75, 0.5, 'Computer\n(Processing)', ha='center', va='center', fontsize=8)

# Arrow: amplifier to computer
ax.annotate('', xy=(-3.5, 0.5), xytext=(-2.5, 1.5),
           arrowprops=dict(arrowstyle='->', color='gray', lw=2))

# Output
ax.annotate('', xy=(1.2, 2), xytext=(0.2, 1.5),
           arrowprops=dict(arrowstyle='->', color='green', lw=2))
ax.text(1.5, 2.3, 'BCI Output\n(Speller/Prosthetic)', ha='center', va='center', fontsize=9)

# Labels
ax.text(-2.5, -1.2, 'Hardware', ha='center', fontsize=11, fontweight='bold',
       bbox=dict(boxstyle='round', facecolor='#FFECB3', edgecolor='#FFC107'))
ax.text(0.5, -2.5, 'Signal Processing & Classification', ha='center', fontsize=11, fontweight='bold',
       bbox=dict(boxstyle='round', facecolor='#E8F5E9', edgecolor='#4CAF50'))

plt.tight_layout()
path = out_dir / 'day12_plot_6.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 6 saved: {path}')

print('\n' + '='*60)
print('Day 12 Complete! Generated 6 figures.')
print('='*60)
