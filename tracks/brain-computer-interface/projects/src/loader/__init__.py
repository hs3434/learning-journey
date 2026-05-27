"""
Data Loader Module
==================
EEG Data Loading - MNE/EEGLAB/BrainVision support
"""

from pathlib import Path
from typing import Optional, Tuple, List
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LoaderResult:
    """Result of data loading"""
    raw: 'mne.io.Raw'  # Forward reference to avoid circular import
    filepath: Path
    format: str
    n_channels: int
    duration: float
    sfreq: float


class DataLoader:
    """EEG Data Loader - supports multiple formats"""

    SUPPORTED_FORMATS = {
        '.edf': 'edf',
        '.fif': 'fif',
        '.set': 'eeglab',
        '.vhdr': 'brainvision',
        '.fdt': 'eeglab',
    }

    def __init__(self, config: Optional['PipelineConfig'] = None):
        self.config = config
        self.raw = None

    def load(self, filepath: Path | str, preload: bool = True) -> 'Raw':
        """Load EEG data from file

        Args:
            filepath: Path to EEG file
            preload: Whether to load data into memory

        Returns:
            MNE Raw object
        """
        filepath = Path(filepath)
        suffix = filepath.suffix.lower()

        logger.info(f"Loading {suffix} file: {filepath}")

        if suffix == '.edf' or suffix == '.EDF':
            import mne
            self.raw = mne.io.read_raw_edf(filepath, preload=preload)
        elif suffix == '.fif':
            import mne
            self.raw = mne.io.read_raw_fif(filepath, preload=preload)
        elif suffix == '.set':
            import mne
            self.raw = mne.io.read_raw_eeglab(filepath, preload=preload)
        elif suffix == '.vhdr':
            import mne
            self.raw = mne.io.read_raw_brainvision(filepath, preload=preload)
        else:
            raise ValueError(f"Unsupported format: {suffix}")

        logger.info(f"Loaded {len(self.raw.ch_names)} channels, "
                   f"{self.raw.n_times/self.raw.info['sfreq']:.1f}s, "
                   f"{self.raw.info['sfreq']} Hz")

        return self.raw

    def get_info(self) -> dict:
        """Get raw info as dict"""
        if self.raw is None:
            raise RuntimeError("No data loaded, call load() first")
        return {
            'n_channels': len(self.raw.ch_names),
            'sfreq': self.raw.info['sfreq'],
            'duration': self.raw.n_times / self.raw.info['sfreq'],
            'channels': self.raw.ch_names,
            'lowpass': self.raw.info.get('lowpass'),
            'highpass': self.raw.info.get('highpass'),
        }

    def get_data(self, start: Optional[int] = None, stop: Optional[int] = None,
                 picks: str = 'eeg') -> Tuple['ndarray', 'ndarray']:
        """Get data and times

        Args:
            start: Start sample
            stop: Stop sample
            picks: Channel selection

        Returns:
            (data, times) tuple
        """
        if self.raw is None:
            raise RuntimeError("No data loaded")
        data = self.raw.get_data(picks=picks, start=start, stop=stop)
        times = self.raw.times[start:stop]
        return data, times


def load_raw(filepath: Path | str, **kwargs) -> 'mne.io.Raw':
    """Convenience function to load EEG data"""
    loader = DataLoader()
    return loader.load(filepath, **kwargs)