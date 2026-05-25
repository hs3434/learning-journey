"""
Day 15: Deep Learning in BCI — EEGNet vs Traditional Methods
Week 5 Day 5 (BCI Paradigms)

Topics covered:
1. EEG signal as "image" — data representation for CNNs
2. EEGNet architecture — depthwise separable convolution
3. Shallow ConvNet — learnable CSP equivalent
4. Traditional vs Deep Learning comparison
5. Data augmentation techniques for BCI
6. Transfer learning concept visualization
"""

import matplotlib
matplotlib.use('Agg')
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# Configuration
# ============================================================
SAVE_DIR = '/workspace/learning-journey/tracks/brain-computer-interface/projects/signal-processor/exercises/'
N_CHANNELS = 16
N_TIMES = 500
FS = 250

np.random.seed(42)

# ============================================================
# Helper: generate synthetic MI EEG data
# ============================================================
def generate_mi_eeg(n_trials, n_channels=16, n_times=500, fs=250, snr_db=5):
    """Generate synthetic Motor Imagery EEG data (Left vs Right hand)."""
    t = np.arange(n_times) / fs
    X = np.zeros((n_trials, n_channels, n_times))
    y = np.zeros(n_trials, dtype=int)
    
    for i in range(n_trials):
        label = np.random.randint(0, 2)
        y[i] = label
        
        # Base noise (1/f + white)
        noise = np.random.randn(n_channels, n_times) * 2.0
        
        # MI-specific ERD/ERS pattern
        if label == 0:  # Left hand → right hemisphere ERD
            erd_channels = [8, 9, 10]  # C4 area
            ers_channels = [4, 5, 6]   # C3 area (contralateral ERS)
        else:  # Right hand → left hemisphere ERD
            erd_channels = [4, 5, 6]   # C3 area
            ers_channels = [8, 9, 10]  # C4 area
        
        # ERD: mu rhythm (10Hz) amplitude decreases after cue
        mu_base = 0.8 * np.sin(2 * np.pi * 10 * t)
        erd_envelope = 1.0 - 0.6 * np.exp(-((t - 0.5)**2) / 0.2)
        for ch in erd_channels:
            noise[ch] += mu_base * erd_envelope * 2.5
        
        # ERS: beta rhythm (20Hz) amplitude increases (contralateral)
        beta_base = 0.4 * np.sin(2 * np.pi * 20 * t)
        ers_envelope = 0.4 * np.exp(-((t - 0.5)**2) / 0.3)
        for ch in ers_channels:
            noise[ch] += beta_base * ers_envelope * 2.0
        
        # Add some non-informative alpha rhythm to all channels
        for ch in range(n_channels):
            alpha_phase = np.random.uniform(0, 2*np.pi)
            noise[ch] += 0.5 * np.sin(2 * np.pi * 10 * t + alpha_phase)
        
        X[i] = noise
    
    return X, y

# ============================================================
# Generate dataset
# ============================================================
print("Generating synthetic MI EEG dataset...")
X_train, y_train = generate_mi_eeg(200)
X_test, y_test = generate_mi_eeg(80)
print(f"  Train: {X_train.shape}, Test: {X_test.shape}")

# ============================================================
# Plot 1: EEG Data as "Image" — CNN Input Representation
# ============================================================
print("\nPlot 1: EEG as image representation...")

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# Raw EEG traces
ax = axes[0]
trial = X_train[0]
offsets = np.arange(N_CHANNELS) * 8
for ch in range(N_CHANNELS):
    ax.plot(np.arange(N_TIMES) / FS, trial[ch] + offsets[ch], linewidth=0.5, color='steelblue')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Channel (offset)')
ax.set_title('Raw EEG Traces')
ax.set_yticks(offsets[::3])
ax.set_yticklabels([f'Ch{i}' for i in range(0, N_CHANNELS, 3)])

# EEG as 2D "image"
ax = axes[1]
im = ax.imshow(trial, aspect='auto', cmap='RdBu_r', vmin=-5, vmax=5,
               extent=[0, N_TIMES/FS, N_CHANNELS-0.5, -0.5])
