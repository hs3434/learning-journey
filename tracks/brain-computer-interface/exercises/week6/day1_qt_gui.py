"""
Day 16: Qt GUI Architecture for BCI — Static Architecture Diagrams
(Docker has no display server — generate architecture diagrams instead)

Topics:
1. Qt signal-slot mechanism visualization
2. BCI Viewer layout design
3. Thread model — UI thread vs worker threads
4. MVC architecture for BCI
5. Data flow pipeline: acquisition → processing → display

Note: Actual running Qt code is in projects/bci/gui/__init__.py
This exercise demonstrates Qt concepts through diagrams since we can't run GUI in Docker.
"""

import matplotlib
matplotlib.use('Agg')
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import warnings
warnings.filterwarnings('ignore')

SAVE_DIR = '/workspace/learning-journey/tracks/brain-computer-interface/projects/signal-processor/exercises/'
np.random.seed(42)

# ============================================================
# Plot 1: Qt Signal-Slot Mechanism
# ============================================================
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14); ax.set_ylim(0, 10); ax.axis('off')

# Sender objects
senders = [
    ('Button\n"Load Data"', 1.0, 8.0, '#FFCCBC'),
    ('Slider\n"Filter Freq"', 1.0, 6.0, '#C8E6C9'),
    ('Timer\n"100ms tick"', 1.0, 4.0, '#BBDEFB'),
    ('Worker\n"data_loaded"', 1.0, 2.0, '#FFF9C4'),
]

for name, x, y, color in senders:
    rect = FancyBboxPatch((x, y-0.7), 2.5, 1.4, boxstyle="round,pad=0.1",
                          facecolor=color, edgecolor='#333', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x+1.25, y, name, ha='center', va='center', fontsize=9, fontweight='bold')

# Signal arrow area
for _, x, y, _ in senders:
    ax.annotate('', xy=(5.5, y), xytext=(3.5, y),
                arrowprops=dict(arrowstyle='->', color='#E53935', lw=2))
    ax.text(4.5, y+0.3, 'signal', ha='center', fontsize=7, color='#E53935', style='italic')

# Central signal bus
rect = FancyBboxPatch((5.5, 1.0), 2.0, 8.0, boxstyle="round,pad=0.15",
                      facecolor='#F5F5F5', edgecolor='#9E9E9E', linewidth=2, linestyle='--')
ax.add_patch(rect)
ax.text(6.5, 9.3, 'Signal Bus\n(connect)', ha='center', fontsize=10, fontweight='bold', color='#616161')

# Receiver objects
receivers = [
    ('Model\nload_file()', 9.5, 8.0, '#E1BEE7'),
    ('View\nupdate_plot()', 9.5, 6.0, '#B2EBF2'),
    ('Controller\nrefresh()', 9.5, 4.0, '#DCEDC8'),
    ('StatusBar\nshow_msg()', 9.5, 2.0, '#FFE0B2'),
]

for name, x, y, color in receivers:
    rect = FancyBboxPatch((x, y-0.7), 2.5, 1.4, boxstyle="round,pad=0.1",
                          facecolor=color, edgecolor='#333', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x+1.25, y, name, ha='center', va='center', fontsize=9, fontweight='bold')

for _, x, y, _ in receivers:
    ax.annotate('', xy=(x, y), xytext=(7.5, y),
                arrowprops=dict(arrowstyle='->', color='#1E88E5', lw=2))
    ax.text(8.5, y+0.3, 'slot', ha='center', fontsize=7, color='#1E88E5', style='italic')

