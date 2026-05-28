"""
Widgets Module
===============
Reusable visualization components for BCI data.
"""
from .waveform import EEGWaveformWidget
from .spectrum import SpectrumWidget
from .topomap import TopomapWidget
from .result_panel import ResultPanel

__all__ = ['EEGWaveformWidget', 'SpectrumWidget', 'TopomapWidget', 'ResultPanel']