ax.set_xlabel('Time (s)')
ax.set_ylabel('Channel #')
ax.set_title('EEG as "Image" (CNN Input)')
plt.colorbar(im, ax=ax, label='Amplitude (μV)', shrink=0.8)

# Channel topography hint (simplified 10-20 layout)
ax = axes[2]
ch_names = [f'Ch{i}' for i in range(N_CHANNELS)]
# Approximate 2D positions for 16 channels
positions = np.array([
    [0.0, 1.0], [0.5, 0.9], [1.0, 1.0],   # Fp1, Fpz, Fp2
    [-0.5, 0.5], [0.0, 0.5], [0.5, 0.5], [1.0, 0.5],  # C3, Cz, C4
    [-0.5, 0.0], [0.0, 0.0], [0.5, 0.0], [1.0, 0.0],  # T3, Pz, P4, T4
    [-0.3, -0.5], [0.3, -0.5],              # O1, O2
    [-0.7, 0.5], [0.7, 0.5],                # F7, F8
    [0.0, -0.5],                             # Oz
])
positions = positions[:N_CHANNELS]

# Color by mean amplitude in mu band window
mu_window = trial[:, int(0.3*FS):int(0.7*FS)]
ch_power = np.mean(mu_window**2, axis=1)
scatter = ax.scatter(positions[:, 0], positions[:, 1], c=ch_power, 
                     cmap='hot_r', s=200, edgecolors='black', linewidth=1)
for i in range(N_CHANNELS):
    ax.annotate(ch_names[i], positions[i], textcoords="offset points", 
                xytext=(0, -18), ha='center', fontsize=6)
ax.set_title('Channel Topo (Mu Power)')
ax.set_xlim(-1.2, 1.5)
ax.set_ylim(-0.8, 1.3)
ax.set_aspect('equal')
ax.axis('off')
plt.colorbar(scatter, ax=ax, label='Mu Power (μV²)', shrink=0.8)

plt.suptitle('EEG Data Representation for Deep Learning', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{SAVE_DIR}day15_plot_1.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved day15_plot_1.png")

# ============================================================
# Plot 2: EEGNet Architecture Visualization
# ============================================================
print("\nPlot 2: EEGNet architecture...")

fig, ax = plt.subplots(figsize=(16, 8))
ax.set_xlim(0, 16)
ax.set_ylim(0, 10)
ax.axis('off')

# Layer boxes
layers = [
    {'name': 'Input\n(1, C, T)', 'pos': (0.5, 4.5), 'size': (2, 3), 'color': '#E3F2FD'},
    {'name': 'Temporal Conv\n(2D, F1 kernels)\nkernel=T/2', 'pos': (3.2, 4.5), 'size': (2.5, 3), 'color': '#FFF3E0'},
    {'name': 'Depthwise\nConv\n(spatial filter)', 'pos': (6.2, 4.5), 'size': (2.2, 3), 'color': '#E8F5E9'},
    {'name': 'Separable Conv\n(Pointwise +\nTemporal)', 'pos': (8.9, 4.5), 'size': (2.5, 3), 'color': '#F3E5F5'},
    {'name': 'Avg Pool\n+ Dropout', 'pos': (11.9, 5.5), 'size': (1.8, 2), 'color': '#FFEBEE'},
    {'name': 'Dense\n+ Softmax', 'pos': (11.9, 3.0), 'size': (1.8, 2), 'color': '#E0F7FA'},
]

for layer in layers:
    x, y = layer['pos']
    w, h = layer['size']
    rect = FancyBboxPatch((x, y - h/2), w, h, boxstyle="round,pad=0.15",
                          facecolor=layer['color'], edgecolor='#333333', linewidth=2)
    ax.add_patch(rect)
    ax.text(x + w/2, y, layer['name'], ha='center', va='center', fontsize=9, fontweight='bold')

# Arrows
arrow_pairs = [
    (2.5, 4.5), (5.7, 4.5), (8.4, 4.5), (11.4, 5.5),
    (12.8, 4.5), (12.8, 4.0),
]
for i in range(len(arrow_pairs) - 1):
    x1, y1 = arrow_pairs[i]
    x2, y2 = arrow_pairs[i + 1]
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=2))

