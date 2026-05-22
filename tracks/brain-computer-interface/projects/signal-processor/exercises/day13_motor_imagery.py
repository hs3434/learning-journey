"""
Day 13: Motor Imagery (MI) and CSP Algorithm
=============================================

Week 5 Day 3: Motor imagery principles, ERD/ERS patterns, CSP spatial filtering

Goals:
1. Understand motor imagery signal characteristics
2. Learn CSP (Common Spatial Pattern) algorithm
3. Implement CSP for binary MI classification
4. Visualize spatial patterns and discriminability
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

out_dir = Path(__file__).parent
out_dir.mkdir(exist_ok=True)

# =============================================================================
# Figure 1: Motor Cortex Organization (Homunculus)
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 8))
ax.set_aspect('equal')
ax.axis('off')
ax.set_title('Motor Cortex: Homunculus Map', fontsize=14, fontweight='bold')

# Head outline
theta = np.linspace(0, 2*np.pi, 100)
head_x = np.cos(theta)
head_y = np.sin(theta)
ax.plot(head_x, head_y, 'k-', linewidth=2)

# Motor cortex region (中央沟后方)
cortex = plt.Circle((0, 0), 0.7, fill=False, edgecolor='red', linewidth=2, linestyle='--')
ax.add_patch(cortex)
ax.text(0, 0.85, 'Motor\nCortex', ha='center', va='bottom', fontsize=9, color='red')

# Body parts mapped to cortex (simplified lateral view)
# Left cortex controls right body, vice versa
body_parts = [
    # (x_offset, y_position, size, name, cortex_side)
    (0.1, 0.5, 0.08, 'Foot', 'left'),    # Foot at top (medial)
    (0.2, 0.35, 0.12, 'Leg', 'left'),
    (0.3, 0.15, 0.15, 'Trunk', 'left'),
    (0.4, -0.05, 0.18, 'Arm', 'left'),
    (0.5, -0.25, 0.12, 'Hand', 'left'),
    (0.55, -0.45, 0.08, 'Fingers', 'left'),
    (0.5, -0.6, 0.06, 'Neck', 'left'),
    (0.3, -0.75, 0.12, 'Face/\nTongue', 'left'),
]

# Draw simplified homunculus
for x, y, size, name, side in body_parts:
    circle = plt.Circle((x, y), size, color='#FFE0B2', edgecolor='#E65100', linewidth=1.5)
    ax.add_patch(circle)
    ax.text(x + size + 0.05, y, name, ha='left', va='center', fontsize=8)

# Labels
ax.text(-0.6, 0.5, 'Right\nBrain\n(L->R)', ha='center', va='center', fontsize=9, 
        bbox=dict(boxstyle='round', facecolor='#E3F2FD', edgecolor='#1976D2'))
ax.text(0.85, 0, 'Body\nParts', ha='left', va='center', fontsize=9,
        bbox=dict(boxstyle='round', facecolor='#FFF3E0', edgecolor='#FF9800'))

# Arrow showing the mapping
ax.annotate('', xy=(0.75, 0.35), xytext=(0.65, 0.5),
           arrowprops=dict(arrowstyle='->', color='green', lw=2))

plt.tight_layout()
path = out_dir / 'day13_plot_1.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 1 saved: {path}')

# =============================================================================
# Figure 2: ERD/ERS During Motor Imagery
# =============================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('ERD/ERS During Motor Imagery', fontsize=14, fontweight='bold')

fs = 250
t_imagery = np.arange(-2, 6, 1/fs)  # -2s to 6s relative to cue

# 2a: Alpha (mu) rhythm power
ax1 = axes[0]
# Imagine RIGHT hand -> LEFT motor cortex ERD
mu_right = -np.exp(-((t_imagery - 0)**2) / 0.5) * 0.8  # ERD at left cortex
mu_baseline = np.zeros_like(t_imagery)

# Simulate alpha power at C3 and C4 (left/right motor cortex)
t_cue = 0  # cue onset

# C3 (left hemisphere) - ERD during right hand imagination
c3_power = 1.0 * np.ones_like(t_imagery)
c3_erd = np.exp(-((t_imagery - 0.5)**2) / 0.8) * 0.6
c3_power = c3_power - c3_erd

# C4 (right hemisphere) - less change
c4_power = 1.0 * np.ones_like(t_imagery)
c4_erd = np.exp(-((t_imagery - 0.5)**2) / 0.8) * 0.2
c4_power = c4_power - c4_erd

ax1.fill_between(t_imagery, 1.0, c3_power, where=(c3_power < 1.0), 
                 alpha=0.5, color='red', label='C3 (contralateral) - ERD')
ax1.fill_between(t_imagery, 1.0, c4_power, where=(c4_power < 1.0), 
                 alpha=0.5, color='green', label='C4 (ipsilateral)')
ax1.plot(t_imagery, c3_power, 'r-', linewidth=1.5)
ax1.plot(t_imagery, c4_power, 'g-', linewidth=1.5)
ax1.axvline(x=0, color='black', linestyle='--', label='Cue onset')
ax1.axhline(y=1.0, color='gray', linestyle=':', alpha=0.5)
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Relative Power (baseline=1)')
ax1.set_title('Imagine RIGHT Hand: Mu Rhythm Power')
ax1.legend(fontsize=8)
ax1.set_xlim(-1, 4)
ax1.grid(True, alpha=0.3)

# 2b: Beta rebound
ax2 = axes[1]

# Beta power at C3
beta_c3 = 1.0 * np.ones_like(t_imagery)
beta_ers = np.exp(-((t_imagery - 2)**2) / 1.5) * 0.7  # ERS after imagination
beta_c3 = beta_c3 + beta_ers

# Beta power at C4 (less rebound)
beta_c4 = 1.0 * np.ones_like(t_imagery)
beta_ers_c4 = np.exp(-((t_imagery - 2)**2) / 1.5) * 0.2
beta_c4 = beta_c4 + beta_ers_c4

ax2.fill_between(t_imagery, 1.0, beta_c3, where=(beta_c3 > 1.0), 
                 alpha=0.5, color='blue', label='C3 (contralateral) - ERS')
ax2.fill_between(t_imagery, 1.0, beta_c4, where=(beta_c4 > 1.0), 
                 alpha=0.5, color='lightgreen', label='C4 (ipsilateral)')
ax2.plot(t_imagery, beta_c3, 'b-', linewidth=1.5)
ax2.plot(t_imagery, beta_c4, 'g-', linewidth=1.5)
ax2.axvline(x=0, color='black', linestyle='--', label='Cue onset')
ax2.axhline(y=1.0, color='gray', linestyle=':', alpha=0.5)
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('Relative Power (baseline=1)')
ax2.set_title('Beta Rebound (ERS) After Motor Imagery')
ax2.legend(fontsize=8)
ax2.set_xlim(-1, 4)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
path = out_dir / 'day13_plot_2.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 2 saved: {path}')

# =============================================================================
# Figure 3: CSP Algorithm Principle
# =============================================================================
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle('CSP (Common Spatial Pattern) Algorithm', fontsize=14, fontweight='bold')

# 3a: EEG covariance for two classes
ax1 = axes[0]
ax1.set_xlim(-1, 3)
ax1.set_ylim(-1, 3)
ax1.axis('off')
ax1.set_title('Step 1: Compute Covariances')

# Class 1: Right hand (C3 > C4)
cov1_mean = [0.8, 0.8]
cov1 = np.array([[0.4, 0.1], [0.1, 0.4]])  # diagonal, C3 and C4 independent
mean1 = np.array(cov1_mean)

# Class 2: Left hand (C4 > C3)
cov2 = np.array([[0.2, 0.05], [0.05, 0.3]])
mean2 = [1.5, 1.5]

# Draw ellipses for covariances
from matplotlib.patches import Ellipse
ellipse1 = Ellipse(cov1_mean, width=1.2, height=1.2, angle=0, 
                   facecolor='red', alpha=0.3, edgecolor='red', linewidth=2)
ellipse2 = Ellipse(mean2, width=0.9, height=1.1, angle=0, 
                   facecolor='blue', alpha=0.3, edgecolor='blue', linewidth=2)
ax1.add_patch(ellipse1)
ax1.add_patch(ellipse2)
ax1.text(cov1_mean[0], cov1_mean[1]-0.8, 'Right\n(C3>C4)', ha='center', fontsize=9, color='red')
ax1.text(mean2[0], mean2[1]+0.8, 'Left\n(C4>C3)', ha='center', fontsize=9, color='blue')
ax1.set_xlabel('C3 channel variance')
ax1.set_ylabel('C4 channel variance')

# 3b: CSP projection
ax2 = axes[1]
ax2.set_xlim(-1, 3)
ax2.set_ylim(-1, 3)
ax2.axis('off')
ax2.set_title('Step 2: CSP Projection')

# CSP finds directions that maximize variance ratio
# w1: maximizes class1 variance / class2 variance
# w2: minimizes class1 variance / class2 variance

# Draw CSP axes
ax2.annotate('', xy=(2.5, 1.5), xytext=(0, 0),
           arrowprops=dict(arrowstyle='->', color='green', lw=3))
ax2.annotate('', xy=(1.5, 2.5), xytext=(0, 0),
           arrowprops=dict(arrowstyle='->', color='purple', lw=2, ls='--'))

ax2.text(1.8, 1.2, 'w1\n(max variance\nfor class 1)', ha='left', fontsize=8, color='green')
ax2.text(0.8, 2.0, 'w2\n(max variance\nfor class 2)', ha='left', fontsize=8, color='purple')

# Projected distributions
ax2.plot([0.5, 2], [0.5, 2], 'r-', linewidth=2, label='Project to w1')
ax2.plot([0.8, 1.8], [1.2, 0.2], 'b--', linewidth=2, label='Project to w2')

# 3c: Projected features
ax3 = axes[2]
ax3.set_title('Step 3: Classified Features')

# Histogram of projected values
x_class1 = np.random.randn(100) * 0.3 + 1.5  # Mean 1.5 for class 1
x_class2 = np.random.randn(100) * 0.3 + 0.8   # Mean 0.8 for class 2

ax3.hist(x_class1, bins=20, alpha=0.6, color='red', label='Right hand', density=True)
ax3.hist(x_class2, bins=20, alpha=0.6, color='blue', label='Left hand', density=True)
ax3.axvline(x=1.15, color='black', linestyle='--', linewidth=2, label='Decision boundary')
ax3.set_xlabel('Projected value (CSP feature)')
ax3.set_ylabel('Density')
ax3.legend()
ax3.set_xlim(-0.5, 2.5)

plt.tight_layout()
path = out_dir / 'day13_plot_3.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 3 saved: {path}')

# =============================================================================
# Figure 4: CSP Mathematical Formulation
# =============================================================================
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_title('CSP Mathematical Formulation', fontsize=14, fontweight='bold')

# Step boxes
steps = [
    (1, '1. Normalize Covariance\n\nC_i = (X_i X_i^T) / trace(X_i X_i^T)\n\nX_i: EEG data for class i\nC_i: Normalized covariance'),
    (4.5, '2. Composite Covariance\n\nC_c = C_1 + C_2\n\nSum of both class covariances'),
    (8, '3. Simultaneous Diagonalization\n\nFind W: C_c^-1 C_1 = W Lambda W^-1\n\nEigenvectors in W'),
    (11.5, '4. CSP Features\n\nZ = W^T X\n\nf = log(var(Z) / sum(var(Z)))\n\nLog-variance as features'),
]

colors = ['#E3F2FD', '#FFF3E0', '#E8F5E9', '#F3E5F5']
for i, (x, text) in enumerate(steps):
    rect = plt.Rectangle((x-0.8, 3), 3, 5), 
    rect = plt.Rectangle((x-0.8, 3), 3, 5, facecolor=colors[i], edgecolor='#333', linewidth=2)
    ax.add_patch(rect)
    ax.text(x+0.7, 5.5, text, ha='center', va='center', fontsize=9)

# Arrows between steps
for x in [2.8, 6.3, 9.8]:
    ax.annotate('', xy=(x+1, 5.5), xytext=(x, 5.5),
               arrowprops=dict(arrowstyle='->', color='#333', lw=2))

# Key insight box
insight_box = plt.Rectangle((1, 0.5), 12, 2), 
insight_box = plt.Rectangle((1, 0.5), 12, 2, facecolor='#E0F7FA', edgecolor='#00BCD4', linewidth=2)
ax.add_patch(insight_box)
ax.text(7, 1.5, 
        'Key Insight:\n'
        'CSP finds spatial filters that MAXIMIZE variance for one class\n'
        'while MINIMIZING variance for the other class.\n'
        '-> Most discriminative projection direction!',
        ha='center', va='center', fontsize=10, fontweight='bold')

plt.tight_layout()
path = out_dir / 'day13_plot_4.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 4 saved: {path}')

# =============================================================================
# Figure 5: CSP Implementation
# =============================================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('CSP Implementation Example', fontsize=14, fontweight='bold')

# Simulate MI EEG data
np.random.seed(42)
fs = 250
n_channels = 8
n_samples = int(fs * 3)  # 3 seconds
t = np.arange(n_samples) / fs

# Generate synthetic MI data
def generate_mi_data(n_trials, n_channels, n_samples, class_label):
    """Generate synthetic MI EEG data"""
    data = []
    for _ in range(n_trials):
        trial = np.zeros((n_channels, n_samples))
        for ch in range(n_channels):
            # Base EEG (alpha rhythm ~10 Hz)
            base = np.sin(2 * np.pi * 10 * t + np.random.rand() * 2 * np.pi) * 10
            # Add mu rhythm ERD for contralateral channels
            if class_label == 0:  # Right hand -> ERD at left channels (0-3)
                if ch < 4:
                    erd = np.exp(-((t - 1)**2) / 0.5) * 5
                    base = base - erd
            else:  # Left hand -> ERD at right channels (4-7)
                if ch >= 4:
                    erd = np.exp(-((t - 1)**2) / 0.5) * 5
                    base = base - erd
            # Add noise
            trial[ch] = base + np.random.randn(n_samples) * 2
        data.append(trial)
    return np.array(data)

# Generate data
X_right = generate_mi_data(50, n_channels, n_samples, 0)  # Right hand
X_left = generate_mi_data(50, n_channels, n_samples, 1)   # Left hand

# 5a: Original EEG (C3 and C4 channels)
ax1 = axes[0, 0]
# C3 is channel 3, C4 is channel 4
ax1.plot(t, X_right[0, 3, :], 'r-', linewidth=0.5, alpha=0.8, label='Right hand - C3')
ax1.plot(t, X_right[0, 4, :], 'b-', linewidth=0.5, alpha=0.8, label='Right hand - C4')
ax1.set_title('EEG During Right Hand Imagery')
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Amplitude (uV)')
ax1.legend(fontsize=8)
ax1.set_xlim(0, 3)

# 5b: CSP spatial patterns (simplified)
ax2 = axes[0, 1]
# Simulate CSP patterns
n_patterns = 4
pattern_1 = np.random.randn(n_channels, n_patterns)
pattern_2 = np.random.randn(n_channels, n_patterns)

im = ax2.imshow(pattern_1, cmap='RdBu_r', aspect='auto')
ax2.set_title('CSP Spatial Patterns (First 4 patterns)')
ax2.set_xlabel('CSP Component')
ax2.set_ylabel('EEG Channel')
ax2.set_yticks(range(n_channels))
ax2.set_yticklabels(['Fp1', 'Fp2', 'C3', 'C4', 'Cz', 'P3', 'P4', 'Oz'][:n_channels])
plt.colorbar(im, ax=ax2, shrink=0.8)

# 5c: Variance ratio
ax3 = axes[1, 0]
# Simulate variance ratios for different CSP components
csp_components = np.arange(1, 9)
var_right = np.array([0.85, 0.78, 0.65, 0.55, 0.45, 0.35, 0.22, 0.15])
var_left = 1 - var_right

ax3.bar(csp_components - 0.2, var_right, width=0.4, color='red', alpha=0.7, label='Right hand variance')
ax3.bar(csp_components + 0.2, var_left, width=0.4, color='blue', alpha=0.7, label='Left hand variance')
ax3.set_xlabel('CSP Component')
ax3.set_ylabel('Normalized Variance')
ax3.set_title('Variance Ratio per CSP Component')
ax3.legend()
ax3.set_xticks(csp_components)

# 5d: Classification accuracy
ax4 = axes[1, 1]
# Simulate accuracy with different number of CSP components
n_csp_components = [2, 4, 6, 8]
acc_right_hand = [82, 88, 85, 80]
acc_left_hand = [80, 87, 84, 78]

x = np.arange(len(n_csp_components))
width = 0.35
ax4.bar(x - width/2, acc_right_hand, width, label='Right hand', color='red', alpha=0.7)
ax4.bar(x + width/2, acc_left_hand, width, label='Left hand', color='blue', alpha=0.7)
ax4.set_xlabel('Number of CSP Components')
ax4.set_ylabel('Accuracy (%)')
ax4.set_title('Classification Accuracy vs CSP Components')
ax4.set_xticks(x)
ax4.set_xticklabels(n_csp_components)
ax4.legend()
ax4.set_ylim(70, 95)

plt.tight_layout()
path = out_dir / 'day13_plot_5.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 5 saved: {path}')

# =============================================================================
# Figure 6: CSP vs Other Methods
# =============================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('CSP vs Other MI Classification Methods', fontsize=14, fontweight='bold')

# 6a: Method comparison
ax1 = axes[0]
methods = ['CSP + LDA', 'Filter Bank CSP', 'Deep Learning\n(EEGNet)', 'SSVEP\n(CCA)', 'P300\n(LDA)']
accuracies = [85, 90, 88, 75, 70]  # Typical accuracies
colors = ['#4CAF50', '#2196F3', '#9C27B0', '#FF9800', '#F44336']

bars = ax1.barh(methods, accuracies, color=colors, alpha=0.7, edgecolor='black')
ax1.set_xlabel('Typical Accuracy (%)')
ax1.set_title('MI Classification Methods')
ax1.set_xlim(0, 100)

for bar, acc in zip(bars, accuracies):
    ax1.text(acc + 1, bar.get_y() + bar.get_height()/2, f'{acc}%', 
             va='center', fontsize=10)

# 6b: Pros and Cons
ax2 = axes[1]
ax2.axis('off')

comparison_text = """
CSP (Common Spatial Pattern)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pros:
  + Excellent for binary MI classification
  + Interpretable spatial patterns
  + Computationally efficient
  + No need for reference signals

Cons:
  - Requires labeled training data
  - Sensitive to noise and artifacts
  - Binary classification (needs extension for multi-class)
  - Subject-specific (needs recalibration)

Extensions:
  - Filter Bank CSP (FBCSP): Multiple frequency bands
  - Regularized CSP: More robust to noise
  - Common Sparse Spatial Pattern: Feature selection
"""

ax2.text(0.05, 0.95, comparison_text, transform=ax2.transAxes,
        fontsize=10, verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='#F5F5F5', edgecolor='#333'))

plt.tight_layout()
path = out_dir / 'day13_plot_6.png'
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Fig 6 saved: {path}')

print('\n' + '='*60)
print('Day 13 Complete! Generated 6 figures.')
print('='*60)
