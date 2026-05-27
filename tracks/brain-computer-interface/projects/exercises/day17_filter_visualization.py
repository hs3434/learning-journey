"""
Day 17: Filter & Visualization Integration
==========================================
Week 6 Day 2 — 滤波与可视化组件集成

Since Docker has no display server, we generate static architecture
diagrams and simulated BCI GUI layouts using Matplotlib.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.gridspec import GridSpec
from scipy.signal import butter, filtfilt, iirnotch, welch
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# Simulated EEG data generator (for visualization demos)
# ============================================================
def generate_eeg_signal(fs=256, duration=5, n_channels=16, seed=42):
    """Generate synthetic EEG with alpha, beta, and 50Hz powerline."""
    rng = np.random.RandomState(seed)
    n_samples = int(fs * duration)
    t = np.arange(n_samples) / fs
    
    data = np.zeros((n_channels, n_samples))
    for ch in range(n_channels):
        # Alpha rhythm (8-13 Hz)
        alpha = 30 * np.sin(2 * np.pi * (10 + rng.randn() * 0.5) * t)
        # Beta (15-30 Hz)
        beta = 10 * np.sin(2 * np.pi * (20 + rng.randn()) * t)
        # 50Hz powerline
        powerline = 20 * np.sin(2 * np.pi * 50 * t)
        # Noise
        noise = rng.randn(n_samples) * 5
        data[ch] = alpha + beta + powerline + noise
    
    return data, t, fs


def apply_bandpass(data, lowcut, highcut, fs, order=4):
    """Butterworth bandpass filter."""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, data, axis=-1)


def apply_notch(data, freq, fs, Q=30):
    """Notch filter to remove powerline interference."""
    w0 = freq / (fs / 2)
    b, a = iirnotch(w0, Q)
    return filtfilt(b, a, data, axis=-1)


# ============================================================
# Plot 1: Filter Pipeline Architecture
# ============================================================
def plot1_filter_pipeline():
    """Filter processing pipeline architecture diagram."""
    fig, ax = plt.subplots(1, 1, figsize=(14, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis('off')
    ax.set_title('Filter Pipeline Architecture', fontsize=16, fontweight='bold', pad=15)
    
    # Color scheme
    colors = {
        'input': '#4CAF50',
        'process': '#2196F3',
        'output': '#FF9800',
        'decision': '#9C27B0',
        'cache': '#607D8B',
    }
    
    # Box positions and labels
    boxes = [
        # (x, y, w, h, label, color, fontsize)
        (0.5, 5.5, 2.2, 1.0, 'Raw EEG\nData', colors['input'], 10),
        (4.0, 5.5, 2.5, 1.0, 'Bandpass\nFilter\n(1-40 Hz)', colors['process'], 9),
        (7.5, 5.5, 2.5, 1.0, 'Notch\nFilter\n(50/100 Hz)', colors['process'], 9),
        (11.0, 5.5, 2.2, 1.0, 'Filtered\nData', colors['output'], 10),
        
        (4.0, 3.5, 2.5, 1.0, 'FilterParams\n(dataclass)', '#E91E63', 9),
        (7.5, 3.5, 2.5, 1.0, 'FilterCache\n(LRU)', colors['cache'], 9),
        
        (0.5, 1.0, 2.2, 1.0, 'PSD\nWidget', '#FF5722', 10),
        (4.0, 1.0, 2.5, 1.0, 'EEG Plot\nWidget', '#FF5722', 10),
        (7.5, 1.0, 2.5, 1.0, 'Topo Map\nWidget', '#FF5722', 10),
        (11.0, 1.0, 2.2, 1.0, 'TFR\nWidget', '#FF5722', 10),
    ]
    
    for (x, y, w, h, label, color, fs) in boxes:
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor='white', alpha=0.85, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, label, ha='center', va='center',
                fontsize=fs, color='white', fontweight='bold')
    
    # Arrows
    arrows = [
        (2.7, 6.0, 4.0, 6.0),   # Raw → Bandpass
        (6.5, 6.0, 7.5, 6.0),   # Bandpass → Notch
        (10.0, 6.0, 11.0, 6.0), # Notch → Filtered
        (5.25, 5.5, 5.25, 4.5), # Bandpass ← Params
        (8.75, 5.5, 8.75, 4.5), # Notch ← Cache
        (5.25, 3.5, 5.25, 2.0), # Cache → EEG Plot
    ]
    
    for (x1, y1, x2, y2) in arrows:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='white', lw=2))
    
    # Visualization layer label
    ax.text(7.0, 2.5, 'Visualization Layer (Observer Pattern)',
            ha='center', fontsize=12, color='#FF5722', fontstyle='italic')
    
    # Pipeline flow label
    ax.text(7.0, 6.8, 'Processing Pipeline', ha='center',
            fontsize=12, color='#2196F3', fontstyle='italic')
    
    # Data flow from filtered to all widgets
    for target_x in [1.6, 5.25, 8.75, 12.1]:
        ax.annotate('', xy=(target_x, 2.0), xytext=(12.1, 5.5),
                    arrowprops=dict(arrowstyle='->', color='#FF9800',
                                    lw=1.5, connectionstyle='arc3,rad=0.2',
                                    alpha=0.6))
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day17_plot_1.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 2: Before/After Bandpass + Notch Filter (Simulated GUI)
# ============================================================
def plot2_filter_effect():
    """Show raw vs bandpass vs bandpass+notch filtering."""
    data, t, fs = generate_eeg_signal()
    ch_idx = 0  # Show one channel
    
    raw_signal = data[ch_idx]
    bp_signal = apply_bandpass(raw_signal, 1, 40, fs)
    bp_notch_signal = apply_notch(bp_signal, 50, fs)
    
    # PSD
    freqs_raw, psd_raw = welch(raw_signal, fs, nperseg=512)
    freqs_bp, psd_bp = welch(bp_signal, fs, nperseg=512)
    freqs_bpn, psd_bpn = welch(bp_notch_signal, fs, nperseg=512)
    
    fig = plt.figure(figsize=(16, 10), facecolor='#1a1a2e')
    gs = GridSpec(3, 3, figure=fig, hspace=0.4, wspace=0.3)
    
    # Time domain - 3 rows (raw, bandpass, bandpass+notch)
    titles_td = ['Raw EEG', 'After Bandpass (1-40 Hz)', 'After Bandpass + Notch (50 Hz)']
    signals_td = [raw_signal, bp_signal, bp_notch_signal]
    colors_td = ['#4CAF50', '#2196F3', '#FF9800']
    
    for i, (sig, title, color) in enumerate(zip(signals_td, titles_td, colors_td)):
        ax = fig.add_subplot(gs[i, 0:2])
        ax.set_facecolor('#16213e')
        # Show only first 1 second for clarity
        mask = t <= 1.0
        ax.plot(t[mask], sig[mask], linewidth=0.6, color=color, alpha=0.8)
        ax.set_title(title, color='white', fontsize=11, fontweight='bold')
        ax.set_ylabel('Amplitude (uV)', color='white', fontsize=9)
        ax.tick_params(colors='white', labelsize=8)
        for spine in ax.spines.values():
            spine.set_color('#444')
    
    # PSD - right column
    ax_psd = fig.add_subplot(gs[:, 2])
    ax_psd.set_facecolor('#16213e')
    ax_psd.semilogy(freqs_raw, psd_raw, color='#4CAF50', alpha=0.7, linewidth=1, label='Raw')
    ax_psd.semilogy(freqs_bp, psd_bp, color='#2196F3', alpha=0.7, linewidth=1, label='Bandpass')
    ax_psd.semilogy(freqs_bpn, psd_bpn, color='#FF9800', alpha=0.7, linewidth=1, label='BP+Notch')
    ax_psd.axvline(50, color='red', linestyle='--', alpha=0.5, linewidth=1, label='50 Hz')
    ax_psd.set_title('Power Spectral Density', color='white', fontsize=12, fontweight='bold')
    ax_psd.set_xlabel('Frequency (Hz)', color='white', fontsize=10)
    ax_psd.set_ylabel('PSD (uV^2/Hz)', color='white', fontsize=10)
    ax_psd.legend(fontsize=8, facecolor='#16213e', edgecolor='#444', labelcolor='white')
    ax_psd.set_xlim(0, 80)
    ax_psd.tick_params(colors='white', labelsize=8)
    for spine in ax_psd.spines.values():
        spine.set_color('#444')
    
    fig.suptitle('Filter Pipeline: Raw → Bandpass → Notch', 
                 color='white', fontsize=14, fontweight='bold', y=0.98)
    
    path = os.path.join(OUT_DIR, 'day17_plot_2.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 3: GUI Layout Blueprint (Simulated BCI Data Analysis Tool)
# ============================================================
def plot3_gui_layout():
    """Simulated BCI GUI layout with all panels."""
    fig = plt.figure(figsize=(16, 10), facecolor='#1a1a2e')
    
    # Title bar
    ax_title = fig.add_axes([0.02, 0.94, 0.96, 0.05])
    ax_title.set_facecolor('#0f3460')
    ax_title.text(0.5, 0.5, 'BCI Data Analysis Tool v1.0', 
                  ha='center', va='center', fontsize=14, 
                  color='white', fontweight='bold')
    ax_title.axis('off')
    
    # Toolbar
    ax_toolbar = fig.add_axes([0.02, 0.89, 0.96, 0.04])
    ax_toolbar.set_facecolor('#16213e')
    toolbar_labels = ['Load', 'Filter', 'Notch', 'Epoch', 'Decode', 'Export']
    for i, label in enumerate(toolbar_labels):
        x = 0.05 + i * 0.15
        rect = FancyBboxPatch((x, 0.15), 0.10, 0.7, boxstyle="round,pad=0.02",
                              facecolor='#2196F3', edgecolor='white', 
                              alpha=0.8, transform=ax_toolbar.transAxes)
        ax_toolbar.add_patch(rect)
        ax_toolbar.text(x + 0.05, 0.5, label, ha='center', va='center',
                       fontsize=9, color='white', fontweight='bold',
                       transform=ax_toolbar.transAxes)
    ax_toolbar.axis('off')
    
    # Left panel: Controls
    ax_ctrl = fig.add_axes([0.02, 0.08, 0.18, 0.79])
    ax_ctrl.set_facecolor('#16213e')
    ax_ctrl.set_title('Controls', color='white', fontsize=11, fontweight='bold')
    
    ctrl_items = [
        ('Bandpass Filter', '#2196F3'),
        ('  Low: [===] 1 Hz', '#4CAF50'),
        ('  High: [====] 40 Hz', '#4CAF50'),
        ('  [Apply]', '#FF9800'),
        ('', '#16213e'),
        ('Notch Filter', '#2196F3'),
        ('  [x] 50 Hz', '#4CAF50'),
        ('  [x] 100 Hz', '#4CAF50'),
        ('  [Apply]', '#FF9800'),
        ('', '#16213e'),
        ('Epoch Settings', '#2196F3'),
        ('  tmin: -0.2 s', '#4CAF50'),
        ('  tmax: 0.5 s', '#4CAF50'),
        ('  [Extract]', '#FF9800'),
    ]
    
    for i, (text, color) in enumerate(ctrl_items):
        y = 0.95 - i * 0.065
        fontsize = 8 if text.startswith('  ') else 9
        weight = 'bold' if not text.startswith('  ') else 'normal'
        ax_ctrl.text(0.1, y, text, fontsize=fontsize, color='white',
                    fontweight=weight, va='top', transform=ax_ctrl.transAxes)
    ax_ctrl.axis('off')
    
    # Right top: EEG waveform area
    data, t, fs = generate_eeg_signal(duration=3, n_channels=8)
    data_filt = apply_notch(apply_bandpass(data, 1, 40, fs), 50, fs)
    
    ax_eeg = fig.add_axes([0.23, 0.55, 0.74, 0.32])
    ax_eeg.set_facecolor('#0a0a23')
    n_show = 8
    for ch in range(n_show):
        offset = ch * 80
        ax_eeg.plot(t, data_filt[ch] + offset, linewidth=0.4, 
                   color='#00ff88', alpha=0.8)
        ax_eeg.text(-0.01, offset, f'Ch{ch+1}', fontsize=7, color='#aaa',
                   ha='right', va='center', transform=ax_eeg.get_yaxis_transform())
    ax_eeg.set_title('EEG Waveform (Filtered)', color='white', fontsize=11, fontweight='bold')
    ax_eeg.set_xlabel('Time (s)', color='white', fontsize=9)
    ax_eeg.tick_params(colors='white', labelsize=7)
    for spine in ax_eeg.spines.values():
        spine.set_color('#333')
    
    # Right middle: PSD
    ax_psd = fig.add_axes([0.23, 0.30, 0.35, 0.22])
    ax_psd.set_facecolor('#0a0a23')
    freqs_r, psd_r = welch(data[0], fs, nperseg=512)
    freqs_f, psd_f = welch(data_filt[0], fs, nperseg=512)
    ax_psd.semilogy(freqs_r, psd_r, color='#4CAF50', alpha=0.5, linewidth=0.8, label='Raw')
    ax_psd.semilogy(freqs_f, psd_f, color='#2196F3', alpha=0.8, linewidth=0.8, label='Filtered')
    ax_psd.axvline(50, color='red', linestyle='--', alpha=0.4, linewidth=0.8)
    ax_psd.set_title('PSD Comparison', color='white', fontsize=10, fontweight='bold')
    ax_psd.set_xlabel('Freq (Hz)', color='white', fontsize=8)
    ax_psd.set_xlim(0, 80)
    ax_psd.legend(fontsize=7, facecolor='#0a0a23', edgecolor='#444', labelcolor='white')
    ax_psd.tick_params(colors='white', labelsize=7)
    for spine in ax_psd.spines.values():
        spine.set_color('#333')
    
    # Right middle: Topomap placeholder
    ax_topo = fig.add_axes([0.62, 0.30, 0.35, 0.22])
    ax_topo.set_facecolor('#0a0a23')
    # Simulate a topomap using a 2D Gaussian
    x = np.linspace(-1, 1, 100)
    y = np.linspace(-1, 1, 100)
    X, Y = np.meshgrid(x, y)
    Z = np.exp(-((X-0.2)**2 + (Y-0.1)**2) / 0.3) * 0.8 + \
        np.exp(-((X+0.3)**2 + (Y-0.3)**2) / 0.2) * 0.5
    # Mask outside head
    mask = X**2 + Y**2 > 1
    Z[mask] = np.nan
    im = ax_topo.imshow(Z, extent=[-1, 1, -1, 1], cmap='RdBu_r', 
                        vmin=-0.5, vmax=1.0, origin='lower')
    # Head outline
    theta = np.linspace(0, 2*np.pi, 100)
    ax_topo.plot(np.cos(theta), np.sin(theta), 'k-', linewidth=1.5)
    # Nose
    ax_topo.plot([0, 0], [0.95, 1.1], 'k-', linewidth=1.5)
    ax_topo.set_title('Alpha Topomap (8-13 Hz)', color='white', fontsize=10, fontweight='bold')
    ax_topo.axis('off')
    cbar = fig.colorbar(im, ax=ax_topo, shrink=0.7, pad=0.02)
    cbar.ax.tick_params(colors='white', labelsize=7)
    
    # Bottom: Status bar
    ax_status = fig.add_axes([0.02, 0.02, 0.96, 0.05])
    ax_status.set_facecolor('#0f3460')
    status_text = '16 ch | 256 Hz | 5.0s | Filtered: 1-40 Hz + Notch 50Hz | Pipeline: FILTERED'
    ax_status.text(0.5, 0.5, status_text, ha='center', va='center',
                  fontsize=9, color='#00ff88')
    ax_status.axis('off')
    
    path = os.path.join(OUT_DIR, 'day17_plot_3.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 4: Observer Pattern — Signal Flow Diagram
# ============================================================
def plot4_observer_pattern():
    """Observer pattern signal flow in BCI GUI."""
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')
    ax.set_title('Observer Pattern: Data Change Propagation', 
                 fontsize=15, fontweight='bold', pad=15)
    
    # Subject (center)
    subject = FancyBboxPatch((4.5, 5.0), 5, 1.5, boxstyle="round,pad=0.15",
                             facecolor='#E91E63', edgecolor='white', 
                             alpha=0.9, linewidth=2)
    ax.add_patch(subject)
    ax.text(7.0, 5.75, 'VisualizationManager\ndata_updated.emit(raw)',
            ha='center', va='center', fontsize=10, color='white', fontweight='bold')
    
    # Observers (bottom row)
    observers = [
        (0.5, 1.0, 'EEG Plot\nWidget', '#2196F3'),
        (3.5, 1.0, 'PSD Plot\nWidget', '#4CAF50'),
        (6.5, 1.0, 'Topomap\nWidget', '#FF9800'),
        (9.5, 1.0, 'TFR Plot\nWidget', '#9C27B0'),
        (12.0, 1.0, 'Status\nBar', '#607D8B'),
    ]
    
    for (x, y, label, color) in observers:
        rect = FancyBboxPatch((x, y), 2.5, 1.2, boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor='white', 
                              alpha=0.85, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 1.25, y + 0.6, label, ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
    
    # Trigger sources (top)
    triggers = [
        (1.0, 7.0, 'User clicks\n"Apply Filter"', '#FF5722'),
        (5.0, 7.0, 'Data loaded\nfrom file', '#00BCD4'),
        (9.5, 7.0, 'Notch filter\ntoggled', '#795548'),
    ]
    
    for (x, y, label, color) in triggers:
        rect = FancyBboxPatch((x, y), 2.5, 0.9, boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor='white',
                              alpha=0.85, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 1.25, y + 0.45, label, ha='center', va='center',
                fontsize=8, color='white', fontweight='bold')
    
    # Arrows: triggers → subject
    for (x, _, _, _) in triggers:
        ax.annotate('', xy=(x + 1.25, 6.5), xytext=(x + 1.25, 7.0),
                    arrowprops=dict(arrowstyle='->', color='white', lw=2))
    
    # Arrows: subject → observers (broadcast)
    for (x, _, _, color) in observers:
        ax.annotate('', xy=(x + 1.25, 2.2), xytext=(7.0, 5.0),
                    arrowprops=dict(arrowstyle='->', color=color, lw=2,
                                    connectionstyle='arc3,rad=0.15', alpha=0.7))
    
    # Labels
    ax.text(7.0, 4.2, '▼  broadcast signal  ▼', ha='center',
            fontsize=11, color='#E91E63', fontstyle='italic')
    ax.text(3.5, 7.7, 'Trigger Sources', ha='center',
            fontsize=11, color='#FF5722', fontstyle='italic')
    ax.text(7.0, 0.5, 'Observer Widgets (auto-update on signal)', ha='center',
            fontsize=11, color='#2196F3', fontstyle='italic')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day17_plot_4.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 5: Pipeline State Machine + UI Availability
# ============================================================
def plot5_state_machine():
    """Pipeline state machine diagram with UI availability."""
    fig, ax = plt.subplots(1, 1, figsize=(15, 7))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 7)
    ax.axis('off')
    ax.set_title('Pipeline State Machine & UI Availability', 
                 fontsize=15, fontweight='bold', pad=15)
    
    states = [
        (1.0, 4.0, 'EMPTY\n(no data)', '#9E9E9E', ['Load: ON', 'Filter: OFF', 'Epoch: OFF', 'Decode: OFF']),
        (4.0, 4.0, 'LOADED\n(raw data)', '#4CAF50', ['Load: ON', 'Filter: ON', 'Epoch: OFF', 'Decode: OFF']),
        (7.0, 4.0, 'FILTERED\n(clean data)', '#2196F3', ['Load: ON', 'Filter: ON', 'Epoch: ON', 'Decode: OFF']),
        (10.0, 4.0, 'EPOCHED\n(trials)', '#FF9800', ['Load: ON', 'Filter: ON', 'Epoch: ON', 'Decode: ON']),
        (13.0, 4.0, 'DECODED\n(results)', '#E91E63', ['Load: ON', 'Filter: ON', 'Epoch: ON', 'Decode: ON']),
    ]
    
    for i, (x, y, label, color, avail) in enumerate(states):
        # State circle
        circle = plt.Circle((x + 1, y + 1), 0.9, facecolor=color, 
                           edgecolor='white', linewidth=2, alpha=0.85)
        ax.add_patch(circle)
        ax.text(x + 1, y + 1, label, ha='center', va='center',
               fontsize=8, color='white', fontweight='bold')
        
        # Available operations
        for j, op in enumerate(avail):
            op_color = '#4CAF50' if 'ON' in op else '#F44336'
            ax.text(x + 1, y - 0.5 - j * 0.35, op, ha='center',
                   fontsize=7, color=op_color)
        
        # Arrow to next state
        if i < len(states) - 1:
            next_x = states[i+1][0]
            ax.annotate('', xy=(next_x + 0.1, y + 1), xytext=(x + 1.9, y + 1),
                       arrowprops=dict(arrowstyle='->', color='white', lw=2.5))
    
    # Transition labels
    transitions = ['load_data()', 'apply_filter()', 'extract_epochs()', 'decode()']
    for i, t in enumerate(transitions):
        x = states[i][0] + 2.0
        ax.text(x, 5.5, t, ha='center', fontsize=8, color='#FFD700',
               fontstyle='italic', fontweight='bold')
    
    # Annotation
    ax.text(7.5, 6.5, 'State advances → more UI controls become available',
            ha='center', fontsize=11, color='#FFD700', fontstyle='italic')
    
    # Back arrow (can reload anytime)
    ax.annotate('', xy=(1.5, 6.2), xytext=(13.5, 6.2),
               arrowprops=dict(arrowstyle='->', color='#9E9E9E', lw=1.5,
                               connectionstyle='arc3,rad=-0.3', linestyle='dashed'))
    ax.text(7.5, 6.8, 'load_data() resets to LOADED (anytime)', ha='center',
            fontsize=8, color='#9E9E9E')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day17_plot_5.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 6: Multi-channel Filtered EEG + PSD + Band Power
# ============================================================
def plot6_multi_channel_analysis():
    """Multi-channel EEG analysis: waveform + PSD + band power bars."""
    data, t, fs = generate_eeg_signal(duration=3, n_channels=16)
    data_filt = apply_notch(apply_bandpass(data, 1, 40, fs), 50, fs)
    
    fig = plt.figure(figsize=(14, 8), facecolor='#1a1a2e')
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.3,
                  height_ratios=[1.2, 1],
                  top=0.93, bottom=0.08, left=0.08, right=0.95)
    
    # Top: Multi-channel waveform
    ax_wave = fig.add_subplot(gs[0, :])
    ax_wave.set_facecolor('#0a0a23')
    n_show = 12
    for ch in range(n_show):
        offset = ch * 60
        ax_wave.plot(t, data_filt[ch] + offset, linewidth=0.3, 
                    color='#00ff88', alpha=0.7)
        ax_wave.text(-0.02, offset, f'Ch{ch+1:02d}', fontsize=7, color='#aaa',
                    ha='right', va='center', transform=ax_wave.get_yaxis_transform())
    ax_wave.set_title('Multi-Channel Filtered EEG (1-40 Hz + Notch 50 Hz)', 
                      color='white', fontsize=12, fontweight='bold')
    ax_wave.set_xlabel('Time (s)', color='white', fontsize=9)
    ax_wave.set_ylabel('Channels (offset)', color='white', fontsize=9)
    ax_wave.tick_params(colors='white', labelsize=7)
    for spine in ax_wave.spines.values():
        spine.set_color('#333')
    
    # Bottom left: Average PSD across channels
    ax_psd = fig.add_subplot(gs[1, 0])
    ax_psd.set_facecolor('#0a0a23')
    
    avg_psd_raw = np.zeros(257)
    avg_psd_filt = np.zeros(257)
    for ch in range(16):
        f_r, p_r = welch(data[ch], fs, nperseg=512)
        f_f, p_f = welch(data_filt[ch], fs, nperseg=512)
        avg_psd_raw += p_r[:257]
        avg_psd_filt += p_f[:257]
    avg_psd_raw /= 16
    avg_psd_filt /= 16
    freqs = f_r[:257]
    
    ax_psd.semilogy(freqs, avg_psd_raw, color='#4CAF50', alpha=0.5, linewidth=0.8, label='Raw')
    ax_psd.semilogy(freqs, avg_psd_filt, color='#2196F3', alpha=0.8, linewidth=0.8, label='Filtered')
    ax_psd.axvline(50, color='red', linestyle='--', alpha=0.4, linewidth=0.8, label='50 Hz notch')
    
    # Band markers
    bands = [(1, 4, 'Delta'), (4, 8, 'Theta'), (8, 13, 'Alpha'), (13, 30, 'Beta')]
    band_colors = ['#9C27B0', '#00BCD4', '#4CAF50', '#FF9800']
    for (lo, hi, name), bc in zip(bands, band_colors):
        ax_psd.axvspan(lo, hi, alpha=0.15, color=bc)
        ax_psd.text((lo + hi) / 2, 0.85, 
                    name, ha='center', fontsize=7, color=bc, fontweight='bold',
                    transform=ax_psd.get_xaxis_transform())
    
    ax_psd.set_title('Average PSD (16 channels)', color='white', fontsize=11, fontweight='bold')
    ax_psd.set_xlabel('Frequency (Hz)', color='white', fontsize=9)
    ax_psd.set_xlim(0, 60)
    ax_psd.legend(fontsize=7, facecolor='#0a0a23', edgecolor='#444', labelcolor='white')
    ax_psd.tick_params(colors='white', labelsize=7)
    for spine in ax_psd.spines.values():
        spine.set_color('#333')
    
    # Bottom right: Band power comparison
    ax_bar = fig.add_subplot(gs[1, 1])
    ax_bar.set_facecolor('#0a0a23')
    
    band_powers_raw = []
    band_powers_filt = []
    band_names = ['Delta\n(1-4)', 'Theta\n(4-8)', 'Alpha\n(8-13)', 'Beta\n(13-30)']
    band_ranges = [(1, 4), (4, 8), (8, 13), (13, 30)]
    
    for lo, hi in band_ranges:
        mask = (freqs >= lo) & (freqs <= hi)
        band_powers_raw.append(np.mean(avg_psd_raw[mask]))
        band_powers_filt.append(np.mean(avg_psd_filt[mask]))
    
    x_pos = np.arange(len(band_names))
    width = 0.35
    bars1 = ax_bar.bar(x_pos - width/2, band_powers_raw, width, 
                       color='#4CAF50', alpha=0.7, label='Raw')
    bars2 = ax_bar.bar(x_pos + width/2, band_powers_filt, width,
                       color='#2196F3', alpha=0.7, label='Filtered')
    
    ax_bar.set_xticks(x_pos)
    ax_bar.set_xticklabels(band_names, fontsize=8, color='white')
    ax_bar.set_title('Band Power: Raw vs Filtered', color='white', fontsize=11, fontweight='bold')
    ax_bar.set_ylabel('Avg PSD (uV^2/Hz)', color='white', fontsize=9)
    ax_bar.legend(fontsize=8, facecolor='#0a0a23', edgecolor='#444', labelcolor='white')
    ax_bar.tick_params(colors='white', labelsize=7)
    for spine in ax_bar.spines.values():
        spine.set_color('#333')
    
    fig.suptitle('Integrated Visualization: Waveform + Spectrum + Band Power', 
                 color='white', fontsize=13, fontweight='bold', y=0.99)
    
    path = os.path.join(OUT_DIR, 'day17_plot_6.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Main
# ============================================================
if __name__ == '__main__':
    print("Day 17: Filter & Visualization Integration")
    print("=" * 50)
    
    plot1_filter_pipeline()
    plot2_filter_effect()
    plot3_gui_layout()
    plot4_observer_pattern()
    plot5_state_machine()
    plot6_multi_channel_analysis()
    
    print("\n✅ Day 17 所有图表生成完毕!")
