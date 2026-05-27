"""
Decoder Module
===============
BCI Decoding: SSVEP, Motor Imagery, P300
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
    """SSVEP detector using CCA"""

    def __init__(self, target_freqs: List[float], fs: float, n_harmonics: int = 5):
        self.target_freqs = target_freqs
        self.fs = fs
        self.n_harmonics = n_harmonics
        self.templates: Dict[float, np.ndarray] = self._generate_templates()

    def _generate_templates(self) -> Dict[float, np.ndarray]:
        """Generate reference signal templates"""
        templates = {}
        duration = 1.0
        n_samples = int(duration * self.fs)
        t = np.arange(n_samples) / self.fs

        for freq in self.target_freqs:
            template = []
            for h in range(1, self.n_harmonics + 1):
                template.append(np.sin(2 * np.pi * h * freq * t))
                template.append(np.cos(2 * np.pi * h * freq * t))
            templates[freq] = np.array(template)
        return templates

    def _cca_score(self, data: np.ndarray, freq: float) -> float:
        """Calculate CCA correlation score"""
        try:
            X = data  # (n_channels, n_samples)
            Y = self.templates[freq]  # (2*n_harmonics, n_samples)

            C_xx = np.cov(X)
            C_yy = np.cov(Y)
            C_xy = X @ Y.T

            C_xx_inv = np.linalg.inv(C_xx)
            C_yy_inv = np.linalg.inv(C_yy)

            r = np.corrcoef(C_xx_inv @ C_xy @ C_yy_inv @ Y)[0, 1]
            return abs(r) if not np.isnan(r) else 0.0
        except np.linalg.LinAlgError:
            return 0.0

    def detect(self, data: np.ndarray) -> Tuple[int, np.ndarray]:
        """Detect SSVEP target

        Args:
            data: EEG data (n_channels, n_samples)

        Returns:
            (target_index, all_scores)
        """
        scores = [self._cca_score(data, freq) for freq in self.target_freqs]
        return int(np.argmax(scores)), np.array(scores)


class MIDecoder:
    """Motor Imagery decoder"""

    def __init__(self, fs: float, band: Tuple[float, float] = (8, 30)):
        self.fs = fs
        self.band = band

    def extract_features(self, data: np.ndarray) -> np.ndarray:
        """Extract MI features (band power)"""
        from scipy import signal

        features = []
        for ch in range(data.shape[0]):
            nyq = 0.5 * self.fs
            low, high = self.band[0] / nyq, self.band[1] / nyq
            b, a = signal.butter(4, [low, high], btype='band')
            filtered = signal.filtfilt(b, a, data[ch])
            power = np.mean(filtered ** 2)
            features.append(power)
        return np.array(features)

    def decode(self, epochs_data: np.ndarray, labels: np.ndarray,
               cv_folds: int = 5) -> DecodeResult:
        """Decode MI epochs"""
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
        from sklearn.model_selection import cross_val_score

        X = np.array([self.extract_features(epoch) for epoch in epochs_data])
        y = labels

        clf = LinearDiscriminantAnalysis()
        scores = cross_val_score(clf, X, y, cv=cv_folds)

        return DecodeResult(
            accuracy=scores.mean(),
            std=scores.std(),
            cv_scores=scores.tolist(),
            method='lda'
        )


class DecoderFactory:
    """Factory for creating decoders"""

    @staticmethod
    def create(method: str, **kwargs) -> SSVEPDetector | MIDecoder:
        if method == 'ssvep':
            return SSVEPDetector(**kwargs)
        elif method == 'mi':
            return MIDecoder(**kwargs)
        else:
            raise ValueError(f"Unknown decoder method: {method}")


def decode(epochs_data: np.ndarray, labels: np.ndarray,
           method: str = 'lda', cv_folds: int = 5) -> DecodeResult:
    """Convenience function for decoding"""
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.model_selection import cross_val_score

    clf = LinearDiscriminantAnalysis()
    scores = cross_val_score(clf, epochs_data, labels, cv=cv_folds)

    return DecodeResult(
        accuracy=scores.mean(),
        std=scores.std(),
        cv_scores=scores.tolist(),
        method=method
    )