"""
EEG Data Loader
EEG 数据加载与预处理基础工具
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, List, Tuple


class EEGDataLoader:
    """EEG 数据加载器

    支持多种格式：.edf, .fif, .set, .vhdr 等
    """

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.raw = None
        self.info = None
        self._data = None

    def load_raw(self, format: str = 'auto') -> 'EEGDataLoader':
        """加载原始数据

        Args:
            format: 数据格式，'auto' 自动检测

        Returns:
            self
        """
        # TODO: 实现 MNE 加载逻辑
        # import mne
        # self.raw = mne.io.read_raw_xxx(self.filepath, preload=True)
        # self.info = self.raw.info
        pass

    def get_data(
        self,
        start: Optional[int] = 0,
        stop: Optional[int] = None,
        picks: str = 'eeg'
    ) -> np.ndarray:
        """获取指定通道数据

        Args:
            start: 起始采样点
            stop: 结束采样点
            picks: 通道选择（'eeg', 'data', 'all'）

        Returns:
            数据数组 (n_channels, n_samples)
        """
        # TODO: 实现
        pass

    def get_times(self) -> np.ndarray:
        """获取时间轴"""
        if self.raw is None:
            return np.array([])
        return self.raw.times

    def to_dataframe(self) -> pd.DataFrame:
        """转换为 DataFrame"""
        # TODO: 实现
        pass

    def get_channel_names(self) -> List[str]:
        """获取通道名称列表"""
        if self.raw is None:
            return []
        return self.raw.ch_names

    def get_sampling_rate(self) -> float:
        """获取采样率"""
        if self.raw is None:
            return 0.0
        return self.raw.info['sfreq']

    def plot(self, duration: float = 10.0, n_channels: int = 20):
        """绘制 EEG 波形

        Args:
            duration: 显示时长（秒）
            n_channels: 显示通道数
        """
        if self.raw is None:
            print("No data loaded")
            return
        # TODO: 使用 MNE 绘图
        # self.raw.plot(duration=duration, n_channels=n_channels)


def load_edf(filepath: str) -> EEGDataLoader:
    """加载 EDF 文件的便捷函数"""
    loader = EEGDataLoader(filepath)
    loader.load_raw()
    return loader


if __name__ == '__main__':
    print("BCI Data Utils - EEG Data Loader")
    print("Usage: from eeg_loader import EEGDataLoader, load_edf")