# Key insight
ax.text(7.0, 0.3, 'Signal-Slot: Sender does NOT know who receives → Loose Coupling',
        ha='center', fontsize=10, fontweight='bold', color='#D32F2F',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

ax.set_title('Qt Signal-Slot Mechanism', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{SAVE_DIR}day16_plot_1.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved day16_plot_1.png")

# ============================================================
# Plot 2: BCI Viewer Layout Design
# ============================================================
fig, ax = plt.subplots(figsize=(14, 9))
ax.set_xlim(0, 14); ax.set_ylim(0, 10); ax.axis('off')

# Main window border
rect = FancyBboxPatch((0.3, 0.3), 13.4, 9.2, boxstyle="round,pad=0.1",
                      facecolor='#FAFAFA', edgecolor='#333', linewidth=2)
ax.add_patch(rect)

# Menu bar
rect = FancyBboxPatch((0.5, 9.0), 13.0, 0.4, boxstyle="round,pad=0.02",
                      facecolor='#E0E0E0', edgecolor='#666', linewidth=1)
ax.add_patch(rect)
ax.text(7.0, 9.2, 'File | Edit | View | Tools | Help', ha='center', fontsize=8, color='#333')

# Toolbar
rect = FancyBboxPatch((0.5, 8.4), 13.0, 0.5, boxstyle="round,pad=0.02",
                      facecolor='#E8EAF6', edgecolor='#3F51B5', linewidth=1)
ax.add_patch(rect)
tools = ['[Load]', '[Filter]', '[Epoch]', '[Decode]', '[Export]', '[Settings]']
ax.text(7.0, 8.65, '  '.join(tools), ha='center', fontsize=8, fontweight='bold', color='#3F51B5')

# Left control panel (QDockWidget)
rect = FancyBboxPatch((0.5, 0.5), 3.0, 7.7, boxstyle="round,pad=0.05",
                      facecolor='#FFF3E0', edgecolor='#E65100', linewidth=1.5)
ax.add_patch(rect)
ax.text(2.0, 7.9, 'Control Panel', ha='center', fontsize=9, fontweight='bold', color='#E65100')

controls = [
    (2.0, 7.2, 'Filter Params', '#FFCCBC'),
    (2.0, 5.8, 'Epoch Settings', '#C8E6C9'),
    (2.0, 4.4, 'Channel Select', '#BBDEFB'),
    (2.0, 3.0, 'Classification', '#E1BEE7'),
    (2.0, 1.5, 'Display Options', '#DCEDC8'),
]
for x, y, label, color in controls:
    rect = FancyBboxPatch((x-1.2, y-0.5), 2.4, 1.0, boxstyle="round,pad=0.05",
                          facecolor=color, edgecolor='#999', linewidth=1)
    ax.add_patch(rect)
    ax.text(x, y, label, ha='center', va='center', fontsize=7.5, fontweight='bold')

# Center: EEG plot area
rect = FancyBboxPatch((3.7, 5.2), 9.5, 3.0, boxstyle="round,pad=0.05",
                      facecolor='#1a1a2e', edgecolor='#00ff88', linewidth=1.5)
ax.add_patch(rect)
ax.text(8.45, 7.8, 'EEG Waveform Display (Matplotlib Canvas)', ha='center', fontsize=9, 
        fontweight='bold', color='#00ff88')
# Simulate EEG traces
for i in range(8):
    t = np.linspace(3.8, 13.0, 200)
    signal = np.sin(2*np.pi*(5+i)*t + i) * 0.15 + 6.2 - i*0.3
    ax.plot(t, signal, linewidth=0.5, color='#00ff88', alpha=0.7)

# Center: Spectrum/Topo area
rect = FancyBboxPatch((3.7, 2.2), 9.5, 2.8, boxstyle="round,pad=0.05",
                      facecolor='#F5F5F5', edgecolor='#666', linewidth=1.5)
ax.add_patch(rect)
ax.text(8.45, 4.7, 'Spectrum / Topomap / TFR', ha='center', fontsize=9, fontweight='bold', color='#333')

# Mini spectrum plot
t = np.linspace(3.8, 7.0, 100)
psd = 1.0 / (1 + (t - 5.0)**2 / 0.5) + 0.3 / (1 + (t - 10)**2 / 2) + np.random.randn(100)*0.02
ax.plot(t, psd*1.5 + 2.8, linewidth=1, color='#2196F3')
ax.text(5.5, 3.2, 'PSD', fontsize=7, color='#2196F3')

# Mini topo placeholder
circle = plt.Circle((10.5, 3.5), 1.0, fill=False, edgecolor='#9C27B0', linewidth=1.5)
ax.add_patch(circle)
ax.text(10.5, 3.5, 'Topo', ha='center', fontsize=7, color='#9C27B0')

# Bottom: Results area
rect = FancyBboxPatch((3.7, 0.5), 9.5, 1.5, boxstyle="round,pad=0.05",
                      facecolor='#E8F5E9', edgecolor='#2E7D32', linewidth=1.5)
ax.add_patch(rect)
ax.text(8.45, 1.6, 'Results: Accuracy=92.3% | ITR=45.2 bits/min | Class: Left Hand',
        ha='center', fontsize=8, fontweight='bold', color='#2E7D32')
ax.text(8.45, 0.9, '[Confusion Matrix]  [ROC Curve]  [Export CSV]',
        ha='center', fontsize=7, color='#666')

# Status bar
rect = FancyBboxPatch((0.5, 0.1), 13.0, 0.3, boxstyle="round,pad=0.02",
                      facecolor='#E0E0E0', edgecolor='#666', linewidth=1)
ax.add_patch(rect)
ax.text(7.0, 0.25, 'Ready | 16 channels | 250 Hz | Filtered 1-40 Hz', ha='center', fontsize=7, color='#666')

# Qt class annotations
qt_classes = [
    (1.0, 0.3, 'QDockWidget', '#E65100'),
    (8.45, 8.2, 'QMainWindow', '#333'),
    (8.45, 5.0, 'FigureCanvasQTAgg', '#00ff88'),
    (8.45, 1.8, 'QStatusBar', '#2E7D32'),
]
for x, y, name, color in qt_classes:
    ax.text(x, y, f'({name})', fontsize=6, style='italic', color=color, alpha=0.7)

ax.set_title('BCI Data Viewer — Qt Layout Design', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{SAVE_DIR}day16_plot_2.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved day16_plot_2.png")

# ============================================================
# Plot 3: Thread Model — UI vs Workers
# ============================================================
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14); ax.set_ylim(0, 10); ax.axis('off')

# UI Thread
rect = FancyBboxPatch((0.5, 5.5), 5.0, 4.0, boxstyle="round,pad=0.15",
                      facecolor='#E3F2FD', edgecolor='#1565C0', linewidth=2)
ax.add_patch(rect)
ax.text(3.0, 9.0, 'UI Thread (Main)', ha='center', fontsize=11, fontweight='bold', color='#1565C0')

ui_tasks = ['QApplication.exec()', 'Event processing', 'Widget rendering', 'Signal dispatching']
for i, task in enumerate(ui_tasks):
    ax.text(3.0, 8.2 - i*0.6, f'• {task}', ha='center', fontsize=8, color='#1565C0')

# Worker threads
workers = [
    ('DataLoader\n(QThread)', 7.0, 8.5, '#FFF3E0', '#E65100'),
    ('Processor\n(QThread)', 10.0, 8.5, '#E8F5E9', '#2E7D32'),
    ('Classifier\n(QThread)', 7.0, 6.2, '#F3E5F5', '#7B1FA2'),
    ('RealtimeStream\n(QThread)', 10.0, 6.2, '#FFEBEE', '#C62828'),
]

for name, x, y, bg, border in workers:
    rect = FancyBboxPatch((x-1.2, y-0.8), 2.4, 1.6, boxstyle="round,pad=0.1",
                          facecolor=bg, edgecolor=border, linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x, y, name, ha='center', va='center', fontsize=8, fontweight='bold', color=border)

# Arrows: UI → Workers (start)
for _, x, y, _, border in workers:
    ax.annotate('', xy=(x, y+0.8), xytext=(5.5, 7.5),
                arrowprops=dict(arrowstyle='->', color=border, lw=1.5, connectionstyle='arc3,rad=0.1'))

# Arrows: Workers → UI (signals back)
signals_back = [
    (7.0, 7.7, 'data_loaded', '#E65100'),
    (10.0, 7.7, 'processing_done', '#2E7D32'),
    (7.0, 5.4, 'classified', '#7B1FA2'),
    (10.0, 5.4, 'new_sample', '#C62828'),
]
for x, y, label, color in signals_back:
    ax.annotate('', xy=(5.5, 6.5), xytext=(x, y),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.5, linestyle='dashed',
                               connectionstyle='arc3,rad=-0.1'))
    ax.text((x+5.5)/2 + 0.3, y + 0.3, label, fontsize=6, color=color, style='italic')

# Danger zone
rect = FancyBboxPatch((0.5, 0.5), 13.0, 4.5, boxstyle="round,pad=0.1",
                      facecolor='#FFEBEE', edgecolor='#C62828', linewidth=2, linestyle='--')
ax.add_patch(rect)
ax.text(7.0, 4.5, '⚠ Common Mistakes & Solutions', ha='center', fontsize=11, fontweight='bold', color='#C62828')

mistakes = [
    ('❌ raw.filter() in UI thread', '✅ QThread + finished signal', 3.5),
    ('❌ Direct UI update from worker', '✅ signal.emit() → slot in UI thread', 2.5),
    ('❌ No progress feedback', '✅ progress signal + QProgressBar', 1.5),
    ('❌ Forgetting draw_idle()', '✅ canvas.draw_idle() after update', 0.8),
]
for wrong, right, y in mistakes:
    ax.text(1.5, y, wrong, fontsize=8, color='#C62828')
    ax.text(7.5, y, '→  ' + right, fontsize=8, color='#2E7D32', fontweight='bold')

ax.set_title('Thread Model: UI Thread vs Worker Threads', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{SAVE_DIR}day16_plot_3.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved day16_plot_3.png")

# ============================================================
# Plot 4: MVC Architecture for BCI
# ============================================================
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14); ax.set_ylim(0, 10); ax.axis('off')

# Model
rect = FancyBboxPatch((0.5, 3.5), 3.5, 4.5, boxstyle="round,pad=0.15",
                      facecolor='#E3F2FD', edgecolor='#1565C0', linewidth=2)
ax.add_patch(rect)
ax.text(2.25, 7.5, 'MODEL', ha='center', fontsize=12, fontweight='bold', color='#1565C0')
model_items = ['Raw EEG data', 'Filtered data', 'Epochs', 'Classification results', 'Processing params']
for i, item in enumerate(model_items):
    ax.text(2.25, 6.7 - i*0.6, f'• {item}', ha='center', fontsize=8, color='#1565C0')

# View
rect = FancyBboxPatch((5.25, 3.5), 3.5, 4.5, boxstyle="round,pad=0.15",
                      facecolor='#E8F5E9', edgecolor='#2E7D32', linewidth=2)
ax.add_patch(rect)
ax.text(7.0, 7.5, 'VIEW', ha='center', fontsize=12, fontweight='bold', color='#2E7D32')
view_items = ['Waveform plot', 'Topomap display', 'Spectrum chart', 'Result panel', 'Status bar']
for i, item in enumerate(view_items):
    ax.text(7.0, 6.7 - i*0.6, f'• {item}', ha='center', fontsize=8, color='#2E7D32')

# Controller
rect = FancyBboxPatch((10.0, 3.5), 3.5, 4.5, boxstyle="round,pad=0.15",
                      facecolor='#FFF3E0', edgecolor='#E65100', linewidth=2)
ax.add_patch(rect)
ax.text(11.75, 7.5, 'CONTROLLER', ha='center', fontsize=12, fontweight='bold', color='#E65100')
ctrl_items = ['Signal processing', 'Parameter validation', 'Thread management', 'Error handling', 'State machine']
for i, item in enumerate(ctrl_items):
    ax.text(11.75, 6.7 - i*0.6, f'• {item}', ha='center', fontsize=8, color='#E65100')

# Arrows: Model ↔ Controller ↔ View
ax.annotate('', xy=(10.0, 6.0), xytext=(8.75, 6.0),
            arrowprops=dict(arrowstyle='<->', color='#E65100', lw=2.5))
ax.text(9.4, 6.4, 'update\ndata', ha='center', fontsize=7, style='italic', color='#E65100')

ax.annotate('', xy=(5.25, 5.0), xytext=(4.0, 5.0),
            arrowprops=dict(arrowstyle='<->', color='#2E7D32', lw=2.5))
ax.text(4.6, 5.4, 'notify\nchanges', ha='center', fontsize=7, style='italic', color='#2E7D32')

# User interaction
rect = FancyBboxPatch((5.25, 8.5), 3.5, 1.0, boxstyle="round,pad=0.1",
                      facecolor='#F5F5F5', edgecolor='#666', linewidth=1.5)
ax.add_patch(rect)
ax.text(7.0, 9.0, 'User Interaction', ha='center', fontsize=9, fontweight='bold')
ax.annotate('', xy=(7.0, 8.5), xytext=(7.0, 8.0),
            arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))

