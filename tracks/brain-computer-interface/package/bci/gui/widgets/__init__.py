"""
Widgets Module
===============
Reusable visualization components for BCI data.
"""
from .waveform import EEGWaveformWidget
from .spectrum import SpectrumWidget
from .topomap import TopomapWidget
from .result_panel import ResultPanel
from .info_panel import EEGInfoPanel
from .step_strip import StepStrip, StepStatus

__all__ = ['EEGWaveformWidget', 'SpectrumWidget', 'TopomapWidget', 'ResultPanel',
           'EEGInfoPanel', 'StepStrip', 'StepStatus']