"""
Day 20: Data Export & Report Generation
========================================
Week 6 Day 5 — 数据导出与报告生成
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.gridspec import GridSpec
import os, json

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# Plot 1: Export Format Comparison
# ============================================================
def plot1_export_formats():
    fig, ax = plt.subplots(1, 1, figsize=(14, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis('off')
    ax.set_title('Data Export: Format Selection Guide', fontsize=15, fontweight='bold', pad=15)
    
    formats = [
        (0.3, 4.5, 'FIF\n(.fif)', '#4CAF50', 
         ['MNE native', 'Full metadata', 'Binary, fast', 'MNE only']),
        (3.0, 4.5, 'EDF+\n(.edf)', '#2196F3',
         ['Clinical std', '16-bit precision', 'Cross-tool', 'Widely used']),
        (5.7, 4.5, 'BrainVision\n(.vhdr)', '#FF9800',
         ['EEGLAB compat', 'Multi-file', 'Good precision', 'Research std']),
        (8.4, 4.5, 'CSV\n(.csv)', '#9C27B0',
         ['Universal', 'Excel/R ready', 'No metadata', 'Large files']),
        (11.1, 4.5, 'HDF5\n(.h5)', '#F44336',
         ['Big data', 'Hierarchical', 'Chunked I/O', 'h5py required']),
    ]
    
    for (x, y, label, color, features) in formats:
        rect = FancyBboxPatch((x, y), 2.3, 1.8, boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor='white', alpha=0.85, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 1.15, y + 1.5, label, ha='center', va='center',
                fontsize=10, color='white', fontweight='bold')
        
        for i, feat in enumerate(features):
            ax.text(x + 1.15, y + 0.9 - i * 0.25, feat, ha='center', va='center',
                    fontsize=7, color='white', alpha=0.8)
    
    # Pipeline flow at bottom
    steps = [
        (1.0, 1.0, 'Raw\nData', '#607D8B'),
        (3.5, 1.0, 'Filtered\nData', '#4CAF50'),
        (6.0, 1.0, 'Epochs', '#2196F3'),
        (8.5, 1.0, 'Decoding\nResults', '#FF9800'),
        (11.0, 1.0, 'Report\n(HTML)', '#9C27B0'),
    ]
    
    for i, (x, y, label, color) in enumerate(steps):
        rect = FancyBboxPatch((x, y), 2.0, 0.9, boxstyle="round,pad=0.08",
                              facecolor=color, edgecolor='white', alpha=0.7, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + 1.0, y + 0.45, label, ha='center', va='center',
                fontsize=8, color='white', fontweight='bold')
        
        if i < len(steps) - 1:
            ax.annotate('', xy=(steps[i+1][0], y + 0.45), xytext=(x + 2.0, y + 0.45),
                        arrowprops=dict(arrowstyle='->', color='white', lw=1.5))
    
    ax.text(7.0, 2.3, 'Export Points in Pipeline', ha='center',
            fontsize=10, color='#FFD700', fontstyle='italic')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day20_plot_1.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 2: Export Manager Architecture
# ============================================================
def plot2_export_manager():
    fig, ax = plt.subplots(1, 1, figsize=(14, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis('off')
    ax.set_title('Export Manager: Unified Export Interface', fontsize=15, fontweight='bold', pad=15)
    
    # Central: ExportManager
    center = FancyBboxPatch((4.5, 3.0), 5.0, 1.5, boxstyle="round,pad=0.15",
                            facecolor='#E91E63', edgecolor='white', alpha=0.9, linewidth=2)
    ax.add_patch(center)
    ax.text(7.0, 3.75, 'ExportManager', ha='center', va='center',
            fontsize=13, color='white', fontweight='bold')
    ax.text(7.0, 3.25, 'export_raw() / export_epochs()\nexport_results() / export_plots()',
            ha='center', va='center', fontsize=8, color='white', alpha=0.8)
    
    # Left: Input sources
    inputs = [
        (0.5, 5.5, 'Filtered Raw', '#4CAF50'),
        (0.5, 4.0, 'Epochs Object', '#2196F3'),
        (0.5, 2.5, 'Decoding Metrics', '#FF9800'),
        (0.5, 1.0, 'Figures/Images', '#9C27B0'),
    ]
    
    for (x, y, label, color) in inputs:
        rect = FancyBboxPatch((x, y), 2.5, 0.9, boxstyle="round,pad=0.08",
                              facecolor=color, edgecolor='white', alpha=0.8, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + 1.25, y + 0.45, label, ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
        ax.annotate('', xy=(4.5, 3.75), xytext=(x + 2.5, y + 0.45),
                    arrowprops=dict(arrowstyle='->', color='white', lw=1.5,
                                    connectionstyle='arc3,rad=0.1', alpha=0.6))
    
    # Right: Output formats
    outputs = [
        (11.0, 5.5, '.fif', '#4CAF50'),
        (11.0, 4.5, '.edf', '#2196F3'),
        (11.0, 3.5, '.csv', '#FF9800'),
        (11.0, 2.5, '.json', '#9C27B0'),
        (11.0, 1.5, '.png/.svg', '#F44336'),
        (11.0, 0.5, '.html', '#00BCD4'),
    ]
    
    for (x, y, label, color) in outputs:
        rect = FancyBboxPatch((x, y), 2.0, 0.7, boxstyle="round,pad=0.05",
                              facecolor=color, edgecolor='white', alpha=0.7, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + 1.0, y + 0.35, label, ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
        ax.annotate('', xy=(x, y + 0.35), xytext=(9.5, 3.75),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.5,
                                    connectionstyle='arc3,rad=-0.1', alpha=0.6))
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day20_plot_2.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 3: HTML Report Preview (Simulated)
# ============================================================
def plot3_report_preview():
    fig = plt.figure(figsize=(14, 9), facecolor='#1a1a2e')
    
    # Title bar
    ax_title = fig.add_axes([0.02, 0.94, 0.96, 0.05])
    ax_title.set_facecolor('#0f3460')
    ax_title.text(0.5, 0.5, 'BCI Analysis Report — Generated 2026-05-26',
                  ha='center', va='center', fontsize=13, color='white', fontweight='bold')
    ax_title.axis('off')
    
    # Section 1: Data Overview
    ax1 = fig.add_axes([0.05, 0.75, 0.90, 0.17])
    ax1.set_facecolor('#16213e')
    ax1.axis('off')
    ax1.text(0.02, 0.9, '1. Data Overview', fontsize=12, color='#4CAF50', 
             fontweight='bold', transform=ax1.transAxes)
    overview_items = [
        'Channels: 16 EEG + 2 EOG',
        'Sampling Rate: 256 Hz',
        'Duration: 277.3 s',
        'Events: 284 (Left: 142, Right: 142)',
    ]
    for i, item in enumerate(overview_items):
        ax1.text(0.05 + (i % 2) * 0.45, 0.6 - (i // 2) * 0.3, item,
                fontsize=9, color='white', transform=ax1.transAxes)
    
    # Section 2: Preprocessing
    ax2 = fig.add_axes([0.05, 0.52, 0.90, 0.20])
    ax2.set_facecolor('#16213e')
    ax2.axis('off')
    ax2.text(0.02, 0.9, '2. Preprocessing', fontsize=12, color='#2196F3',
             fontweight='bold', transform=ax2.transAxes)
    preproc_items = [
        'Bandpass: 1-40 Hz (FIR)',
        'Notch: 50 Hz + 100 Hz',
        'Re-reference: Average',
        'Bad channels: 0',
    ]
    for i, item in enumerate(preproc_items):
        ax2.text(0.05 + (i % 2) * 0.45, 0.6 - (i // 2) * 0.3, item,
                fontsize=9, color='white', transform=ax2.transAxes)
    
    # Simulated filter effect plot
    ax_filt = fig.add_axes([0.55, 0.54, 0.38, 0.14])
    ax_filt.set_facecolor('#0a0a23')
    fs = 256
    freqs = np.linspace(0.5, 80, 200)
    psd_raw = 1.0 / (1 + ((freqs - 10) / 3)**2) + 0.5 / (1 + ((freqs - 50) / 2)**2)
    psd_filt = 1.0 / (1 + ((freqs - 10) / 3)**2)
    psd_filt[freqs < 1] = 0.01
    psd_filt[freqs > 40] *= 0.01
    psd_filt[np.abs(freqs - 50) < 1] = 0.01
    ax_filt.semilogy(freqs, psd_raw + 0.001, color='#4CAF50', alpha=0.5, linewidth=0.8)
    ax_filt.semilogy(freqs, psd_filt + 0.001, color='#2196F3', linewidth=0.8)
    ax_filt.set_xlim(0, 80)
    ax_filt.tick_params(colors='white', labelsize=6)
    ax_filt.set_title('PSD: Raw vs Filtered', color='white', fontsize=8)
    for spine in ax_filt.spines.values():
        spine.set_color('#333')
    
    # Section 3: Decoding Results
    ax3 = fig.add_axes([0.05, 0.26, 0.90, 0.23])
    ax3.set_facecolor('#16213e')
    ax3.axis('off')
    ax3.text(0.02, 0.9, '3. Decoding Results', fontsize=12, color='#FF9800',
             fontweight='bold', transform=ax3.transAxes)
    
    # Results table
    result_data = [
        ['Metric', 'Value'],
        ['Accuracy', '85.2%'],
        ['Cohen\'s Kappa', '0.778'],
        ['ITR', '62.3 bits/min'],
        ['CV Score', '83.7% +/- 3.2%'],
    ]
    for i, row in enumerate(result_data):
        for j, cell in enumerate(row):
            color = '#FFD700' if i == 0 else 'white'
            weight = 'bold' if i == 0 else 'normal'
            ax3.text(0.05 + j * 0.25, 0.7 - i * 0.15, cell,
                    fontsize=9, color=color, fontweight=weight,
                    transform=ax3.transAxes)
    
    # Mini confusion matrix
    ax_cm = fig.add_axes([0.60, 0.30, 0.30, 0.16])
    ax_cm.set_facecolor('#0a0a23')
    cm = np.array([[45, 5], [6, 44]])
    cm_norm = cm / cm.sum(axis=1, keepdims=True)
    im = ax_cm.imshow(cm_norm, cmap='Blues', vmin=0, vmax=1)
    for i in range(2):
        for j in range(2):
            color = 'white' if cm_norm[i, j] > 0.5 else 'black'
            ax_cm.text(j, i, str(cm[i, j]), ha='center', va='center',
                      color=color, fontsize=10, fontweight='bold')
    ax_cm.set_xticks([0, 1])
    ax_cm.set_yticks([0, 1])
    ax_cm.set_xticklabels(['Left', 'Right'], fontsize=7, color='white')
    ax_cm.set_yticklabels(['Left', 'Right'], fontsize=7, color='white')
    ax_cm.set_xlabel('Predicted', fontsize=7, color='white')
    ax_cm.set_ylabel('Actual', fontsize=7, color='white')
    ax_cm.set_title('Confusion Matrix', color='white', fontsize=8)
    ax_cm.tick_params(colors='white', labelsize=6)
    
    # Footer
    ax_footer = fig.add_axes([0.02, 0.02, 0.96, 0.04])
    ax_footer.set_facecolor('#0f3460')
    ax_footer.text(0.5, 0.5, 'Generated by BCI Data Analysis Tool v1.0 | Config: bci_config.yaml',
                  ha='center', va='center', fontsize=8, color='#aaa')
    ax_footer.axis('off')
    
    path = os.path.join(OUT_DIR, 'day20_plot_3.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 4: Reproducible Pipeline (Config-driven)
# ============================================================
def plot4_reproducible_pipeline():
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')
    ax.set_title('Reproducible Pipeline: Config-Driven One-Click Analysis', 
                 fontsize=14, fontweight='bold', pad=15)
    
    # Config file at top
    config_rect = FancyBboxPatch((3.5, 6.5), 7, 1.0, boxstyle="round,pad=0.1",
                                  facecolor='#FFD700', edgecolor='white', alpha=0.9, linewidth=2)
    ax.add_patch(config_rect)
    ax.text(7.0, 7.0, 'bci_config.yaml', ha='center', va='center',
            fontsize=12, color='#1a1a2e', fontweight='bold')
    
    # Pipeline steps
    steps = [
        (0.5, 4.5, '1. Load\nRaw Data', '#4CAF50', 'data_path: eeg_raw.fif'),
        (3.5, 4.5, '2. Bandpass\n+ Notch', '#2196F3', 'l_freq: 1, h_freq: 40'),
        (6.5, 4.5, '3. Extract\nEpochs', '#FF9800', 'tmin: -0.2, tmax: 0.5'),
        (9.5, 4.5, '4. Decode\n(LDA/SVM)', '#9C27B0', 'method: lda, cv: 5'),
        (12.0, 4.5, '5. Export\n+ Report', '#F44336', 'formats: [fif,json,html]'),
    ]
    
    for i, (x, y, label, color, cfg) in enumerate(steps):
        rect = FancyBboxPatch((x, y), 2.5, 1.2, boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor='white', alpha=0.85, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 1.25, y + 0.85, label, ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
        ax.text(x + 1.25, y + 0.25, cfg, ha='center', va='center',
                fontsize=7, color='white', alpha=0.7)
        
        if i < len(steps) - 1:
            ax.annotate('', xy=(steps[i+1][0], y + 0.6), xytext=(x + 2.5, y + 0.6),
                        arrowprops=dict(arrowstyle='->', color='white', lw=2))
    
    # Arrow from config to pipeline
    ax.annotate('', xy=(7.0, 5.7), xytext=(7.0, 6.5),
                arrowprops=dict(arrowstyle='->', color='#FFD700', lw=2.5))
    
    # Output files at bottom
    outputs = [
        (1.0, 1.5, 'filtered_raw.fif', '#4CAF50'),
        (4.0, 1.5, 'epochs.fif', '#2196F3'),
        (7.0, 1.5, 'results.json', '#FF9800'),
        (10.0, 1.5, 'report.html', '#9C27B0'),
    ]
    
    ax.text(7.0, 2.8, 'Output Files', ha='center', fontsize=11, 
            color='#FFD700', fontstyle='italic')
    
    for (x, y, label, color) in outputs:
        rect = FancyBboxPatch((x, y), 2.5, 0.8, boxstyle="round,pad=0.05",
                              facecolor=color, edgecolor='white', alpha=0.6, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + 1.25, y + 0.4, label, ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
    
    # One-click command
    cmd_rect = FancyBboxPatch((3.0, 0.2), 8, 0.8, boxstyle="round,pad=0.08",
                               facecolor='#333', edgecolor='#4CAF50', alpha=0.9, linewidth=2)
    ax.add_patch(cmd_rect)
    ax.text(7.0, 0.6, 'pipeline.run("bci_config.yaml")  # One command, full pipeline',
            ha='center', va='center', fontsize=10, color='#4CAF50', fontweight='bold',
            fontfamily='monospace')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day20_plot_4.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


if __name__ == '__main__':
    print("Day 20: Data Export & Report Generation")
    print("=" * 50)
    plot1_export_formats()
    plot2_export_manager()
    plot3_report_preview()
    plot4_reproducible_pipeline()
    print("\n✅ Day 20 所有图表生成完毕!")