# Analogy annotations
annotations = [
    (4.5, 8.5, '≡ Learn ERP waveforms\n(like matching templates)', '#FFF3E0'),
    (7.3, 8.5, '≡ Learn channel weights\n(like CSP spatial filter)', '#E8F5E9'),
    (10.1, 8.5, '≡ Learn channel combinations\n(like CSP projection)', '#F3E5F5'),
    (12.8, 8.0, '≡ log(var) + LDA\n(end-to-end)', '#FFEBEE'),
]

for x, y, text, color in annotations:
    bbox = FancyBboxPatch((x - 1.8, y - 0.8), 3.6, 1.6, boxstyle="round,pad=0.1",
                          facecolor=color, edgecolor='gray', linewidth=1, alpha=0.9)
    ax.add_patch(bbox)
    ax.text(x, y, text, ha='center', va='center', fontsize=8, style='italic')
    # Dashed line to layer
    ax.plot([x, x], [y - 0.8, 6.0], '--', color='gray', alpha=0.5, linewidth=1)

# Parameter count box
param_box = FancyBboxPatch((0.5, 0.5), 5, 1.5, boxstyle="round,pad=0.1",
                           facecolor='#F5F5F5', edgecolor='#666666', linewidth=1.5)
ax.add_patch(param_box)
ax.text(3.0, 1.25, 'EEGNet: ~2,000 params | Shallow ConvNet: ~5,000 | Deep ConvNet: ~50,000',
        ha='center', va='center', fontsize=9, fontweight='bold')

# Key insight
ax.text(10.5, 1.25, 'Depthwise Separable Conv\n= temporal + spatial factorization\n→ fewer params, less overfitting',
        ha='center', va='center', fontsize=8, style='italic',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

ax.set_title('EEGNet Architecture — The "ResNet of BCI"', fontsize=14, fontweight='bold', pad=15)
plt.savefig(f'{SAVE_DIR}day15_plot_2.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved day15_plot_2.png")

# ============================================================
# Plot 3: Shallow ConvNet vs Deep ConvNet Architecture
# ============================================================
print("\nPlot 3: ConvNet architectures comparison...")

fig, axes = plt.subplots(2, 1, figsize=(15, 10))

# --- Shallow ConvNet ---
ax = axes[0]
ax.set_xlim(0, 15)
ax.set_ylim(0, 6)
ax.axis('off')

shallow_layers = [
    ('Input\n(1,C,T)', 0.3, '#E3F2FD'),
    ('Temporal\nConv\n(25ms kernel)', 2.5, '#FFF3E0'),
    ('Spatial\nConv\n(C→1 filter)', 5.0, '#E8F5E9'),
    ('Square', 7.5, '#FFEBEE'),
    ('Log', 9.0, '#FFEBEE'),
    ('Dense\n+ Softmax', 11.0, '#E0F7FA'),
]

for name, x, color in shallow_layers:
    rect = FancyBboxPatch((x, 1.5), 1.8, 3, boxstyle="round,pad=0.1",
                          facecolor=color, edgecolor='#333', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x + 0.9, 3.0, name, ha='center', va='center', fontsize=8, fontweight='bold')

for i in range(len(shallow_layers) - 1):
    x1 = shallow_layers[i][1] + 1.8
    x2 = shallow_layers[i + 1][1]
    ax.annotate('', xy=(x2, 3.0), xytext=(x1, 3.0),
                arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))

ax.text(7.5, 5.2, 'Shallow ConvNet ≈ Learnable CSP + LDA', 
        ha='center', fontsize=11, fontweight='bold', color='#2E7D32')
ax.text(7.5, 0.6, 'Square + Log ≈ log(w^T Cw) = CSP log-variance feature', 
        ha='center', fontsize=9, style='italic', color='gray')

# --- Deep ConvNet ---
ax = axes[1]
ax.set_xlim(0, 15)
ax.set_ylim(0, 6)
ax.axis('off')

deep_layers = [
    ('Input\n(1,C,T)', 0.3, '#E3F2FD'),
    ('Conv1\nTemporal', 2.2, '#FFF3E0'),
    ('Conv2\nSpatial', 3.8, '#E8F5E9'),
    ('Conv3', 5.4, '#F3E5F5'),
    ('Conv4', 7.0, '#F3E5F5'),
    ('Pool +\nDropout', 8.6, '#FFEBEE'),
    ('Dense 1', 10.2, '#E0F7FA'),
    ('Dense 2\n+ Softmax', 12.0, '#E0F7FA'),
]

for name, x, color in deep_layers:
    rect = FancyBboxPatch((x, 1.5), 1.3, 3, boxstyle="round,pad=0.1",
                          facecolor=color, edgecolor='#333', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x + 0.65, 3.0, name, ha='center', va='center', fontsize=7.5, fontweight='bold')

for i in range(len(deep_layers) - 1):
    x1 = deep_layers[i][1] + 1.3
    x2 = deep_layers[i + 1][1]
    ax.annotate('', xy=(x2, 3.0), xytext=(x1, 3.0),
                arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))

