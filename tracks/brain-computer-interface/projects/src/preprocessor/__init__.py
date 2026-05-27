"""
Preprocessor Module
====================
Signal preprocessing: filtering, ICA, artifact removal
"""

from __future__ import annotations
from typing import Optional, List, Tuple, TYPE_CHECKING
import logging
import numpy as np

if TYPE_CHECKING:
    import mne

logger = logging.getLogger(__name__)


class Preprocessor:
    """EEG Signal Preprocessor"""

    def __init__(self, raw: 'mne.io.Raw', config: Optional['FilterConfig'] = None):
        self.raw = raw
        self.config = config

    def bandpass(self, l_freq: float, h_freq: float) -> 'Preprocessor':
        """Apply bandpass filter

        Args:
            l_freq: Low frequency cutoff (Hz)
            h_freq: High frequency cutoff (Hz)

        Returns:
            self
        """
        logger.info(f"Bandpass filter: {l_freq}-{h_freq} Hz")
        self.raw.filter(l_freq=l_freq, h_freq=h_freq)
        return self

    def notch(self, freqs: List[int], Q: float = 30) -> 'Preprocessor':
        """Apply notch filter to remove powerline noise

        Args:
            freqs: Frequencies to notch (e.g., [50, 100])
            Q: Quality factor

        Returns:
            self
        """
        for freq in freqs:
            logger.info(f"Notch filter: {freq} Hz")
            self.raw.notch_filter(freqs=freq, Q=Q)
        return self

    def set_reference(self, ref: str = 'average') -> 'Preprocessor':
        """Set EEG reference

        Args:
            ref: 'average' or 'single' or list of channel names

        Returns:
            self
        """
        logger.info(f"Setting reference: {ref}")
        self.raw.set_eeg_reference(ref)
        return self

    def interpolate_bad_channels(self, bads: Optional[List[str]] = None) -> 'Preprocessor':
        """Interpolate bad channels

        Args:
            bads: List of bad channel names. If None, uses raw.info['bads']

        Returns:
            self
        """
        if bads is None:
            bads = self.raw.info.get('bads', [])
        if bads:
            logger.info(f"Interpolating bad channels: {bads}")
            self.raw.interpolate_bads(reset_bads=True)
        return self

    def apply_ica(self, n_components: int = 20, random_state: int = 42) -> 'ICA':
        """Apply ICA for artifact removal

        Args:
            n_components: Number of ICA components
            random_state: Random seed

        Returns:
            Fitted ICA object
        """
        from mne.preprocessing import ICA

        logger.info(f"Fitting ICA with {n_components} components")
        ica = ICA(n_components=n_components, random_state=random_state, method='infomax')
        ica.fit(self.raw)

        return ica

    def get_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get preprocessed data and times"""
        return self.raw.get_data(), self.raw.times


def preprocess(raw: 'mne.io.Raw', filter_config: 'FilterConfig') -> 'mne.io.Raw':
    """Convenience function to preprocess raw data"""
    preprocessor = Preprocessor(raw, filter_config)
    preprocessor.bandpass(filter_config.l_freq, filter_config.h_freq)
    if filter_config.notch_freqs:
        preprocessor.notch(filter_config.notch_freqs)
    preprocessor.set_reference('average')
    return preprocessor.raw