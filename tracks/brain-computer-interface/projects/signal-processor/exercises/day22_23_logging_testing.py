"""
Day 22-23: Logging, Exceptions, and Testing
============================================
Week 7 Day 2-3 — 日志/异常处理 + 单元测试
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
# Plot 1 (Day22): Logging Levels & Architecture
# ============================================================
def plot1_logging_architecture():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), facecolor='#1a1a2e',
                                    gridspec_kw={'width_ratios': [1, 1.2]})
    
    # Left: Log levels
    ax1.set_xlim(0, 6)
    ax1.set_ylim(0, 8)
    ax1.axis('off')
    ax1.set_title('Log Levels', color='white', fontsize=13, fontweight='bold')
    
    levels = [
        ('DEBUG', '#607D8B', 'Filter coefficients: b=[0.1, 0.2]', 0.6),
        ('INFO', '#4CAF50', 'Loaded 16 channels, 256Hz, 277.3s', 0.5),
        ('WARNING', '#FF9800', 'Channel Fp1 has high impedance', 0.4),
        ('ERROR', '#F44336', 'ICA failed to converge', 0.25),
        ('CRITICAL', '#9C27B0', 'Cannot connect to amplifier', 0.1),
    ]
    
    for i, (level, color, example, width_ratio) in enumerate(levels):
        y = 6.5 - i * 1.3
        w = 5.0 * width_ratio + 1.5
        rect = FancyBboxPatch((0.5, y), w, 0.9, boxstyle="round,pad=0.05",
                              facecolor=color, edgecolor='white', alpha=0.85, linewidth=2)
        ax1.add_patch(rect)
        ax1.text(0.8, y + 0.55, level, fontsize=10, color='white', fontweight='bold', va='center')
        ax1.text(3.5, y + 0.3, example, fontsize=7, color='white', alpha=0.8, va='center')
    
    # Right: Logging architecture
    ax2.set_xlim(0, 8)
    ax2.set_ylim(0, 8)
    ax2.axis('off')
    ax2.set_title('Logging Architecture', color='white', fontsize=13, fontweight='bold')
    
    # Module loggers
    loggers = [
        (0.5, 6.5, 'bci.loader', '#4CAF50'),
        (0.5, 5.0, 'bci.preprocessor', '#2196F3'),
        (0.5, 3.5, 'bci.epocher', '#FF9800'),
        (0.5, 2.0, 'bci.decoder', '#9C27B0'),
    ]
    
    for (x, y, name, color) in loggers:
        rect = FancyBboxPatch((x, y), 3.0, 0.9, boxstyle="round,pad=0.05",
                              facecolor=color, edgecolor='white', alpha=0.8, linewidth=1.5)
        ax2.add_patch(rect)
        ax2.text(x + 1.5, y + 0.45, name, ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
    
    # Handlers
    handlers = [
        (5.0, 6.0, 'Console\nHandler', '#607D8B'),
        (5.0, 4.0, 'File\nHandler', '#00BCD4'),
        (5.0, 2.0, 'JSON\nHandler', '#795548'),
    ]
    
    for (x, y, label, color) in handlers:
        rect = FancyBboxPatch((x, y), 2.5, 1.2, boxstyle="round,pad=0.08",
                              facecolor=color, edgecolor='white', alpha=0.7, linewidth=1.5)
        ax2.add_patch(rect)
        ax2.text(x + 1.25, y + 0.6, label, ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
    
    # Arrows from loggers to handlers
    for (_, yl, _, _) in loggers:
        for (_, yh, _, _) in handlers:
            ax2.annotate('', xy=(5.0, yh + 0.6), xytext=(3.5, yl + 0.45),
                        arrowprops=dict(arrowstyle='->', color='white', lw=1, alpha=0.4))
    
    ax2.text(4.25, 7.5, 'All loggers feed into shared handlers',
            ha='center', fontsize=9, color='#FFD700', fontstyle='italic')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day22_plot_1.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 2 (Day22): Exception Hierarchy + Graceful Degradation
# ============================================================
def plot2_exception_degradation():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), facecolor='#1a1a2e')
    
    # Left: Exception hierarchy
    ax1.set_xlim(0, 7)
    ax1.set_ylim(0, 8)
    ax1.axis('off')
    ax1.set_title('Custom Exception Hierarchy', color='white', fontsize=12, fontweight='bold')
    
    exc_tree = [
        (2.5, 7.0, 'BCIPipelineError', '#E91E63', 2.5),
        (0.5, 5.2, 'DataLoadError', '#F44336', 2.0),
        (4.0, 5.2, 'PreprocessError', '#FF9800', 2.0),
        (0.5, 3.4, 'EpochError', '#2196F3', 2.0),
        (4.0, 3.4, 'DecodeError', '#9C27B0', 2.0),
        (4.0, 1.6, 'FilterError', '#FF5722', 2.0),
    ]
    
    for (x, y, label, color, w) in exc_tree:
        rect = FancyBboxPatch((x, y), w, 0.8, boxstyle="round,pad=0.05",
                              facecolor=color, edgecolor='white', alpha=0.85, linewidth=1.5)
        ax1.add_patch(rect)
        ax1.text(x + w/2, y + 0.4, label, ha='center', va='center',
                fontsize=8, color='white', fontweight='bold')
    
    # Hierarchy arrows
    ax1.annotate('', xy=(2.5, 7.0), xytext=(1.5, 6.0),
                arrowprops=dict(arrowstyle='->', color='white', lw=1.5))
    ax1.annotate('', xy=(3.75, 7.0), xytext=(5.0, 6.0),
                arrowprops=dict(arrowstyle='->', color='white', lw=1.5))
    ax1.annotate('', xy=(5.0, 5.2), xytext=(5.0, 4.2),
                arrowprops=dict(arrowstyle='->', color='white', lw=1.5))
    
    # Right: Graceful degradation flowchart
    ax2.set_xlim(0, 7)
    ax2.set_ylim(0, 8)
    ax2.axis('off')
    ax2.set_title('Graceful Degradation Strategy', color='white', fontsize=12, fontweight='bold')
    
    steps = [
        (1.5, 7.0, 'Full Pipeline\n(ICA + Filter)', '#4CAF50'),
        (1.5, 5.2, 'No ICA\n(Filter only)', '#FF9800'),
        (1.5, 3.4, 'Minimal\n(No reject)', '#F44336'),
        (1.5, 1.6, 'Return raw\nresults only', '#9E9E9E'),
    ]
    
    for i, (x, y, label, color) in enumerate(steps):
        rect = FancyBboxPatch((x, y), 3.5, 1.0, boxstyle="round,pad=0.08",
                              facecolor=color, edgecolor='white', alpha=0.8, linewidth=1.5)
        ax2.add_patch(rect)
        ax2.text(x + 1.75, y + 0.5, label, ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
        
        if i < len(steps) - 1:
            ax2.annotate('', xy=(3.25, steps[i+1][1] + 1.0), xytext=(3.25, y),
                        arrowprops=dict(arrowstyle='->', color='white', lw=1.5))
            ax2.text(5.5, y - 0.5, 'Fallback\nif error', fontsize=7, 
                    color='#FF9800', ha='center', fontstyle='italic')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day22_plot_2.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 3 (Day23): Test Pyramid + Coverage
# ============================================================
def plot3_test_pyramid():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), facecolor='#1a1a2e')
    
    # Left: Test pyramid
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 8)
    ax1.axis('off')
    ax1.set_title('Test Pyramid', color='white', fontsize=13, fontweight='bold')
    
    # Pyramid layers
    layers = [
        (1.0, 0.5, 8.0, 2.0, 'Unit Tests (fast, many)', '#4CAF50', 
         ['test_bandpass()', 'test_notch()', 'test_config_validate()', 
          'test_baseline_correction()']),
        (2.0, 2.5, 6.0, 2.0, 'Integration Tests (medium)', '#2196F3',
         ['test_preprocessor_epocher()', 'test_loader_preprocessor()']),
        (3.0, 4.5, 4.0, 2.0, 'E2E Tests (slow, few)', '#FF9800',
         ['test_full_pipeline()']),
    ]
    
    for (x, y, w, h, label, color, examples) in layers:
        # Trapezoid approximation
        from matplotlib.patches import Polygon
        pts = np.array([
            [x, y], [x + w, y],
            [x + w - 0.5, y + h], [x + 0.5, y + h]
        ])
        poly = Polygon(pts, facecolor=color, edgecolor='white', alpha=0.7, linewidth=2)
        ax1.add_patch(poly)
        ax1.text(x + w/2, y + h - 0.4, label, ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
        for i, ex in enumerate(examples):
            ax1.text(x + w/2, y + h - 0.8 - i * 0.3, ex, ha='center', 
                    fontsize=7, color='white', alpha=0.8)
    
    # Right: Coverage chart
    ax2.set_facecolor('#0a0a23')
    modules = ['config', 'loader', 'preprocessor', 'epocher', 'decoder', 'exporter', 'pipeline']
    coverage = [95, 88, 92, 85, 90, 78, 82]
    colors = ['#4CAF50' if c >= 90 else '#FF9800' if c >= 80 else '#F44336' for c in coverage]
    
    bars = ax2.barh(modules, coverage, color=colors, alpha=0.8, edgecolor='white', linewidth=0.5)
    ax2.axvline(80, color='#FF9800', linestyle='--', alpha=0.5, linewidth=1, label='80% target')
    ax2.axvline(90, color='#4CAF50', linestyle='--', alpha=0.5, linewidth=1, label='90% ideal')
    
    for bar, val in zip(bars, coverage):
        ax2.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f'{val}%', va='center', fontsize=9, color='white', fontweight='bold')
    
    ax2.set_xlabel('Coverage (%)', color='white', fontsize=10)
    ax2.set_title('Test Coverage by Module', color='white', fontsize=12, fontweight='bold')
    ax2.set_xlim(0, 105)
    ax2.legend(fontsize=8, facecolor='#0a0a23', edgecolor='#444', labelcolor='white')
    ax2.tick_params(colors='white', labelsize=9)
    for spine in ax2.spines.values():
        spine.set_color('#333')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day23_plot_1.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 4 (Day23): pytest Examples + Mock Strategy
# ============================================================
def plot4_pytest_mock():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), facecolor='#1a1a2e')
    
    # Left: pytest features
    ax1.set_xlim(0, 7)
    ax1.set_ylim(0, 8)
    ax1.axis('off')
    ax1.set_title('pytest Key Features', color='white', fontsize=12, fontweight='bold')
    
    features = [
        ('@pytest.fixture', 'Shared test data setup', '#4CAF50',
         'def sample_data():\n    return create_synthetic_eeg()'),
        ('@pytest.mark.parametrize', 'Multi-input testing', '#2196F3',
         '@parametrize("l_freq,h_freq",\n  [(1,40), (0.5,100)])'),
        ('unittest.mock', 'Isolate dependencies', '#FF9800',
         'mock = MagicMock()\nmock.load.return_value = ...'),
        ('pytest.raises', 'Exception testing', '#F44336',
         'with raises(ValueError):\n    config.validate()'),
        ('pytest-cov', 'Coverage reports', '#9C27B0',
         'pytest --cov=bci\n--cov-report=html'),
    ]
    
    for i, (name, desc, color, code) in enumerate(features):
        y = 7.0 - i * 1.5
        rect = FancyBboxPatch((0.3, y - 0.5), 6.4, 1.2, boxstyle="round,pad=0.08",
                              facecolor=color, edgecolor='white', alpha=0.6, linewidth=1.5)
        ax1.add_patch(rect)
        ax1.text(0.6, y + 0.4, name, fontsize=9, color='white', fontweight='bold')
        ax1.text(0.6, y + 0.0, desc, fontsize=7, color='white', alpha=0.8)
        ax1.text(3.5, y - 0.3, code, fontsize=6, color='white', alpha=0.7, fontfamily='monospace')
    
    # Right: Mock strategy diagram
    ax2.set_xlim(0, 7)
    ax2.set_ylim(0, 8)
    ax2.axis('off')
    ax2.set_title('Mock Strategy: Test in Isolation', color='white', fontsize=12, fontweight='bold')
    
    # Test subject
    test_rect = FancyBboxPatch((2.0, 5.5), 3.0, 1.0, boxstyle="round,pad=0.1",
                                facecolor='#E91E63', edgecolor='white', alpha=0.9, linewidth=2)
    ax2.add_patch(test_rect)
    ax2.text(3.5, 6.0, 'Unit Under Test\n(e.g. Preprocessor)', ha='center', va='center',
            fontsize=9, color='white', fontweight='bold')
    
    # Mock dependencies
    mocks = [
        (0.3, 3.0, 'Mock\nDataLoader', '#4CAF50'),
        (2.5, 3.0, 'Mock\nRaw object', '#2196F3'),
        (4.7, 3.0, 'Mock\nLogger', '#FF9800'),
    ]
    
    for (x, y, label, color) in mocks:
        rect = FancyBboxPatch((x, y), 2.0, 1.0, boxstyle="round,pad=0.08",
                              facecolor=color, edgecolor='white', alpha=0.7, linewidth=1.5)
        ax2.add_patch(rect)
        ax2.text(x + 1.0, y + 0.5, label, ha='center', va='center',
                fontsize=8, color='white', fontweight='bold')
        ax2.annotate('', xy=(3.5, 5.5), xytext=(x + 1.0, y + 1.0),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.5, alpha=0.6))
    
    # Real assertion
    assert_rect = FancyBboxPatch((1.5, 1.0), 4.0, 1.0, boxstyle="round,pad=0.08",
                                  facecolor='#4CAF50', edgecolor='white', alpha=0.8, linewidth=1.5)
    ax2.add_patch(assert_rect)
    ax2.text(3.5, 1.5, 'assert result.shape == expected\nassert power_50hz < threshold',
            ha='center', va='center', fontsize=7, color='white', fontfamily='monospace')
    
    ax2.annotate('', xy=(3.5, 2.0), xytext=(3.5, 3.0),
                arrowprops=dict(arrowstyle='->', color='white', lw=1.5))
    ax2.text(3.5, 2.6, 'verify output', fontsize=7, color='#4CAF50', ha='center')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day23_plot_2.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


if __name__ == '__main__':
    print("Day 22-23: Logging, Exceptions & Testing")
    print("=" * 50)
    plot1_logging_architecture()
    plot2_exception_degradation()
    plot3_test_pyramid()
    plot4_pytest_mock()
    print("\n✅ Day 22-23 所有图表生成完毕!")