ax.text(7.0, 5.2, 'Deep ConvNet — Hierarchical Feature Extraction', 
        ha='center', fontsize=11, fontweight='bold', color='#6A1B9A')
ax.text(7.0, 0.6, 'More layers = richer features, but needs more data (risk of overfitting)', 
        ha='center', fontsize=9, style='italic', color='gray')

plt.suptitle('BCI Convolutional Network Architectures', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{SAVE_DIR}day15_plot_3.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved day15_plot_3.png")

# ============================================================
# Plot 4: Traditional vs Deep Learning — Simulated Performance
# ============================================================
print("\nPlot 4: Traditional vs Deep Learning performance...")

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# 4a: Accuracy vs Training Data Size
ax = axes[0]
n_trials_list = [20, 50, 100, 200, 500, 1000]

# Simulated accuracy curves (realistic ranges)
csp_acc = [0.55, 0.68, 0.78, 0.82, 0.84, 0.85]
eegnet_acc = [0.50, 0.62, 0.76, 0.85, 0.90, 0.92]
deepconv_acc = [0.48, 0.55, 0.70, 0.83, 0.91, 0.94]
shallow_acc = [0.52, 0.65, 0.77, 0.84, 0.88, 0.90]

ax.plot(n_trials_list, csp_acc, 'o-', label='CSP + LDA', linewidth=2, markersize=6, color='#2196F3')
ax.plot(n_trials_list, shallow_acc, 's-', label='Shallow ConvNet', linewidth=2, markersize=6, color='#4CAF50')
ax.plot(n_trials_list, eegnet_acc, '^-', label='EEGNet', linewidth=2, markersize=6, color='#FF9800')
ax.plot(n_trials_list, deepconv_acc, 'D-', label='Deep ConvNet', linewidth=2, markersize=6, color='#9C27B0')

ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.3, label='Chance')
ax.set_xlabel('Training Trials per Class')
ax.set_ylabel('Accuracy')
ax.set_title('Accuracy vs Data Size')
ax.legend(fontsize=8, loc='lower right')
ax.set_ylim(0.4, 1.0)
ax.grid(True, alpha=0.3)

# 4b: Cross-subject generalization
ax = axes[1]
subjects = ['Within\nSubject', '1 New\nSubject', '3 New\nSubjects', '5 New\nSubjects', '10 New\nSubjects']
csp_cross = [0.82, 0.58, 0.62, 0.65, 0.68]
eegnet_cross = [0.85, 0.65, 0.72, 0.76, 0.80]
eegnet_ft = [0.85, 0.78, 0.80, 0.82, 0.84]  # EEGNet + fine-tune