# Data source
rect = FancyBboxPatch((0.5, 0.5), 3.5, 2.2, boxstyle="round,pad=0.1",
                      facecolor='#FCE4EC', edgecolor='#C62828', linewidth=1.5)
ax.add_patch(rect)
ax.text(2.25, 2.2, 'Data Sources', ha='center', fontsize=9, fontweight='bold', color='#C62828')
ax.text(2.25, 1.5, '• .fif / .edf / .bdf files\n• LSL real-time stream\n• Simulated data', ha='center', fontsize=7, color='#C62828')
ax.annotate('', xy=(2.25, 3.5), xytext=(2.25, 2.7),
            arrowprops=dict(arrowstyle='->', color='#C62828', lw=1.5))

# BCI Pipeline flow
rect = FancyBboxPatch((5.25, 0.5), 8.25, 2.2, boxstyle="round,pad=0.1",
                      facecolor='#F5F5F5', edgecolor='#666', linewidth=1.5)
ax.add_patch(rect)
ax.text(9.4, 2.2, 'BCI Processing Pipeline (inside Controller)', ha='center', fontsize=9, fontweight='bold')

pipeline_steps = ['Load', '→', 'Filter', '→', 'Epoch', '→', 'Feature', '→', 'Classify', '→', 'Result']
x_positions = np.linspace(5.8, 12.8, len(pipeline_steps))
for x, step in zip(x_positions, pipeline_steps):
    if step == '→':
        ax.text(x, 1.2, step, ha='center', fontsize=10, color='#666')
    else:
        ax.text(x, 1.2, step, ha='center', fontsize=8, fontweight='bold', color='#333',
                bbox=dict(boxstyle='round', facecolor='white', edgecolor='#999'))

