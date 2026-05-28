"""
Decoder Module
===============
BCI Decoding: SSVEP, Motor Imagery, LDA

Design:
    DecoderFactory  — 根据 method 字符串创建对应的解码器
    SSVEPDetector   — SSVEP CCA 检测
    MIDecoder       — 运动想象 band power + LDA
    顶层 decode()   — 通过工厂创建解码器并解码

Examples:
    # SSVEP detection
    >>> from bci.decoder import SSVEPDetector
    >>> detector = SSVEPDetector(target_freqs=[15.0, 20.0], fs=256.0)
    >>> target_idx, scores = detector.decode(eeg_data)
    >>> print(f"Target: {target_idx}, Score: {scores[target_idx]:.3f}")

    # Motor Imagery decoding
    >>> from bci.decoder import MIDecoder
    >>> decoder = MIDecoder(fs=256.0, band=(8, 30))
    >>> result = decoder.decode(epochs_data, labels, cv_folds=5)
    >>> print(f"Accuracy: {result.accuracy:.3f} +/- {result.std:.3f}")

    # Factory dispatch
    >>> from bci.decoder import decode
    >>> result = decode(epochs_data, labels, method='ssvep', target_freqs=[15.0, 20.0], fs=256.0)
    >>> result = decode(epochs_data, labels, method='mi', fs=256.0)
    >>> result = decode(epochs_data, labels, method='lda')  # default LDA
"""

from __future__ import annotations
from typing import Optional, Tuple, List, Dict, TYPE_CHECKING
import logging
import numpy as np
from dataclasses import dataclass

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class DecodeResult:
    """Decoding result"""
    accuracy: float
    std: float
    cv_scores: List[float]
    method: str
    feature_importance: Optional[np.ndarray] = None


class SSVEPDetector:
    """SSVEP detector using CCA (Canonical Correlation Analysis)

    Examples:
        >>> detector = SSVEPDetector(target_freqs=[15.0, 20.0], fs=256.0)
        >>> target_idx, scores = detector.decode(eeg_data)
        >>> print(f"Detected target {target_idx}: score={scores[target_idx]:.3f}")
        Detected target 1: score=0.847

        # With custom harmomics
        >>> detector = SSVEPDetector(target_freqs=[8.0, 12.0], fs=128.0, n_harmonics=3)
    """

    def __init__(self, target_freqs: List[float], fs: float, n_harmonics: int = 5):
        self.target_freqs = target_freqs
        self.fs = fs
        self.n_harmonics = n_harmonics
        self.templates: Dict[float, np.ndarray] = self._generate_templates()

    def _generate_templates(self) -> Dict[float, np.ndarray]:
        """Generate sinusoidal reference templates for CCA"""
        templates: Dict[float, np.ndarray] = {}
        duration = 1.0
        n_samples = int(duration * self.fs)
        t = np.arange(n_samples) / self.fs

        for freq in self.target_freqs:
            template: List[np.ndarray] = []
            for h in range(1, self.n_harmonics + 1):
                template.append(np.sin(2 * np.pi * h * freq * t))
                template.append(np.cos(2 * np.pi * h * freq * t))
            templates[freq] = np.array(template)
        return templates

    def _cca_score(self, data: np.ndarray, freq: float) -> float:
        """Calculate CCA correlation score between EEG and reference template"""
        try:
            X = data
            Y = self.templates[freq]

            C_xx = np.cov(X)
            C_yy = np.cov(Y)
            C_xy = X @ Y.T

            C_xx_inv = np.linalg.inv(C_xx)
            C_yy_inv = np.linalg.inv(C_yy)

            corr_result = np.corrcoef(C_xx_inv @ C_xy @ C_yy_inv @ Y)
            r = float(corr_result[0, 1]) if corr_result.ndim == 2 else 0.0
            return abs(r) if not np.isnan(r) else 0.0
        except np.linalg.LinAlgError:
            return 0.0

    def decode(self, data: np.ndarray, *,
               labels: Optional[np.ndarray] = None,
               cv_folds: int = 5) -> Tuple[int, np.ndarray]:
        """Detect which SSVEP target is present

        Args:
            data: EEG data (n_channels, n_samples)
            labels: unused for SSVEP (present for unified API)
            cv_folds: unused for SSVEP (present for unified API)

        Returns:
            (target_index, all_scores)
        """
        scores = [self._cca_score(data, freq) for freq in self.target_freqs]
        return int(np.argmax(scores)), np.array(scores)


