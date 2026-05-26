"""
Day 21: Modular Design & Configuration Management
===================================================
Week 7 Day 1 — 模块化设计与配置管理
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.gridspec import GridSpec
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# Plot 1: Module Architecture Diagram
# ============================================================
def plot1_module_architecture():
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')
    ax.set_title('Modular BCI Pipeline Architecture', fontsize=15, fontweight='bold', pad=15)
    
    # Pipeline orchestrator (center)
    center = FancyBboxPatch((4.0, 3.5), 6.0, 1.5, boxstyle="round,pad=0.15",
                             facecolor='#E91E63', edgecolor='white', alpha=0.9, linewidth=2.5)
    ax.add_patch(center)
    ax.text(7.0, 4.25, 'BCIPipeline\n(Orchestrator)', ha='center', va='center',
            fontsize=12, color='white', fontweight='bold')
    
    # Modules (left column: input, right: output)
    modules = [
        (0.3, 6.0, 'ConfigManager\n(YAML/dataclass)', '#FFD700', 'config.yaml'),
        (0.3, 4.0, 'DataLoader\n(MNE/EEGLAB)', '#4CAF50', '.fif / .edf'),
        (0.3, 2.0, 'Preprocessor\n(Filter/Notch/ICA)', '#2196F3', 'Raw -> Raw'),
        (0.3, 0.3, 'Epocher\n(Events/Epochs)', '#FF9800', 'Raw -> Epochs'),
    ]
    
    outputs = [
        (10.5, 6.0, 'Decoder\n(LDA/SVM/CSP)', '#9C27B0', 'Accuracy/ITR'),
        (10.5, 4.0, 'Exporter\n(FIF/CSV/JSON)', '#00BCD4', 'Output files'),
        (10.5, 2.0, 'Reporter\n(HTML/Sphinx)', '#795548', 'report.html'),
        (10.5, 0.3, 'PipelineData\n(Data Container)', '#607D8B', 'All results'),
    ]
    
    for (x, y, label, color, desc) in modules:
        rect = FancyBboxPatch((x, y), 3.2, 1.2, boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor='white', alpha=0.85, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 1.6, y + 0.75, label, ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
        ax.text(x + 1.6, y + 0.25, desc, ha='center', va='center',
                fontsize=7, color='white', alpha=0.8)
        # Arrow to center
        ax.annotate('', xy=(4.0, 4.25), xytext=(x + 3.2, y + 0.6),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.5,
                                    connectionstyle='arc3,rad=0.1', alpha=0.6))
    
    for (x, y, label, color, desc) in outputs:
        rect = FancyBboxPatch((x, y), 3.2, 1.2, boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor='white', alpha=0.85, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 1.6, y + 0.75, label, ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
        ax.text(x + 1.6, y + 0.25, desc, ha='center', va='center',
                fontsize=7, color='white', alpha=0.8)
        # Arrow from center
        ax.annotate('', xy=(x, y + 0.6), xytext=(10.0, 4.25),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.5,
                                    connectionstyle='arc3,rad=-0.1', alpha=0.6))
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day21_plot_1.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 2: Data Flow Through Pipeline
# ============================================================
def plot2_data_flow():
    fig, ax = plt.subplots(1, 1, figsize=(14, 6))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis('off')
    ax.set_title('PipelineData Flow: From Raw to Results', fontsize=15, fontweight='bold', pad=15)
    
    steps = [
        (0.5, 2.5, 'Raw\n(.fif)', '#4CAF50', '16 ch\n256 Hz\n277s'),
        (3.0, 2.5, 'Filtered\nRaw', '#2196F3', '1-40 Hz\n+Notch 50Hz'),
        (5.5, 2.5, 'Events\n(Nx3)', '#FF9800', '284 events\n2 classes'),
        (8.0, 2.5, 'Epochs\n(MNE)', '#9C27B0', '268 valid\n16 rejected'),
        (10.5, 2.5, 'Scores\n(dict)', '#F44336', 'Acc: 85%\nITR: 62'),
        (12.5, 2.5, 'Report\n(HTML)', '#00BCD4', 'Full analysis'),
    ]
    
    for i, (x, y, label, color, desc) in enumerate(steps):
        rect = FancyBboxPatch((x, y), 2.0, 2.0, boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor='white', alpha=0.85, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 1.0, y + 1.4, label, ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
        ax.text(x + 1.0, y + 0.5, desc, ha='center', va='center',
                fontsize=7, color='white', alpha=0.8)
        
        if i < len(steps) - 1:
            ax.annotate('', xy=(steps[i+1][0], y + 1.0), xytext=(x + 2.0, y + 1.0),
                        arrowprops=dict(arrowstyle='->', color='white', lw=2.5))
    
    # Data container label
    ax.text(7.0, 5.2, 'PipelineData: shared data container across all modules',
            ha='center', fontsize=11, color='#FFD700', fontstyle='italic')
    
    # Method labels on arrows
    methods = ['load()', 'process()', 'find_events()', 'extract()', 'decode()']
    for i, method in enumerate(methods):
        x_mid = steps[i][0] + 2.5
        ax.text(x_mid, 4.5, method, ha='center', fontsize=8, color='#aaa')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day21_plot_2.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 3: Config Management Architecture
# ============================================================
def plot3_config_management():
    fig, ax = plt.subplots(1, 1, figsize=(14, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis('off')
    ax.set_title('Configuration Management: YAML ↔ Dataclass ↔ Validation', 
                 fontsize=14, fontweight='bold', pad=15)
    
    # YAML file (left)
    yaml_rect = FancyBboxPatch((0.5, 2.0), 3.5, 3.5, boxstyle="round,pad=0.15",
                                facecolor='#FFD700', edgecolor='white', alpha=0.9, linewidth=2)
    ax.add_patch(yaml_rect)
    ax.text(2.25, 5.0, 'bci_config.yaml', ha='center', va='center',
            fontsize=11, color='#1a1a2e', fontweight='bold')
    yaml_lines = [
        'filter:',
        '  l_freq: 1.0',
        '  h_freq: 40.0',
        '  notch_freqs: [50, 100]',
        'epoch:',
        '  tmin: -0.2',
        '  tmax: 0.5',
        'decode:',
        '  method: lda',
        '  cv_folds: 5',
    ]
    for i, line in enumerate(yaml_lines):
        ax.text(1.0, 4.3 - i * 0.22, line, fontsize=7, color='#1a1a2e',
                fontfamily='monospace')
    
    # Dataclass (center)
    dc_rect = FancyBboxPatch((5.0, 1.5), 4.0, 4.5, boxstyle="round,pad=0.15",
                              facecolor='#2196F3', edgecolor='white', alpha=0.9, linewidth=2)
    ax.add_patch(dc_rect)
    ax.text(7.0, 5.5, 'PipelineConfig', ha='center', va='center',
            fontsize=12, color='white', fontweight='bold')
    dc_lines = [
        '@dataclass',
        'class PipelineConfig:',
        '  filter: FilterConfig',
        '  epoch: EpochConfig',
        '  decode: DecodeConfig',
        '  output_dir: str',
        '',
        '  def validate(self):',
        '    # Type-safe checks',
        '    # Range validation',
        '    # Cross-field checks',
    ]
    for i, line in enumerate(dc_lines):
        ax.text(5.5, 4.8 - i * 0.22, line, fontsize=7, color='white',
                fontfamily='monospace')
    
    # Validation (right)
    val_rect = FancyBboxPatch((10.0, 1.5), 3.5, 4.5, boxstyle="round,pad=0.15",
                               facecolor='#4CAF50', edgecolor='white', alpha=0.9, linewidth=2)
    ax.add_patch(val_rect)
    ax.text(11.75, 5.5, 'Validation', ha='center', va='center',
            fontsize=12, color='white', fontweight='bold')
    val_lines = [
        'l_freq < h_freq     OK',
        'l_freq > 0          OK',
        'tmin < tmax         OK',
        'cv_folds >= 2       OK',
        '',
        'Error checks:',
        '  l_freq >= h_freq?',
        '  negative freq?',
        '  tmin >= tmax?',
    ]
    for i, line in enumerate(val_lines):
        color = '#4CAF50' if 'OK' in line else 'white'
        ax.text(10.5, 4.8 - i * 0.22, line, fontsize=7, color=color,
                fontfamily='monospace')
    
    # Arrows
    ax.annotate('', xy=(5.0, 3.75), xytext=(4.0, 3.75),
                arrowprops=dict(arrowstyle='->', color='white', lw=2.5))
    ax.text(4.5, 4.1, 'from_yaml()', ha='center', fontsize=8, color='white')
    
    ax.annotate('', xy=(10.0, 3.75), xytext=(9.0, 3.75),
                arrowprops=dict(arrowstyle='->', color='white', lw=2.5))
    ax.text(9.5, 4.1, 'validate()', ha='center', fontsize=8, color='white')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day21_plot_3.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 4: Before vs After Refactoring
# ============================================================
def plot4_before_after_refactor():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), facecolor='#1a1a2e')
    
    # Left: Monolithic (before)
    ax1.set_xlim(0, 6)
    ax1.set_ylim(0, 8)
    ax1.axis('off')
    ax1.set_title('Before: Monolithic Script', color='#F44336', fontsize=13, fontweight='bold')
    
    mono_rect = FancyBboxPatch((0.5, 0.5), 5.0, 7.0, boxstyle="round,pad=0.1",
                                facecolor='#F44336', edgecolor='white', alpha=0.3, linewidth=2)
    ax1.add_patch(mono_rect)
    
    mono_code = [
        'import mne, numpy as np',
        'from sklearn...',
        '',
        '# ALL IN ONE FILE:',
        'raw = mne.io.read_raw_fif(...)',
        'raw.filter(1, 40)',
        'raw.notch_filter([50])',
        'events = mne.find_events(raw)',
        'epochs = mne.Epochs(...)',
        'X = epochs.get_data()',
        'clf = LDA()',
        'scores = cross_val_score(...)',
        'print(scores)',
        '',
        '# 200 lines, no structure',
        '# Hard to reuse, hard to test',
    ]
    for i, line in enumerate(mono_code):
        ax1.text(0.8, 7.0 - i * 0.4, line, fontsize=7, color='white',
                fontfamily='monospace', alpha=0.8)
    
    # Right: Modular (after)
    ax2.set_xlim(0, 7)
    ax2.set_ylim(0, 8)
    ax2.axis('off')
    ax2.set_title('After: Modular Pipeline', color='#4CAF50', fontsize=13, fontweight='bold')
    
    modules = [
        (0.5, 6.5, 'config.py', '#FFD700', 'PipelineConfig\nFilterConfig\nEpochConfig'),
        (3.5, 6.5, 'loader.py', '#4CAF50', 'MNEDataLoader\nEEGLABLoader'),
        (0.5, 4.0, 'preprocessor.py', '#2196F3', 'Preprocessor\nbandpass/notch/ICA'),
        (3.5, 4.0, 'epocher.py', '#FF9800', 'Epocher\nextract/reject'),
        (0.5, 1.5, 'decoder.py', '#9C27B0', 'Decoder\nLDA/SVM/CSP'),
        (3.5, 1.5, 'pipeline.py', '#E91E63', 'BCIPipeline\nrun() -> Results'),
    ]
    
    for (x, y, name, color, desc) in modules:
        rect = FancyBboxPatch((x, y), 2.5, 1.8, boxstyle="round,pad=0.08",
                              facecolor=color, edgecolor='white', alpha=0.8, linewidth=1.5)
        ax2.add_patch(rect)
        ax2.text(x + 1.25, y + 1.35, name, ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
        ax2.text(x + 1.25, y + 0.6, desc, ha='center', va='center',
                fontsize=7, color='white', alpha=0.8)
    
    # Benefits
    ax2.text(6.0, 7.0, 'Benefits:', fontsize=9, color='#4CAF50', fontweight='bold')
    benefits = ['Single Responsibility', 'Easy to test', 'Configurable',
                'Reusable', 'Type-safe', 'Documented']
    for i, b in enumerate(benefits):
        ax2.text(6.0, 6.3 - i * 0.5, f'+ {b}', fontsize=7, color='white')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day21_plot_4.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


if __name__ == '__main__':
    print("Day 21: Modular Design & Configuration")
    print("=" * 50)
    plot1_module_architecture()
    plot2_data_flow()
    plot3_config_management()
    plot4_before_after_refactor()
    print("\n✅ Day 21 所有图表生成完毕!")