ax.set_title('MVC Architecture for BCI Application', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{SAVE_DIR}day16_plot_4.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved day16_plot_4.png")

# ============================================================
# Plot 5: Real-time Data Flow & Performance
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 5a: Data flow timing
ax = axes[0]
stages = ['Acquire\n(2ms)', 'Buffer\n(0.1ms)', 'Filter\n(5ms)', 'Feature\n(3ms)', 'Classify\n(2ms)', 'Display\n(8ms)']
times_ms = [2, 0.1, 5, 3, 2, 8]
colors_flow = ['#EF5350', '#FFA726', '#FFEE58', '#66BB6A', '#42A5F5', '#AB47BC']

bars = ax.barh(range(len(stages)), times_ms, color=colors_flow, edgecolor='black', linewidth=1)
ax.set_yticks(range(len(stages)))
ax.set_yticklabels(stages, fontsize=8)
ax.set_xlabel('Processing Time (ms)')
ax.set_title('Single-Trial Processing Pipeline')
ax.invert_yaxis()

for bar, t in zip(bars, times_ms):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            f'{t}ms', va='center', fontsize=8, fontweight='bold')

total = sum(times_ms)
ax.text(3, 6.5, f'Total: {total:.1f}ms → Well within 1000/250=4ms budget\n(Downsample display for real-time)',
        fontsize=8, fontweight='bold', color='#2E7D32',
        bbox=dict(boxstyle='round', facecolor='lightyellow'))