class MIDecoder:
    """Motor Imagery decoder using band power features and LDA

    Examples:
        >>> decoder = MIDecoder(fs=256.0, band=(8, 30))
        >>> result = decoder.decode(epochs_data, labels, cv_folds=5)
        >>> print(f"Accuracy: {result.accuracy:.3f} +/- {result.std:.3f}")
        Accuracy: 0.823 +/- 0.051

        # Adjust frequency band for mu/beta rhythms
        >>> decoder = MIDecoder(fs=256.0, band=(10, 14))
    """

    def __init__(self, fs: float, band: Tuple[float, float] = (8, 30)):
        self.fs = fs
        self.band = band

    def extract_features(self, data: np.ndarray) -> np.ndarray:
        """Extract band power features per channel

        Args:
            data: Single epoch data (n_channels, n_samples)

        Returns:
            Feature vector (n_channels,)
        """
        from scipy import signal

        features: List[float] = []
        for ch in range(data.shape[0]):
            nyq = 0.5 * self.fs
            low = self.band[0] / nyq
            high = self.band[1] / nyq
            b, a = signal.butter(4, [low, high], btype='band')  # type: ignore
            filtered = signal.filtfilt(b, a, data[ch])
            power = float(np.mean(filtered ** 2))
            features.append(power)
        return np.array(features)

    def decode(self, epochs_data: np.ndarray, labels: np.ndarray,
               cv_folds: int = 5) -> DecodeResult:
        """Decode MI epochs

        Args:
            epochs_data: (n_epochs, n_channels, n_samples)
            labels: (n_epochs,) class labels
            cv_folds: Cross-validation folds

        Returns:
            DecodeResult with accuracy and cv_scores
        """
        import sklearn.discriminant_analysis  # type: ignore
        import sklearn.model_selection  # type: ignore
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis  # type: ignore
        from sklearn.model_selection import cross_val_score  # type: ignore

        X = np.array([self.extract_features(epoch) for epoch in epochs_data])
        y = labels

        clf = LinearDiscriminantAnalysis()
        scores = cross_val_score(clf, X, y, cv=cv_folds)

        return DecodeResult(
            accuracy=float(scores.mean()),
            std=float(scores.std()),
            cv_scores=scores.tolist(),
            method='mi',
        )


class DecoderFactory:
    """Factory for creating decoders by method name

    Supported methods:
        'ssvep' — SSVEPDetector (CCA-based)
        'mi'    — MIDecoder (band power + LDA)
        'lda'   — raw LDA (no feature extraction)

    Examples:
        >>> detector = DecoderFactory.create('ssvep', target_freqs=[15.0, 20.0], fs=256.0)
        >>> detector = DecoderFactory.create('mi', fs=256.0, band=(8, 30))
    """

    @staticmethod
    def create(method: str, **kwargs) -> SSVEPDetector | MIDecoder:
        if method == 'ssvep':
            return SSVEPDetector(**kwargs)
        if method == 'mi':
            return MIDecoder(**kwargs)
        raise ValueError(f"Unknown decoder method: {method} (expected 'ssvep' or 'mi')")


def from_decoder_class(method: str, **kwargs) -> SSVEPDetector | MIDecoder:
    """Alias for DecoderFactory.create"""
    return DecoderFactory.create(method, **kwargs)


def decode(epochs_data: np.ndarray, labels: np.ndarray,
           method: str = 'lda', cv_folds: int = 5,
           **decoder_kwargs) -> DecodeResult:
    """Decode EEG epochs using the specified method

    Uses DecoderFactory internally to create the appropriate decoder.

    Args:
        epochs_data: (n_epochs, n_channels, n_samples)
        labels: (n_epochs,) class labels
        method: 'lda' (default), 'mi', or 'ssvep'
        cv_folds: Cross-validation folds (mi/lda only)
        **decoder_kwargs: Passed to decoder constructor (e.g., fs, band, target_freqs)

    Returns:
        DecodeResult

    Examples:
        # Default LDA
        >>> result = decode(epochs_data, labels)

        # Motor Imagery with custom settings
        >>> result = decode(epochs_data, labels, method='mi', fs=256.0, band=(8, 30))

        # SSVEP (label-agnostic detection, one trial at a time)
        >>> result = decode(epochs_data, labels, method='ssvep',
        ...                 target_freqs=[15.0, 20.0], fs=256.0)
    """
    if method == 'lda':
        import sklearn.discriminant_analysis  # type: ignore
        import sklearn.model_selection  # type: ignore
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis  # type: ignore
        from sklearn.model_selection import cross_val_score  # type: ignore

        clf = LinearDiscriminantAnalysis()
        # LDA needs 2D input: flatten (n_epochs, n_channels, n_samples) -> (n_epochs, n_channels * n_samples)
        X = epochs_data.reshape(epochs_data.shape[0], -1)
        scores = cross_val_score(clf, X, labels, cv=cv_folds)

        return DecodeResult(
            accuracy=float(scores.mean()),
            std=float(scores.std()),
            cv_scores=scores.tolist(),
            method='lda',
        )

    detector = DecoderFactory.create(method, **decoder_kwargs)

    if method == 'ssvep':
        detector_ssvep: SSVEPDetector = detector  # type: ignore
        accuracies: List[float] = []
        for epoch, lbl in zip(epochs_data, labels):
            target_idx, _ = detector_ssvep.decode(epoch)
            accuracies.append(1.0 if target_idx == lbl else 0.0)
        return DecodeResult(
            accuracy=float(np.mean(accuracies)),
            std=float(np.std(accuracies)),
            cv_scores=accuracies,
            method='ssvep',
        )

    if method == 'mi':
        detector_mi: MIDecoder = detector  # type: ignore
        return detector_mi.decode(epochs_data, labels, cv_folds=cv_folds)

    raise ValueError(f"Unknown decode method: {method}")
