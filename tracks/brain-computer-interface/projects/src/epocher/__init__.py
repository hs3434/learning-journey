"""
Epocher Module
==============
Event detection and epoch extraction
"""

from typing import Optional, Dict, Tuple, List
import logging
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EpochStats:
    """Epoch extraction statistics"""
    n_epochs: int
    n_rejected: int
    rejection_rate: float
    duration: float


class Epocher:
    """Event/Epoch processor"""

    def __init__(self, raw: 'mne.io.Raw', config: Optional['EpochConfig'] = None):
        self.raw = raw
        self.config = config
        self.events = None
        self.epochs = None

    def find_events(self, stim_channel: Optional[str] = None,
                    min_duration: float = 0.001) -> np.ndarray:
        """Find events in the data

        Args:
            stim_channel: Stimulus channel name. If None, uses default.
            min_duration: Minimum event duration (s)

        Returns:
            Events array (n_events, 3)
        """
        logger.info("Finding events")
        self.events = self.raw.find_event_overlap(
            stim_channel=stim_channel,
            min_duration=min_duration
        )
        logger.info(f"Found {len(self.events)} events")
        return self.events

    def extract_epochs(self, events: Optional[np.ndarray] = None,
                      event_id: Optional[Dict[str, int]] = None,
                      tmin: float = -0.2, tmax: float = 0.5,
                      baseline: Tuple = (None, 0),
                      preload: bool = True) -> 'mne.Epochs':
        """Extract epochs around events

        Args:
            events: Events array. If None, uses self.events
            event_id: Event ID mapping (e.g., {'left': 1, 'right': 2})
            tmin: Start time relative to event (s)
            tmax: End time relative to event (s)
            baseline: Baseline correction window
            preload: Whether to load data into memory

        Returns:
            MNE Epochs object
        """
        if events is None:
            events = self.events
        if events is None:
            raise ValueError("No events found, call find_events() first")

        if event_id is None:
            # Auto-generate event IDs from unique event values
            unique_events = np.unique(events[:, 2])
            event_id = {f'event_{int(e)}': int(e) for e in unique_events}

        logger.info(f"Extracting epochs: {tmin}s to {tmax}s, baseline={baseline}")
        from mne import Epochs

        self.epochs = Epochs(
            self.raw, events, event_id,
            tmin=tmin, tmax=tmax,
            baseline=baseline,
            preload=preload,
            reject=self.config.reject_threshold if self.config else None
        )

        n_rejected = len(self.epochs.drop_log)
        logger.info(f"Extracted {len(self.epochs)} epochs, "
                   f"{n_rejected} rejected ({n_rejected/len(self.epochs)*100:.1f}%)")

        return self.epochs

    def get_stats(self) -> EpochStats:
        """Get epoch extraction statistics"""
        if self.epochs is None:
            raise RuntimeError("No epochs extracted")
        n_rejected = len(self.epochs.drop_log)
        return EpochStats(
            n_epochs=len(self.epochs),
            n_rejected=n_rejected,
            rejection_rate=n_rejected / len(self.epochs) if len(self.epochs) > 0 else 0,
            duration=self.epochs.tmax - self.epochs.tmin
        )

    def get_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get epochs data and labels

        Returns:
            (data, labels) tuple
        """
        if self.epochs is None:
            raise RuntimeError("No epochs extracted")
        data = self.epochs.get_data()
        labels = self.epochs.events[:, 2]
        return data, labels


def create_epochs(raw: 'mne.io.Raw', events: np.ndarray,
                  event_id: Dict[str, int], **kwargs) -> 'mne.Epochs':
    """Convenience function to create epochs"""
    epocher = Epocher(raw)
    return epocher.extract_epochs(events, event_id, **kwargs)