x = np.arange(len(subjects))
width = 0.25
ax.bar(x - width, csp_cross, width, label='CSP + LDA', color='#2196F3', alpha=0.8)
ax.bar(x, eegnet_cross, width, label='EEGNet (from scratch)', color='#FF9800', alpha=0.8)
ax.bar(x + width, eegnet_ft, width, label='EEGNet + Fine-tune', color='#4CAF50', alpha=0.8)

ax.set_ylabel('Accuracy')
ax.set_title('Cross-Subject Generalization')
ax.set_xticks(x)
ax.set_xticklabels(subjects, fontsize=8)
ax.legend(fontsize=7, loc='lower right')
ax.set_ylim(0.4, 1.0)
ax.grid(True, alpha=0.3, axis='y')

# 4c: Inference time vs accuracy
ax = axes[2]
methods = {
    'CSP+LDA': (0.5, 0.82, '#2196F3', 150),
    'CCA': (0.8, 0.80, '#9C27B0', 150),
    'EEGNet': (5, 0.85, '#FF9800', 200),
    'Shallow\nConvNet': (8, 0.84, '#4CAF50', 180),
    'Deep\nConvNet': (50, 0.91, '#F44336', 200),
    'Transformer': (120, 0.93, '#607D8B', 250),
}

for name, (time_ms, acc, color, size) in methods.items():
    ax.scatter(time_ms, acc, s=size, c=color, alpha=0.8, edgecolors='black', linewidth=1, zorder=3)
    ax.annotate(name, (time_ms, acc), textcoords="offset points",
                xytext=(10, 5), fontsize=8, fontweight='bold')

ax.axvline(x=20, color='red', linestyle='--', alpha=0.5, label='Real-time threshold (~20ms)')
ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.3)
ax.set_xlabel('Inference Time (ms, single trial)')
ax.set_ylabel('Accuracy')
ax.set_title('Speed vs Accuracy Trade-off')
ax.set_xscale('log')
ax.legend(fontsize=8)
ax.set_ylim(0.4, 1.0)
ax.grid(True, alpha=0.3)

