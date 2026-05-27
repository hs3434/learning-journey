"""
BCI Pipeline Package
====================
BCI Signal Processing Pipeline - Engineering and Integration

Modules:
    config   - Configuration management
    loader   - Data loading
    preprocessor - Signal preprocessing
    epocher  - Event/epoch extraction
    decoder  - BCI decoding
    pipeline - Pipeline orchestrator
    gui      - Qt GUI (optional)

Usage:
    from src.config import PipelineConfig
    from src.pipeline import BCIPipeline

    config = PipelineConfig()
    pipeline = BCIPipeline(config)
    result = pipeline.run('data.edf')
"""

__version__ = '1.0.0'
__author__ = 'BCI Learning Journey'

# Import main components for easy access
from config import PipelineConfig, FilterConfig, EpochConfig, DecodeConfig
from pipeline import BCIPipeline, PipelineResult

__all__ = [
    'PipelineConfig',
    'FilterConfig',
    'EpochConfig',
    'DecodeConfig',
    'BCIPipeline',
    'PipelineResult',
]