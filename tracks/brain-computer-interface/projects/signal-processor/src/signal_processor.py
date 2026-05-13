"""
EEG Signal Processor
EEG 信号处理工具：滤波、FFT、特征提取
"""

import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq
from typing import Tuple, Optional


class SignalProcessor:
    """EEG 信号处理器"""

    @staticmethod
    def bandpass_filter(
        data: np.ndarray,
        lowcut: float,
        highcut: float,
        fs: float,
        order: int = 4
    ) -> np.ndarray:
        """带通滤波

        Args:
            data: 输入数据 (n_channels, n_samples) 或 (n_samples,)
            lowcut: 低频截止 (Hz)
            highcut: 高频截止 (Hz)
            fs: 采样率 (Hz)
            order: 滤波器阶数

        Returns:
            滤波后的数据
        """
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq

        # 确保频率在有效范围内
        low = max(0.001, min(low, 0.999))
        high = max(0.001, min(high, 0.999))

        b, a = signal.butter(order, [low, high], btype='band')
        return signal.filtfilt(b, a, data)

    @staticmethod
    def lowpass_filter(
        data: np.ndarray,
        cutoff: float,
        fs: float,
        order: int = 4
    ) -> np.ndarray:
        """低通滤波"""
        nyq = 0.5 * fs
        fc = cutoff / nyq
        fc = max(0.001, min(fc, 0.999))

        b, a = signal.butter(order, fc, btype='low')
        return signal.filtfilt(b, a, data)

    @staticmethod
    def notch_filter(
        data: np.ndarray,
        freq: float,
        fs: float,
        Q: float = 30
    ) -> np.ndarray:
        """去除工频干扰（notch 滤波）

        Args:
            data: 输入数据
            freq: 要去除的频率 (Hz)，如 50 或 60
            fs: 采样率 (Hz)
            Q: 品质因子，值越高滤波器越窄
        """
        w0 = freq / (fs / 2)
        w0 = max(0.001, min(w0, 0.999))

        b, a = signal.iirnotch(w0, Q)
        return signal.filtfilt(b, a, data)

    @staticmethod
    def compute_psd(
        data: np.ndarray,
        fs: float,
        nperseg: int = 256
    ) -> Tuple[np.ndarray, np.ndarray]:
        """计算功率谱密度 (Welch's method)

        Returns:
            freqs: 频率数组
            psd: 功率谱密度
        """
        freqs, psd = signal.welch(data, fs, nperseg=nperseg)
        return freqs, psd

    @staticmethod
    def compute_stft(
        data: np.ndarray,
        fs: float,
        nperseg: int = 256,
        noverlap: Optional[int] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """计算短时傅里叶变换 (STFT)

        Returns:
            freqs: 频率数组
            times: 时间数组
            Sxx: 时频谱图
        """
        if noverlap is None:
            noverlap = nperseg // 2

        freqs, times, Sxx = signal.spectrogram(
            data, fs, nperseg=nperseg, noverlap=noverlap
        )
        return freqs, times, Sxx

    @staticmethod
    def extract_band_power(
        data: np.ndarray,
        fs: float,
        band: Tuple[float, float],
        nperseg: int = 256
    ) -> float:
        """提取指定频段的功率

        Args:
            data: 输入数据
            fs: 采样率
            band: 频段 (low_freq, high_freq)

        Returns:
            频段平均功率
        """
        freqs, psd = SignalProcessor.compute_psd(data, fs, nperseg)

        band_indices = (freqs >= band[0]) & (freqs <= band[1])
        if not np.any(band_indices):
            return 0.0

        return np.mean(psd[band_indices])

    @staticmethod
    def detect_peaks(
        data: np.ndarray,
        threshold: float = 0.5
    ) -> np.ndarray:
        """检测峰值

        Args:
            data: 输入数据
            threshold: 阈值（相对于最大值）

        Returns:
            峰值索引数组
        """
        from scipy.signal import find_peaks

        height = threshold * np.max(data)
        peaks, _ = find_peaks(data, height=height)
        return peaks

    @staticmethod
    def baseline_correct(
        data: np.ndarray,
        baseline_start: float,
        baseline_end: float,
        fs: float
    ) -> np.ndarray:
        """基线校正

        Args:
            data: 输入数据
            baseline_start: 基线开始时间（秒）
            baseline_end: 基线结束时间（秒）
            fs: 采样率
        """
        start_idx = int(baseline_start * fs)
        end_idx = int(baseline_end * fs)

        baseline = np.mean(data[..., start_idx:end_idx], axis=-1, keepdims=True)
        return data - baseline


# EEG 频段定义
EEG_BANDS = {
    'delta': (0.5, 4),
    'theta': (4, 8),
    'alpha': (8, 13),
    'beta': (13, 30),
    'gamma': (30, 100)
}


def extract_eeg_features(data: np.ndarray, fs: float) -> dict:
    """提取 EEG 特征

    Args:
        data: EEG 数据 (n_samples,) 或 (n_channels, n_samples)
        fs: 采样率

    Returns:
        特征字典
    """
    processor = SignalProcessor()
    features = {}

    if data.ndim == 1:
        data = data[np.newaxis, ...]

    for band_name, band_range in EEG_BANDS.items():
        band_power = processor.extract_band_power(data, fs, band_range)
        features[f'{band_name}_power'] = band_power

    return features


if __name__ == '__main__':
    print("Signal Processor - EEG Signal Processing Utilities")
    print("EEG Bands:", list(EEG_BANDS.keys()))