# 5b: FPS vs buffer size trade-off
ax = axes[1]
buffer_sizes = [50, 100, 200, 500, 1000, 2000]
fps_no_blit = [60, 45, 28, 12, 5, 2]
fps_blit = [60, 58, 52, 35, 20, 10]
fps_downsample = [60, 58, 55, 48, 40, 30]

ax.plot(buffer_sizes, fps_no_blit, 'o-', label='Redraw all', linewidth=2, color='#EF5350')
ax.plot(buffer_sizes, fps_blit, 's-', label='Blitting', linewidth=2, color='#42A5F5')
ax.plot(buffer_sizes, fps_downsample, '^-', label='Downsample + Blit', linewidth=2, color='#66BB6A')

ax.axhline(y=30, color='orange', linestyle='--', alpha=0.7, label='Target: 30 FPS')
ax.axhline(y=24, color='red', linestyle='--', alpha=0.5, label='Minimum: 24 FPS')
ax.set_xlabel('Display Buffer Size (samples)')
ax.set_ylabel('Rendering FPS')
ax.set_title('Display Performance vs Data Size')
ax.legend(fontsize=8)
ax.set_ylim(0, 70)
ax.grid(True, alpha=0.3)

plt.suptitle('BCI GUI: Real-time Data Flow & Performance', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{SAVE_DIR}day16_plot_5.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved day16_plot_5.png")

# ============================================================
# Plot 6: Complete BCI GUI Component Hierarchy
# ============================================================
fig, ax = plt.subplots(figsize=(14, 9))
ax.set_xlim(0, 14); ax.set_ylim(0, 10); ax.axis('off')

# Tree structure: QMainWindow at top
nodes = [
    ('QMainWindow\n(BCIViewer)', 7.0, 9.2, '#E3F2FD', '#1565C0', 0),
    # Level 1
    ('QMenuBar', 2.0, 7.5, '#E0E0E0', '#616161', 1),
    ('QToolBar', 4.5, 7.5, '#E8EAF6', '#3F51B5', 1),
    ('Central\nWidget', 7.0, 7.5, '#FFF3E0', '#E65100', 1),
    ('QDockWidget\n(Controls)', 9.5, 7.5, '#FFF3E0', '#E65100', 1),
    ('QStatusBar', 12.0, 7.5, '#E0E0E0', '#616161', 1),
    # Level 2 under Central
    ('EEGPlot\nWidget', 5.5, 5.5, '#E8F5E9', '#2E7D32', 2),
    ('Spectrum\nWidget', 8.5, 5.5, '#E8F5E9', '#2E7D32', 2),
    # Level 2 under DockWidget
    ('Filter\nPanel', 9.5, 5.5, '#FFF9C4', '#F9A825', 3),
    ('Epoch\nPanel', 11.0, 5.5, '#FFF9C4', '#F9A825', 3),
    # Level 3
    ('FigureCanvas\nQTAgg', 5.5, 3.5, '#F3E5F5', '#7B1FA2', 4),
    ('FigureCanvas\nQTAgg', 8.5, 3.5, '#F3E5F5', '#7B1FA2', 4),
    ('QSlider +\nQLabel', 9.5, 3.5, '#FFCCBC', '#BF360C', 5),
    ('QSpinBox +\nQComboBox', 11.0, 3.5, '#FFCCBC', '#BF360C', 5),
    # Level 4 (threads)
    ('QThread\nDataLoader', 3.0, 1.5, '#BBDEFB', '#1565C0', 6),
    ('QThread\nProcessor', 5.5, 1.5, '#BBDEFB', '#1565C0', 6),
    ('QThread\nClassifier', 8.0, 1.5, '#BBDEFB', '#1565C0', 6),
    ('QTimer\nRefresh', 10.5, 1.5, '#BBDEFB', '#1565C0', 6),
]

for name, x, y, bg, border, _ in nodes:
    w, h = 2.0, 1.2 if '\n' in name else 0.9
    rect = FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle="round,pad=0.08",
                          facecolor=bg, edgecolor=border, linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x, y, name, ha='center', va='center', fontsize=7, fontweight='bold', color=border)

