"""
Data Source Module
==================
Abstract data source interface for batch and stream modes.
"""
from .base import DataSource
from .file_source import FileSource
from .stream_source import StreamSource

__all__ = ['DataSource', 'FileSource', 'StreamSource']
