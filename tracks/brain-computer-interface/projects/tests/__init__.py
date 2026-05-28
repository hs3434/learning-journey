"""
Test Module
==========
Unit tests for BCI Pipeline components
"""

import pytest
import numpy as np
from pathlib import Path


class TestFilterConfig:
    """Test filtering configuration"""

    def test_filter_config_validation(self):
        from bci.config import FilterConfig
        cfg = FilterConfig(l_freq=0.5, h_freq=40)
        assert cfg.validate() == True

    def test_filter_config_invalid(self):
        from bci.config import FilterConfig
        cfg = FilterConfig(l_freq=40, h_freq=0.5)
        with pytest.raises(ValueError):
            cfg.validate()

    def test_filter_config_defaults(self):
        from bci.config import FilterConfig
        cfg = FilterConfig()
        assert cfg.l_freq == 0.5
        assert cfg.h_freq == 40.0
        assert cfg.notch_freqs == [50, 100]


class TestPreprocessor:
    """Test preprocessing functions"""

    def test_bandpass_filter_shape(self):
        from bci.preprocessor import Preprocessor
        import mne

        # Create synthetic raw data
        sfreq = 256
        n_channels = 3
        duration = 1
        n_samples = sfreq * duration
        data = np.random.randn(n_channels, n_samples)
        info = mne.create_info(ch_names=[f'EEG {i:02d}' for i in range(n_channels)], sfreq=sfreq, ch_types='eeg')
        raw = mne.io.RawArray(data, info)

        # Apply bandpass filter
        proc = Preprocessor(raw)
        proc.bandpass(l_freq=1.0, h_freq=40.0)

        # Check shape unchanged
        assert proc.raw.get_data().shape == (n_channels, n_samples)

    def test_bandpass_filter_freq_response(self):
        from bci.preprocessor import Preprocessor
        import mne

        sfreq = 256
        n_channels = 1
        n_samples = 2560
        # Create 10 Hz sin wave + noise
        t = np.arange(n_samples) / sfreq
        signal = np.sin(2 * np.pi * 10 * t) + 0.1 * np.random.randn(n_samples)
        info = mne.create_info(ch_names=['EEG 00'], sfreq=sfreq, ch_types='eeg')
        raw = mne.io.RawArray(signal.reshape(1, -1), info)

        proc = Preprocessor(raw)
        proc.bandpass(l_freq=1.0, h_freq=20.0)  # Pass 10 Hz, block 40+ Hz

        # Check amplitude preserved for passband
        filtered = proc.raw.get_data()[0]
        amp_ratio = np.abs(filtered).mean() / np.abs(signal).mean()
        assert 0.3 < amp_ratio < 1.5  # Should preserve signal

    def test_notch_filter(self):
        from bci.preprocessor import Preprocessor
        import mne

        sfreq = 256
        n_channels = 1
        n_samples = 2560
        # Create 50 Hz sin wave
        t = np.arange(n_samples) / sfreq
        signal = np.sin(2 * np.pi * 50 * t)
        info = mne.create_info(ch_names=['EEG 00'], sfreq=sfreq, ch_types='eeg')
        raw = mne.io.RawArray(signal.reshape(1, -1), info)

        proc = Preprocessor(raw)
        proc.notch(freqs=[50])

        # Check 50 Hz component reduced
        filtered = proc.raw.get_data()[0]
        fft = np.fft.fft(filtered)
        freqs = np.fft.fftfreq(n_samples, 1/sfreq)
        idx_50 = np.argmin(np.abs(freqs - 50))
        power_50 = np.abs(fft[idx_50])
        power_10 = np.abs(fft[np.argmin(np.abs(freqs - 10))])

        # 50 Hz should be much smaller than 10 Hz after notch
        assert power_50 < power_10


class TestDecoder:
    """Test decoding functions"""

    def test_cca_score(self):
        from bci.decoder import SSVEPDetector

        detector = SSVEPDetector(target_freqs=[10.0, 12.0], fs=500)

        # Create test signal (10 Hz)
        t = np.arange(500) / 500
        signal = np.sin(2 * np.pi * 10 * t).reshape(1, -1)

        idx, scores = detector.decode(signal)
        assert idx in [0, 1]  # Should detect one of the targets
        assert len(scores) == 2

    def test_decoder_invalid_config(self):
        from bci.decoder import SSVEPDetector
        with pytest.raises(ValueError):
            SSVEPDetector(target_freqs=[], fs=500)  # Empty freqs


class TestPipeline:
    """Test pipeline integration"""

    def test_pipeline_config(self):
        from bci.config import PipelineConfig
        config = PipelineConfig()
        assert config.filter.l_freq == 0.5
        assert config.epoch.tmin == -0.2

    def test_pipeline_result_dataclass(self):
        from bci.pipeline import PipelineResult

        result = PipelineResult(success=True, accuracy=0.85, std=0.05)
        assert result.success == True
        assert result.accuracy == 0.85
        assert result.std == 0.05
        assert result.steps_completed == []
        assert result.errors == []


class TestLoader:
    """Test data loader"""

    def test_loader_import(self):
        from bci.loader import DataLoader
        assert DataLoader is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])