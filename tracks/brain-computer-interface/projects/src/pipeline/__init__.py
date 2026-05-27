"""
Pipeline Module
================
BCI Pipeline Orchestrator
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from pathlib import Path
import logging
from dataclasses import dataclass, field

if TYPE_CHECKING:
    import numpy as np
    import mne

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Pipeline execution result"""
    success: bool
    accuracy: Optional[float] = None
    std: Optional[float] = None
    steps_completed: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    output_files: List[Path] = field(default_factory=list)


class BCIPipeline:
    """
    BCI Signal Processing Pipeline
    ================================
    Orchestrates: Load → Preprocess → Epoch → Decode → Report
    """

    def __init__(self, config: 'PipelineConfig'):
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.raw: Optional['mne.io.Raw'] = None
        self.epochs: Optional['mne.Epochs'] = None
        self.events: Optional['np.ndarray'] = None
        self.result: Optional[PipelineResult] = None

        self._steps: List[str] = []

    def load(self, filepath: Path | str) -> 'BCIPipeline':
        """Load EEG data"""
        from loader import DataLoader

        self.logger.info(f"Loading data: {filepath}")
        try:
            loader = DataLoader(self.config)
            self.raw = loader.load(filepath, preload=True)
            self._steps.append('load')
            self.logger.info(f"Loaded: {len(self.raw.ch_names)} channels")
            return self
        except Exception as e:
            self.logger.error(f"Load failed: {e}")
            raise

    def preprocess(self) -> 'BCIPipeline':
        """Preprocess data"""
        from preprocessor import preprocess

        self.logger.info("Preprocessing")
        try:
            self.raw = preprocess(self.raw, self.config.filter)
            self._steps.append('preprocess')
            self.logger.info("Preprocessing done")
            return self
        except Exception as e:
            self.logger.error(f"Preprocess failed: {e}")
            raise

    def create_epochs(self, events: Optional['np.ndarray'] = None,
                      event_id: Optional[Dict[str, int]] = None) -> 'BCIPipeline':
        """Create epochs"""
        from epocher import Epocher

        self.logger.info("Creating epochs")
        try:
            epocher = Epocher(self.raw, self.config.epoch)

            if events is None:
                events = epocher.find_events()
                self.events = events

            self.epochs = epocher.extract_epochs(
                events, event_id,
                tmin=self.config.epoch.tmin,
                tmax=self.config.epoch.tmax,
                baseline=self.config.epoch.baseline
            )
            self._steps.append('create_epochs')
            self.logger.info(f"Created {len(self.epochs)} epochs")
            return self
        except Exception as e:
            self.logger.error(f"Epoch creation failed: {e}")
            raise

    def decode(self) -> 'BCIPipeline':
        """Decode epochs"""
        from decoder import decode as decode_fn

        self.logger.info("Decoding")
        try:
            data = self.epochs.get_data()
            labels = self.epochs.events[:, 2]

            result = decode_fn(data, labels, method=self.config.decode.method,
                               cv_folds=self.config.decode.cv_folds)

            self.result = PipelineResult(
                success=True,
                accuracy=result.accuracy,
                std=result.std,
                steps_completed=self._steps.copy()
            )
            self._steps.append('decode')
            self.logger.info(f"Decoding done: accuracy={result.accuracy:.3f}")
            return self
        except Exception as e:
            self.logger.error(f"Decode failed: {e}")
            raise

    def run(self, filepath: Path | str,
            events: Optional['np.ndarray'] = None,
            event_id: Optional[Dict[str, int]] = None) -> PipelineResult:
        """
        Run complete pipeline

        Args:
            filepath: Path to EEG file
            events: Events array (optional)
            event_id: Event ID dict (optional)

        Returns:
            PipelineResult
        """
        self.logger.info("=" * 50)
        self.logger.info("Starting BCI Pipeline")
        self.logger.info("=" * 50)

        try:
            self.load(filepath)
            self.preprocess()
            self.create_epochs(events, event_id)
            self.decode()

            self.logger.info("Pipeline completed successfully")
            return self.result

        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            return PipelineResult(
                success=False,
                errors=[str(e)],
                steps_completed=self._steps
            )

    def save_results(self, output_dir: Optional[Path] = None) -> List[Path]:
        """Save pipeline results"""
        if output_dir is None:
            output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved = []

        if self.epochs is not None:
            epochs_path = output_dir / 'epochs.fif'
            self.epochs.save(epochs_path, overwrite=True)
            saved.append(epochs_path)

        import json
        results_path = output_dir / 'results.json'
        with open(results_path, 'w') as f:
            json.dump({
                'accuracy': self.result.accuracy if self.result else None,
                'std': self.result.std if self.result else None,
                'steps': self._steps
            }, f, indent=2)
        saved.append(results_path)

        self.logger.info(f"Saved {len(saved)} files to {output_dir}")
        return saved


def run_pipeline(config: 'PipelineConfig', filepath: Path | str) -> PipelineResult:
    """Convenience function to run pipeline"""
    pipeline = BCIPipeline(config)
    return pipeline.run(filepath)