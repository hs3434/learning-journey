"""
Day 19: Decoding Results & Spectral Topo Visualization
=======================================================
Week 6 Day 4 — 解码结果显示与频谱拓扑图
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.gridspec import GridSpec
from scipy.signal import butter, filtfilt, welch
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# Plot 1: Confusion Matrix + Classification Metrics
# ============================================================
def plot1_confusion_metrics():
    fig = plt.figure(figsize=(14, 6), facecolor='#1a1a2e')
    gs = GridSpec(1, 2, figure=fig, wspace=0.4,
                  top=0.90, bottom=0.10, left=0.08, right=0.95)
    
    # Left: Confusion Matrix
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor('#0a0a23')
    
    cm = np.array([[45, 3, 2], [4, 42, 4], [1, 5, 44]])
    cm_norm = cm / cm.sum(axis=1, keepdims=True)
    
    im = ax1.imshow(cm_norm, cmap='Blues', vmin=0, vmax=1)
    class_names = ['Left Hand', 'Right Hand', 'Foot']
    
    for i in range(3):
        for j in range(3):
            color = 'white' if cm_norm[i, j] > 0.5 else 'black'
            ax1.text(j, i, f'{cm[i, j]}\n({cm_norm[i, j]:.0%})',
                    ha='center', va='center', color=color, fontsize=10, fontweight='bold')
    
    ax1.set_xticks(range(3))
    ax1.set_yticks(range(3))
    ax1.set_xticklabels(class_names, fontsize=9, color='white')
    ax1.set_yticklabels(class_names, fontsize=9, color='white')
    ax1.set_xlabel('Predicted', color='white', fontsize=10)
    ax1.set_ylabel('Actual', color='white', fontsize=10)
    ax1.set_title('Confusion Matrix', color='white', fontsize=12, fontweight='bold')
    cbar = fig.colorbar(im, ax=ax1, shrink=0.8)
    cbar.ax.tick_params(colors='white', labelsize=8)
    ax1.tick_params(colors='white')
    
    # Right: Metrics Dashboard
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor('#0a0a23')
    ax2.axis('off')
    
    metrics = [
        ('Accuracy', '85.2%', '#4CAF50'),
        ('Cohen\'s Kappa', '0.778', '#2196F3'),
        ('ITR', '62.3 bits/min', '#FF9800'),
        ('CV Score (5-fold)', '83.7% +/- 3.2%', '#9C27B0'),
        ('Valid Epochs', '150 / 162', '#00BCD4'),
        ('Rejected', '12 (7.4%)', '#F44336'),
    ]
    
    for i, (name, value, color) in enumerate(metrics):
        y = 0.90 - i * 0.15
        ax2.text(0.05, y, name + ':', fontsize=11, color='#aaa',
                fontweight='bold', transform=ax2.transAxes)
        ax2.text(0.65, y, value, fontsize=12, color=color,
                fontweight='bold', transform=ax2.transAxes)
    
    ax2.set_title('Performance Metrics', color='white', fontsize=12, fontweight='bold')
    
    fig.suptitle('Decoding Results Dashboard', color='white', fontsize=14, fontweight='bold')
    
    path = os.path.join(OUT_DIR, 'day19_plot_1.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 2: ITR vs Accuracy Curve
# ============================================================
def plot2_itr_curve():
    fig, ax = plt.subplots(1, 1, figsize=(10, 6), facecolor='#1a1a2e')
    ax.set_facecolor('#0a0a23')
    
    accuracies = np.linspace(0.01, 0.99, 200)
    
    for n_classes, color, label in [(2, '#4CAF50', '2-class'), 
                                      (3, '#2196F3', '3-class'),
                                      (4, '#FF9800', '4-class')]:
        itrs = []
        T = 4.0  # trial duration
        for P in accuracies:
            N = n_classes
            if 0 < P < 1:
                itr = (60 / T) * (np.log2(N) + P * np.log2(P) + 
                       (1 - P) * np.log2((1 - P) / (N - 1)))
            elif P >= 1:
                itr = (60 / T) * np.log2(N)
            else:
                itr = 0
            itrs.append(max(0, itr))
        
        ax.plot(accuracies * 100, itrs, color=color, linewidth=2.5, label=label)
    
    # Mark common operating points
    for acc, color in [(85, '#4CAF50'), (75, '#2196F3'), (70, '#FF9800')]:
        ax.axvline(acc, color='white', alpha=0.2, linewidth=0.5, linestyle=':')
    
    # Random guess lines
    for n, color in [(2, '#4CAF50'), (3, '#2196F3'), (4, '#FF9800')]:
        ax.plot(100 / n, 0, 'o', color=color, markersize=8)
        ax.text(100 / n, -3, f'chance\n{100/n:.0f}%', fontsize=7, 
                color=color, ha='center', va='top')
    
    ax.set_xlabel('Classification Accuracy (%)', color='white', fontsize=11)
    ax.set_ylabel('ITR (bits/min)', color='white', fontsize=11)
    ax.set_title('Information Transfer Rate vs Accuracy', color='white', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10, facecolor='#0a0a23', edgecolor='#444', labelcolor='white')
    ax.set_xlim(0, 100)
    ax.set_ylim(-5, 80)
    ax.tick_params(colors='white', labelsize=9)
    ax.grid(True, alpha=0.15, color='white')
    for spine in ax.spines.values():
        spine.set_color('#333')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day19_plot_2.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 3: Band Power Topomaps (Simulated)
# ============================================================
def plot3_band_topomaps():
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.5), facecolor='#1a1a2e')
    
    bands = [
        ('Delta (1-4 Hz)', '#9C27B0', -0.2, 0.3),
        ('Theta (4-8 Hz)', '#00BCD4', 0.1, 0.5),
        ('Alpha (8-13 Hz)', '#4CAF50', 0.3, 1.0),
        ('Beta (13-30 Hz)', '#FF9800', 0.1, 0.6),
    ]
    
    for ax, (name, color, vmin, vmax) in zip(axes, bands):
        ax.set_facecolor('#0a0a23')
        
        x = np.linspace(-1, 1, 100)
        y = np.linspace(-1, 1, 100)
        X, Y = np.meshgrid(x, y)
        
        # Different spatial patterns per band
        if 'Alpha' in name:
            Z = 0.8 * np.exp(-((X - 0.0)**2 + (Y + 0.3)**2) / 0.3) + \
                0.3 * np.exp(-((X - 0.0)**2 + (Y - 0.5)**2) / 0.2)
        elif 'Beta' in name:
            Z = 0.5 * np.exp(-((X + 0.3)**2 + (Y + 0.1)**2) / 0.2) + \
                0.5 * np.exp(-((X - 0.3)**2 + (Y + 0.1)**2) / 0.2)
        elif 'Theta' in name:
            Z = 0.6 * np.exp(-((X)**2 + (Y - 0.2)**2) / 0.4)
        else:
            Z = 0.3 * np.exp(-((X)**2 + (Y)**2) / 0.5)
        
        mask = X**2 + Y**2 > 1
        Z[mask] = np.nan
        
        im = ax.imshow(Z, extent=[-1, 1, -1, 1], cmap='RdBu_r',
                       vmin=vmin, vmax=vmax, origin='lower')
        
        theta = np.linspace(0, 2 * np.pi, 100)
        ax.plot(np.cos(theta), np.sin(theta), 'k-', linewidth=1.5)
        ax.plot([0, 0], [0.95, 1.08], 'k-', linewidth=1.5)
        
        ax.set_title(name, color=color, fontsize=10, fontweight='bold')
        ax.axis('off')
        
        cbar = fig.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
        cbar.ax.tick_params(colors='white', labelsize=6)
    
    fig.suptitle('Band Power Topomaps (EEG Scalp Distribution)', 
                 color='white', fontsize=13, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    
    path = os.path.join(OUT_DIR, 'day19_plot_3.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 4: LDA/CSP Feature Importance
# ============================================================
def plot4_feature_importance():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), facecolor='#1a1a2e')
    
    # Left: LDA weight heatmap (channel x time)
    ax1.set_facecolor('#0a0a23')
    n_channels = 16
    n_times = 50
    rng = np.random.RandomState(42)
    times = np.linspace(-0.2, 0.5, n_times)
    
    # Simulate LDA weights with spatial-temporal pattern
    weights = rng.randn(n_channels, n_times) * 0.3
    # C3 and C4 have strong weights around 0.2-0.4s
    weights[4:6, 25:35] += 1.5  # Central channels, post-stimulus
    weights[8:10, 25:35] -= 1.0  # Parietal channels
    
    im = ax1.imshow(weights, aspect='auto', cmap='RdBu_r',
                    extent=[times[0], times[-1], n_channels, 0],
                    vmin=-2, vmax=2)
    ax1.axvline(0, color='white', linestyle=':', alpha=0.5)
    ax1.set_title('LDA Weights (Channel x Time)', color='white', fontsize=11, fontweight='bold')
    ax1.set_xlabel('Time (s)', color='white', fontsize=9)
    ax1.set_ylabel('Channel', color='white', fontsize=9)
    cbar = fig.colorbar(im, ax=ax1, shrink=0.8)
    cbar.ax.tick_params(colors='white', labelsize=7)
    ax1.tick_params(colors='white', labelsize=8)
    for spine in ax1.spines.values():
        spine.set_color('#333')
    
    # Right: CSP pattern topomaps (simulated)
    ax2.set_facecolor('#0a0a23')
    ax2.axis('off')
    
    # Simulate 4 CSP patterns
    csp_patterns = [
        ('CSP 1 (max var)', 0.3, 0.1, 0.15, '#FF5722'),
        ('CSP 2 (max var)', -0.3, 0.1, 0.15, '#FF9800'),
        ('CSP 3 (min var)', 0.0, -0.3, 0.2, '#2196F3'),
        ('CSP 4 (min var)', 0.0, 0.4, 0.12, '#4CAF50'),
    ]
    
    for i, (label, cx, cy, sigma, color) in enumerate(csp_patterns):
        sub_ax = fig.add_axes([0.52 + (i % 2) * 0.22, 0.52 - (i // 2) * 0.38, 0.18, 0.38])
        sub_ax.set_facecolor('#0a0a23')
        
        x = np.linspace(-1, 1, 80)
        y = np.linspace(-1, 1, 80)
        X, Y = np.meshgrid(x, y)
        Z = np.exp(-((X - cx)**2 + (Y - cy)**2) / sigma)
        mask = X**2 + Y**2 > 1
        Z[mask] = np.nan
        
        sub_ax.imshow(Z, extent=[-1, 1, -1, 1], cmap='RdBu_r',
                      vmin=0, vmax=1, origin='lower')
        theta = np.linspace(0, 2 * np.pi, 100)
        sub_ax.plot(np.cos(theta), np.sin(theta), 'k-', linewidth=1)
        sub_ax.set_title(label, fontsize=8, color=color, fontweight='bold')
        sub_ax.axis('off')
    
    ax2.text(0.5, 0.95, 'CSP Spatial Patterns', ha='center', va='top',
             fontsize=12, color='white', fontweight='bold', transform=ax2.transAxes)
    
    path = os.path.join(OUT_DIR, 'day19_plot_4.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


if __name__ == '__main__':
    print("Day 19: Decoding Results & Spectral Topo")
    print("=" * 50)
    plot1_confusion_metrics()
    plot2_itr_curve()
    plot3_band_topomaps()
    plot4_feature_importance()
    print("\n✅ Day 19 所有图表生成完毕!")
