"""
MNE Sample 数据 → epochs (X, y)
================================
任务：听觉 vs 视觉 二分类
- 事件 1+2 (audio L/R) → 类 0
- 事件 3+4 (visual L/R) → 类 1
仅用 EEG 通道（60 ch），去掉 EOG/MEG/STIM。
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import mne


def load_audvis_epochs(
    tmin: float = -0.2,
    tmax: float = 0.5,
    baseline=(-0.2, 0.0),
    decim: int = 1,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """加载 MNE Sample → (X, y, ch_names)

    Returns
    -------
    X : (n_trials, n_channels, n_times) float32
    y : (n_trials,) int  — 0=auditory, 1=visual
    ch_names : list[str]
    """
    data_path = mne.datasets.sample.data_path()
    raw_path = Path(data_path) / "MEG" / "sample" / "sample_audvis_filt-0-40_raw.fif"

    raw = mne.io.read_raw_fif(raw_path, preload=True, verbose="ERROR")

    events = mne.find_events(raw, stim_channel="STI 014", verbose="ERROR")

    # 事件找到后，再选 EEG 通道
    raw.pick(picks=["eeg"], exclude="bads")

    # 二分类合并：1+2 → 0 (audio), 3+4 → 1 (visual)
    event_id_orig = {"aud_l": 1, "aud_r": 2, "vis_l": 3, "vis_r": 4}
    epochs = mne.Epochs(
        raw, events, event_id=event_id_orig,
        tmin=tmin, tmax=tmax, baseline=baseline,
        preload=True, decim=decim, reject=None, verbose="ERROR",
    )

    X = epochs.get_data(copy=True).astype(np.float32) * 1e6  # 单位 μV，量级友好
    labels_orig = epochs.events[:, -1]
    y = np.where(labels_orig <= 2, 0, 1).astype(np.int64)

    return X, y, epochs.ch_names


if __name__ == "__main__":
    X, y, ch = load_audvis_epochs()
    print(f"X: {X.shape} {X.dtype}")
    print(f"y: {y.shape}, classes: {np.unique(y, return_counts=True)}")
    print(f"ch ({len(ch)}): {ch[:5]} ...")
    print(f"X stats: mean={X.mean():.3f}, std={X.std():.3f}, range=[{X.min():.1f}, {X.max():.1f}]")