plt.suptitle('Traditional vs Deep Learning in BCI', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{SAVE_DIR}day15_plot_4.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved day15_plot_4.png")

# ============================================================
# Plot 5: Data Augmentation & Transfer Learning
# ============================================================
print("\nPlot 5: Data augmentation & transfer learning...")

fig, axes = plt.subplots(2, 3, figsize=(16, 10))

# --- Row 1: Data Augmentation Techniques ---
trial_sample = X_train[0, :3, :]  # 3 representative channels
t_axis = np.arange(N_TIMES) / FS

# 5a: Original
ax = axes[0, 0]
for ch in range(3):
    ax.plot(t_axis, trial_sample[ch] + ch * 6, linewidth=0.8)
ax.set_title('Original EEG')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Channel (offset)')

# 5b: Time Shift
ax = axes[0, 1]
shift = int(0.05 * FS)  # 50ms shift
shifted = np.roll(trial_sample, shift, axis=1)
for ch in range(3):
    ax.plot(t_axis, shifted[ch] + ch * 6, linewidth=0.8, color='orange')
ax.axvline(x=0.05, color='red', linestyle='--', alpha=0.5, label='Shifted +50ms')
ax.set_title('Time Shift (+50ms)')
ax.set_xlabel('Time (s)')
ax.legend(fontsize=7)

# 5c: Channel Dropout
ax = axes[0, 2]
dropped = trial_sample.copy()
dropped[1, :] = 0  # Drop channel 1
for ch in range(3):
    color = 'gray' if ch == 1 else 'steelblue'
    alpha = 0.3 if ch == 1 else 1.0
    ax.plot(t_axis, dropped[ch] + ch * 6, linewidth=0.8, color=color, alpha=alpha)
ax.set_title('Channel Dropout (Ch1 → 0)')
ax.set_xlabel('Time (s)')

# 5d: Gaussian Noise
ax = axes[1, 0]
noisy = trial_sample + np.random.randn(*trial_sample.shape) * 1.0
for ch in range(3):
    ax.plot(t_axis, noisy[ch] + ch * 6, linewidth=0.8, color='green')
ax.set_title('+ Gaussian Noise (σ=1.0)')
ax.set_xlabel('Time (s)')

# 5e: Frequency Mask
ax = axes[1, 1]
# Simulate by notch-filtering a band
from scipy.signal import butter, filtfilt
masked = trial_sample.copy()
for ch in range(3):
    # Add notch at 8-12 Hz to simulate masking
    b, a = butter(4, [8/(FS/2), 12/(FS/2)], btype='bandstop')
    masked[ch] = filtfilt(b, a, trial_sample[ch])
    ax.plot(t_axis, masked[ch] + ch * 6, linewidth=0.8, color='purple')
ax.set_title('Frequency Mask (8-12 Hz removed)')
ax.set_xlabel('Time (s)')

# 5f: Augmentation effect on accuracy
ax = axes[1, 2]
aug_methods = ['Baseline\n(no aug)', '+ Time\nShift', '+ Channel\nDropout', '+ Noise', '+ All\nCombined']
accs = [0.76, 0.79, 0.78, 0.80, 0.84]
colors_aug = ['#9E9E9E', '#FF9800', '#4CAF50', '#2196F3', '#F44336']
bars = ax.bar(range(len(aug_methods)), accs, color=colors_aug, edgecolor='black', linewidth=1)
ax.set_xticks(range(len(aug_methods)))
ax.set_xticklabels(aug_methods, fontsize=8)
ax.set_ylabel('Accuracy')
ax.set_title('Augmentation Impact (100 trials)')
ax.set_ylim(0.6, 0.95)
for bar, acc in zip(bars, accs):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
            f'{acc:.0%}', ha='center', fontsize=9, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

plt.suptitle('Data Augmentation for BCI Deep Learning', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{SAVE_DIR}day15_plot_5.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved day15_plot_5.png")

# ============================================================
# Plot 6: Transfer Learning Concept & Week 5 Summary
# ============================================================
print("\nPlot 6: Transfer learning & Week 5 summary...")

fig = plt.figure(figsize=(16, 10))

# --- Transfer Learning Visualization ---
ax = fig.add_axes([0.05, 0.52, 0.9, 0.42])
ax.set_xlim(0, 16)
ax.set_ylim(0, 8)
ax.axis('off')

# Source subjects (pre-training)
for i in range(5):
    rect = FancyBboxPatch((0.3 + i * 1.5, 5.5), 1.2, 1.5, boxstyle="round,pad=0.1",
                          facecolor='#E3F2FD', edgecolor='#1565C0', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(0.9 + i * 1.5, 6.25, f'Subj {i+1}\n(100 trials)', ha='center', va='center', fontsize=8)

ax.text(4.5, 7.6, 'Pre-training: 500 trials from 5 subjects', ha='center', fontsize=11, fontweight='bold', color='#1565C0')

# Arrow to pre-trained model
ax.annotate('', xy=(8.0, 4.5), xytext=(4.5, 5.3),
            arrowprops=dict(arrowstyle='->', color='#1565C0', lw=2.5))

# Pre-trained model
rect = FancyBboxPatch((5.5, 3.0), 5.0, 2.5, boxstyle="round,pad=0.15",
                      facecolor='#FFF3E0', edgecolor='#E65100', linewidth=2)
ax.add_patch(rect)
ax.text(8.0, 4.8, 'Pre-trained EEGNet', ha='center', va='center', fontsize=11, fontweight='bold')
ax.text(8.0, 3.7, 'Learned general EEG features:\nERP patterns, spatial filters, frequency features',
        ha='center', va='center', fontsize=8, style='italic')

# Fine-tune arrow
ax.annotate('', xy=(14.5, 4.5), xytext=(10.5, 4.5),
            arrowprops=dict(arrowstyle='->', color='#2E7D32', lw=2.5))
ax.text(12.5, 5.2, 'Fine-tune\n(~20 trials)', ha='center', fontsize=9, fontweight='bold', color='#2E7D32')

# Target subject
rect = FancyBboxPatch((13.0, 3.0), 2.5, 3, boxstyle="round,pad=0.15",
                      facecolor='#E8F5E9', edgecolor='#2E7D32', linewidth=2)
ax.add_patch(rect)
ax.text(14.25, 5.0, 'New Subject', ha='center', va='center', fontsize=10, fontweight='bold')
ax.text(14.25, 3.8, '20 min → 2 min\ncalibration', ha='center', va='center', fontsize=9, color='#2E7D32')

# Comparison box
comp_box = FancyBboxPatch((0.3, 0.5), 5.5, 2.0, boxstyle="round,pad=0.1",
                          facecolor='#F5F5F5', edgecolor='#666', linewidth=1.5)
ax.add_patch(comp_box)
ax.text(3.05, 1.5, 
        'Calibration Time Comparison:\n'
        'From scratch: 20 min (200 trials)\n'
        'Transfer + fine-tune: 2 min (20 trials)\n'
        '→ 10x reduction in setup time!',
        ha='center', va='center', fontsize=8, fontweight='bold')

# --- Week 5 Summary Table ---
ax2 = fig.add_axes([0.05, 0.02, 0.9, 0.45])
ax2.axis('off')

# Create a nice summary table
days = ['Day 11', 'Day 12', 'Day 13', 'Day 14', 'Day 15']
topics = ['BCI System\nArchitecture', 'SSVEP +\nCCA/FBCCA', 'Motor Imagery\n+ CSP', 'P300 +\nOddball', 'Deep Learning\n+ EEGNet']
methods = ['Signal acquisition\nProtocol & pipeline', 'CCA: max correlation\nFBCCA: filter bank', 'Spatial filter\nlog-var + LDA', 'Stepwise LDA\nRepetition voting', 'EEGNet: 2K params\nTransfer learning']
colors_w5 = ['#BBDEFB', '#C8E6C9', '#FFF9C4', '#FFCCBC', '#E1BEE7']

for i in range(5):
    rect = FancyBboxPatch((0.5 + i * 3.0, 0.5), 2.5, 4.0, boxstyle="round,pad=0.1",
                          facecolor=colors_w5[i], edgecolor='#333', linewidth=1.5)
    ax2.add_patch(rect)
    ax2.text(1.75 + i * 3.0, 3.8, days[i], ha='center', va='center', fontsize=10, fontweight='bold')
    ax2.text(1.75 + i * 3.0, 2.8, topics[i], ha='center', va='center', fontsize=9, fontweight='bold')
    ax2.text(1.75 + i * 3.0, 1.5, methods[i], ha='center', va='center', fontsize=7, style='italic')

ax2.text(8.0, 4.9, 'Week 5 Complete: BCI Paradigms & Deep Learning', 
         ha='center', fontsize=13, fontweight='bold')

plt.savefig(f'{SAVE_DIR}day15_plot_6.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved day15_plot_6.png")

# ============================================================
# Summary
# ============================================================
print("\n" + "="*60)
print("Day 15: Deep Learning in BCI — Key Takeaways")
print("="*60)
print("""
1. EEG as Image: (Channels × Time) → 2D input for CNNs
   - Spatial conv = learn channel relationships
   - Temporal conv = learn ERP/oscillation patterns

2. EEGNet: The "ResNet of BCI"
   - Depthwise separable convolution = temporal + spatial factorization
   - ~2,000 parameters → works with small BCI datasets
   - Cross-paradigm: P300, MI, SSVEP all work

3. Shallow ConvNet = Learnable CSP + LDA
   - Square + Log = log-variance (same as CSP)
   - But weights are learned from data, not analytically derived

4. When to use Deep Learning:
   - Small data (≤100 trials) → stick with traditional methods
   - Medium data (200-500) → EEGNet with augmentation
   - Large data / cross-subject → Deep learning + transfer learning

5. Key BCI challenges for DL:
   - Data scarcity → augmentation, transfer learning
   - Cross-subject variability → domain adaptation, fine-tuning
   - Real-time constraint → EEGNet (~5ms inference)
""")
print("✅ Day 15 所有图表生成完毕!")