# Connections
parent_child = [
    (7.0, 8.6, 2.0, 8.0), (7.0, 8.6, 4.5, 8.0), (7.0, 8.6, 7.0, 8.0),
    (7.0, 8.6, 9.5, 8.0), (7.0, 8.6, 12.0, 8.0),
    (7.0, 7.0, 5.5, 6.1), (7.0, 7.0, 8.5, 6.1),
    (9.5, 7.0, 9.5, 6.1), (9.5, 7.0, 11.0, 6.1),
    (5.5, 4.9, 5.5, 4.1), (8.5, 4.9, 8.5, 4.1),
    (9.5, 4.9, 9.5, 4.1), (11.0, 4.9, 11.0, 4.1),
]
for x1, y1, x2, y2 in parent_child:
    ax.plot([x1, x2], [y1, y2], '-', color='#999', linewidth=1, alpha=0.5)

# Thread connections (dashed)
thread_conns = [
    (5.5, 2.9, 3.0, 2.1), (5.5, 2.9, 5.5, 2.1),
    (8.5, 2.9, 8.0, 2.1), (8.5, 2.9, 10.5, 2.1),
]
for x1, y1, x2, y2 in thread_conns:
    ax.plot([x1, x2], [y1, y2], '--', color='#1565C0', linewidth=1, alpha=0.5)

ax.text(7.0, 0.3, 'Threads communicate with UI via Signal-Slot (never direct UI manipulation from QThread)',
        ha='center', fontsize=8, style='italic', color='#1565C0',
        bbox=dict(boxstyle='round', facecolor='#E3F2FD', alpha=0.8))

ax.set_title('BCI Viewer — Complete Qt Component Hierarchy', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{SAVE_DIR}day16_plot_6.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved day16_plot_6.png")

print("\n✅ Day 16 所有图表生成完毕!")
