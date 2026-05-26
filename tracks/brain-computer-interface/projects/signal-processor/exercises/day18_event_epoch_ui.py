"""
Day 18: Event Marking & Epoch Extraction UI
============================================
Week 6 Day 3 — 事件标记与 Epoch 提取 UI

Static architecture diagrams + simulated MNE data processing.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle
from matplotlib.gridspec import GridSpec
from scipy.signal import butter, filtfilt, iirnotch
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_eeg_signal(fs=256, duration=10, n_channels=16, seed=42):
    rng = np.random.RandomState(seed)
    n_samples = int(fs * duration)
    t = np.arange(n_samples) / fs
    data = np.zeros((n_channels, n_samples))
    
    # Create events at specific times
    event_times = [1.0, 3.0, 5.0, 7.0, 9.0]  # 5 events
    event_ids = [1, 2, 1, 2, 1]  # alternating class
    
    for ch in range(n_channels):
        # Background alpha
        signal = 20 * np.sin(2 * np.pi * 10 * t)
        # Add ERP-like response at event times
        for et, eid in zip(event_times, event_ids):
            idx_start = int(et * fs)
            idx_end = min(idx_start + int(0.8 * fs), n_samples)
            t_local = np.arange(idx_end - idx_start) / fs
            if eid == 1:
                # P300-like positive peak
                signal[idx_start:idx_end] += 15 * np.exp(-((t_local - 0.3)**2) / 0.02)
            else:
                # N200-like negative peak
                signal[idx_start:idx_end] -= 10 * np.exp(-((t_local - 0.2)**2) / 0.01)
        # Noise
        signal += rng.randn(n_samples) * 5
        data[ch] = signal
    
    return data, t, fs, event_times, event_ids


# ============================================================
# Plot 1: Event Marking Architecture
# ============================================================
def plot1_event_marking_arch():
    fig, ax = plt.subplots(1, 1, figsize=(14, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis('off')
    ax.set_title('Event Marking: Three Input Modes', fontsize=15, fontweight='bold', pad=15)
    
    # Three input modes
    modes = [
        (1.0, 5.5, 'Auto Detect\n(find_events)', '#4CAF50', 'Trigger channel\nstim threshold'),
        (5.0, 5.5, 'Manual Click\n(GUI interactive)', '#2196F3', 'User clicks on\nwaveform'),
        (9.0, 5.5, 'Batch Import\n(CSV/TSV)', '#FF9800', 'External event\nmarker file'),
    ]
    
    for (x, y, label, color, desc) in modes:
        rect = FancyBboxPatch((x, y), 3.5, 1.2, boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor='white', alpha=0.85, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 1.75, y + 0.8, label, ha='center', va='center',
                fontsize=10, color='white', fontweight='bold')
        ax.text(x + 1.75, y + 0.3, desc, ha='center', va='center',
                fontsize=8, color='white', alpha=0.8)
    
    # Central: Event Array
    center_rect = FancyBboxPatch((3.5, 2.8), 7, 1.2, boxstyle="round,pad=0.1",
                                  facecolor='#E91E63', edgecolor='white', alpha=0.9, linewidth=2)
    ax.add_patch(center_rect)
    ax.text(7.0, 3.4, 'Events Array  (N x 3)', ha='center', va='center',
            fontsize=12, color='white', fontweight='bold')
    ax.text(7.0, 3.0, '[sample_index, 0, event_id]', ha='center', va='center',
            fontsize=9, color='white', alpha=0.8)
    
    # Arrows: modes → center
    for (x, _, _, _, _) in modes:
        ax.annotate('', xy=(7.0, 4.0), xytext=(x + 1.75, 5.5),
                    arrowprops=dict(arrowstyle='->', color='white', lw=2,
                                    connectionstyle='arc3,rad=0.1'))
    
    # Bottom: Epoch extraction
    bottom_rect = FancyBboxPatch((2.5, 0.5), 9, 1.2, boxstyle="round,pad=0.1",
                                  facecolor='#9C27B0', edgecolor='white', alpha=0.85, linewidth=2)
    ax.add_patch(bottom_rect)
    ax.text(7.0, 1.1, 'Epoch Extraction  (tmin, tmax, baseline)', ha='center', va='center',
            fontsize=11, color='white', fontweight='bold')
    ax.text(7.0, 0.7, 'mne.Epochs(raw, events, event_id, tmin, tmax, baseline)', ha='center', va='center',
            fontsize=8, color='white', alpha=0.8)
    
    ax.annotate('', xy=(7.0, 1.7), xytext=(7.0, 2.8),
                arrowprops=dict(arrowstyle='->', color='white', lw=2.5))
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day18_plot_1.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 2: EEG with Event Markers + Epoch Windows
# ============================================================
def plot2_eeg_events_epochs():
    data, t, fs, event_times, event_ids = generate_eeg_signal(duration=10, n_channels=4)
    data_filt = filtfilt(*butter(4, [1, 40], btype='band', fs=fs), data, axis=-1)
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 9), facecolor='#1a1a2e',
                              gridspec_kw={'height_ratios': [1.2, 1, 1]})
    
    # Top: Raw with event markers
    ax1 = axes[0]
    ax1.set_facecolor('#0a0a23')
    ch = 0
    mask = t <= 5
    ax1.plot(t[mask], data_filt[ch, mask], color='#00ff88', linewidth=0.5, alpha=0.8)
    
    event_colors = {1: '#FF5722', 2: '#2196F3'}
    event_labels = {1: 'Class A', 2: 'Class B'}
    for et, eid in zip(event_times[:3], event_ids[:3]):
        ax1.axvline(et, color=event_colors[eid], linewidth=2, alpha=0.8, linestyle='--')
        ax1.text(et, ax1.get_ylim()[1] if ax1.get_ylim()[1] != 0 else 50, 
                 event_labels[eid], fontsize=9, color=event_colors[eid],
                 fontweight='bold', ha='center', va='bottom')
    ax1.set_title('EEG with Event Markers', color='white', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Time (s)', color='white', fontsize=9)
    ax1.set_ylabel('Amplitude', color='white', fontsize=9)
    ax1.tick_params(colors='white', labelsize=8)
    for spine in ax1.spines.values():
        spine.set_color('#333')
    
    # Middle: Epoch windows highlighted
    ax2 = axes[1]
    ax2.set_facecolor('#0a0a23')
    ax2.plot(t[mask], data_filt[ch, mask], color='#00ff88', linewidth=0.5, alpha=0.8)
    
    tmin, tmax = -0.2, 0.5
    for et, eid in zip(event_times[:3], event_ids[:3]):
        ax2.axvspan(et + tmin, et + tmax, alpha=0.2, color=event_colors[eid])
        ax2.axvline(et, color=event_colors[eid], linewidth=1.5, linestyle='--')
    ax2.set_title(f'Epoch Windows (tmin={tmin}s, tmax={tmax}s)', color='white', 
                  fontsize=12, fontweight='bold')
    ax2.set_xlabel('Time (s)', color='white', fontsize=9)
    ax2.tick_params(colors='white', labelsize=8)
    for spine in ax2.spines.values():
        spine.set_color('#333')
    
    # Bottom: Extracted Epochs overlay
    ax3 = axes[2]
    ax3.set_facecolor('#0a0a23')
    
    for i, (et, eid) in enumerate(zip(event_times[:3], event_ids[:3])):
        idx_start = int((et + tmin) * fs)
        idx_end = int((et + tmax) * fs)
        epoch_data = data_filt[ch, idx_start:idx_end]
        t_epoch = np.linspace(tmin, tmax, len(epoch_data))
        # Baseline correction
        baseline_mean = epoch_data[:int(-tmin * fs)].mean()
        epoch_data = epoch_data - baseline_mean
        ax3.plot(t_epoch, epoch_data + i * 30, color=event_colors[eid], 
                linewidth=0.8, alpha=0.7)
        ax3.text(tmax + 0.05, i * 30, f'Trial {i+1} ({event_labels[eid]})',
                fontsize=8, color=event_colors[eid], va='center')
    
    ax3.axvline(0, color='white', linestyle=':', alpha=0.5, linewidth=1)
    ax3.set_title('Extracted Epochs (Baseline Corrected)', color='white', 
                  fontsize=12, fontweight='bold')
    ax3.set_xlabel('Time relative to event (s)', color='white', fontsize=9)
    ax3.tick_params(colors='white', labelsize=8)
    for spine in ax3.spines.values():
        spine.set_color('#333')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day18_plot_2.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 3: Epoch Extraction + Artifact Rejection
# ============================================================
def plot3_artifact_rejection():
    data, t, fs, event_times, event_ids = generate_eeg_signal(duration=10, n_channels=16)
    data_filt = filtfilt(*butter(4, [1, 40], btype='band', fs=fs), data, axis=-1)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), facecolor='#1a1a2e')
    
    # Left: Peak-to-peak amplitude distribution
    ax1.set_facecolor('#0a0a23')
    tmin, tmax = -0.2, 0.5
    ptp_values = []
    labels = []
    
    for et, eid in zip(event_times, event_ids):
        idx_start = int((et + tmin) * fs)
        idx_end = int((et + tmax) * fs)
        epoch_data = data_filt[:, idx_start:idx_end]
        ptp = epoch_data.max(axis=1) - epoch_data.min(axis=1)
        ptp_values.append(ptp.max())
        labels.append(eid)
    
    # Add some artifact-like epochs
    rng = np.random.RandomState(123)
    for _ in range(3):
        ptp_values.append(80 + rng.rand() * 60)
        labels.append(0)
    
    colors = ['#4CAF50' if l == 1 else '#2196F3' if l == 2 else '#F44336' for l in labels]
    x = range(len(ptp_values))
    ax1.bar(x, ptp_values, color=colors, alpha=0.8, edgecolor='white', linewidth=0.5)
    ax1.axhline(100, color='#FF9800', linestyle='--', linewidth=2, label='Reject threshold (100 uV)')
    ax1.set_title('Peak-to-Peak Amplitude per Epoch', color='white', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Epoch Index', color='white', fontsize=9)
    ax1.set_ylabel('P-P Amplitude (uV)', color='white', fontsize=9)
    ax1.legend(fontsize=8, facecolor='#0a0a23', edgecolor='#444', labelcolor='white')
    ax1.tick_params(colors='white', labelsize=8)
    for spine in ax1.spines.values():
        spine.set_color('#333')
    
    # Right: Good vs Bad epoch count
    ax2.set_facecolor('#0a0a23')
    good = sum(1 for v in ptp_values if v < 100)
    bad = len(ptp_values) - good
    bars = ax2.bar(['Accepted', 'Rejected'], [good, bad], 
                   color=['#4CAF50', '#F44336'], alpha=0.8, edgecolor='white', linewidth=1)
    for bar, val in zip(bars, [good, bad]):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                str(val), ha='center', fontsize=14, color='white', fontweight='bold')
    ax2.set_title('Epoch Acceptance Summary', color='white', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Count', color='white', fontsize=9)
    ax2.tick_params(colors='white', labelsize=9)
    for spine in ax2.spines.values():
        spine.set_color('#333')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day18_plot_3.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 4: ERP Overlay + Grand Average
# ============================================================
def plot4_erp_overlay():
    data, t, fs, event_times, event_ids = generate_eeg_signal(duration=10, n_channels=16)
    data_filt = filtfilt(*butter(4, [1, 40], btype='band', fs=fs), data, axis=-1)
    tmin, tmax = -0.2, 0.5
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), facecolor='#1a1a2e')
    
    # Channel C3 (index 2) for MI-like analysis
    ch = 2
    
    class_a_epochs = []
    class_b_epochs = []
    
    for et, eid in zip(event_times, event_ids):
        idx_start = int((et + tmin) * fs)
        idx_end = int((et + tmax) * fs)
        epoch = data_filt[ch, idx_start:idx_end]
        baseline = epoch[:int(-tmin * fs)].mean()
        epoch = epoch - baseline
        if eid == 1:
            class_a_epochs.append(epoch)
        else:
            class_b_epochs.append(epoch)
    
    t_epoch = np.linspace(tmin, tmax, len(class_a_epochs[0]))
    
    # Left: All epochs overlay (Class A)
    ax1.set_facecolor('#0a0a23')
    for ep in class_a_epochs:
        ax1.plot(t_epoch, ep, color='#FF5722', alpha=0.3, linewidth=0.5)
    avg_a = np.mean(class_a_epochs, axis=0)
    ax1.plot(t_epoch, avg_a, color='#FF5722', linewidth=2.5, label='Class A (avg)')
    
    for ep in class_b_epochs:
        ax1.plot(t_epoch, ep, color='#2196F3', alpha=0.3, linewidth=0.5)
    avg_b = np.mean(class_b_epochs, axis=0)
    ax1.plot(t_epoch, avg_b, color='#2196F3', linewidth=2.5, label='Class B (avg)')
    
    ax1.axvline(0, color='white', linestyle=':', alpha=0.5, linewidth=1)
    ax1.set_title('ERP Overlay: All Trials + Grand Average', color='white', 
                  fontsize=11, fontweight='bold')
    ax1.set_xlabel('Time (s)', color='white', fontsize=9)
    ax1.set_ylabel('Amplitude (uV)', color='white', fontsize=9)
    ax1.legend(fontsize=9, facecolor='#0a0a23', edgecolor='#444', labelcolor='white')
    ax1.tick_params(colors='white', labelsize=8)
    for spine in ax1.spines.values():
        spine.set_color('#333')
    
    # Right: Grand average comparison with confidence
    ax2.set_facecolor('#0a0a23')
    ax2.plot(t_epoch, avg_a, color='#FF5722', linewidth=2, label='Class A')
    ax2.plot(t_epoch, avg_b, color='#2196F3', linewidth=2, label='Class B')
    
    # Confidence band (simulated)
    std_a = np.std(class_a_epochs, axis=0)
    std_b = np.std(class_b_epochs, axis=0)
    ax2.fill_between(t_epoch, avg_a - std_a, avg_a + std_a, color='#FF5722', alpha=0.15)
    ax2.fill_between(t_epoch, avg_b - std_b, avg_b + std_b, color='#2196F3', alpha=0.15)
    
    # Difference
    diff = avg_a - avg_b
    ax2_twin = ax2.twinx()
    ax2_twin.plot(t_epoch, diff, color='#4CAF50', linewidth=1.5, linestyle='--', alpha=0.6, label='A - B')
    ax2_twin.set_ylabel('Difference', color='#4CAF50', fontsize=8)
    ax2_twin.tick_params(axis='y', colors='#4CAF50', labelsize=7)
    
    ax2.axvline(0, color='white', linestyle=':', alpha=0.5, linewidth=1)
    ax2.set_title('Grand Average with Std Bands', color='white', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Time (s)', color='white', fontsize=9)
    ax2.set_ylabel('Amplitude (uV)', color='white', fontsize=9)
    ax2.legend(fontsize=9, facecolor='#0a0a23', edgecolor='#444', labelcolor='white', loc='upper left')
    ax2.tick_params(colors='white', labelsize=8)
    for spine in ax2.spines.values():
        spine.set_color('#333')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day18_plot_4.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


if __name__ == '__main__':
    print("Day 18: Event Marking & Epoch Extraction UI")
    print("=" * 50)
    plot1_event_marking_arch()
    plot2_eeg_events_epochs()
    plot3_artifact_rejection()
    plot4_erp_overlay()
    print("\n✅ Day 18 所有图表生成完毕!")
