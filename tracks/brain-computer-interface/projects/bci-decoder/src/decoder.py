"""
BCI Decoder
SSVEP 和 MI (运动想象) 解码实现
"""

import numpy as np
from typing import List, Tuple, Optional


class SSVEPDetector:
    """SSVEP 检测器

    使用 CCA (Canonical Correlation Analysis) 方法检测 SSVEP 目标
    """

    def __init__(self, target_freqs: List[float], fs: float, n_harmonics: int = 5):
        """初始化 SSVEP 检测器

        Args:
            target_freqs: 目标频率列表 (Hz)
            fs: 采样率 (Hz)
            n_harmonics: 使用的谐波数量
        """
        self.target_freqs = target_freqs
        self.fs = fs
        self.n_harmonics = n_harmonics
        self.templates = {}

        # 预计算参考信号模板
        for freq in target_freqs:
            self.templates[freq] = self._generate_template(freq)

    def _generate_template(self, freq: float) -> np.ndarray:
        """生成参考信号模板

        Args:
            freq: 频率 (Hz)

        Returns:
            模板数组 (n_harmonics, n_samples)
        """
        duration = 1.0  # 1秒模板
        n_samples = int(duration * self.fs)
        t = np.arange(n_samples) / self.fs

        template = np.zeros((self.n_harmonics, n_samples))
        for h in range(1, self.n_harmonics + 1):
            # 正弦
            template[h - 1] = np.sin(2 * np.pi * h * freq * t)
            # 余弦
            template = np.vstack([template, np.cos(2 * np.pi * h * freq * t)])

        return template  # (2*n_harmonics, n_samples)

    def _cca_score(self, data: np.ndarray, freq: float) -> float:
        """计算 CCA 分数

        Args:
            data: EEG 数据 (n_channels, n_samples)
            freq: 目标频率

        Returns:
            CCA 相关系数
        """
        template = self.templates[freq]  # (2n, T)

        try:
            # 数据矩阵
            X = data  # (n_channels, n_samples)

            # 计算互相关矩阵
            C_xx = np.cov(X)
            C_yy = np.cov(template)
            C_xy = X @ template.T

            # CCA
            A = np.linalg.solve(C_yy, C_xy.T)
            B = np.linalg.solve(C_xx, C_xy)

            # 典范相关系数
            R = np.corrcoef(np.dot(B.T, X), np.dot(A.T, template))
            r = R[0, 1]

            return np.abs(r) if not np.isnan(r) else 0.0

        except np.linalg.LinAlgError:
            return 0.0

    def detect(self, data: np.ndarray) -> Tuple[int, np.ndarray]:
        """检测 SSVEP 目标

        Args:
            data: EEG 数据 (n_channels, n_samples)

        Returns:
            (检测到的目标索引, 所有目标分数)
        """
        scores = []
        for freq in self.target_freqs:
            score = self._cca_score(data, freq)
            scores.append(score)

        scores = np.array(scores)
        return int(np.argmax(scores)), scores


class MIDecoder:
    """运动想象 (MI) 解码器

    使用滤波后信号的频带功率特征进行分类
    """

    def __init__(self, fs: float):
        self.fs = fs
        # MI 典型频段: C3 (left) -> mu (8-13Hz), C4 (right) -> mu (8-13Hz)
        self.band = (8, 13)

    @staticmethod
    def compute_band_power(data: np.ndarray, fs: float, band: Tuple[float, float]) -> float:
        """计算频带功率"""
        from scipy import signal

        # 设计带通滤波器
        nyq = 0.5 * fs
        low, high = band[0] / nyq, band[1] / nyq
        b, a = signal.butter(4, [low, high], btype='band')

        # 滤波
        filtered = signal.filtfilt(b, a, data)

        # 计算功率
        return np.mean(filtered ** 2)

    def extract_features(self, data: np.ndarray) -> np.ndarray:
        """提取 MI 特征

        Args:
            data: EEG 数据 (n_channels, n_samples)

        Returns:
            特征向量
        """
        n_channels = data.shape[0]
        features = []

        for ch in range(n_channels):
            power = self.compute_band_power(data[ch], self.fs, self.band)
            features.append(power)

        return np.array(features)


class BCIDecoderFactory:
    """BCI 解码器工厂"""

    @staticmethod
    def create_decoder(
        decoder_type: str,
        fs: float,
        **kwargs
    ) -> 'BCIDecoder':
        """创建解码器

        Args:
            decoder_type: 'ssvep' 或 'mi'
            fs: 采样率

        Returns:
            解码器实例
        """
        if decoder_type.lower() == 'ssvep':
            target_freqs = kwargs.get('target_freqs', [10.0, 12.0, 15.0])
            return SSVEPDetector(target_freqs, fs)

        elif decoder_type.lower() == 'mi':
            return MIDecoder(fs)

        else:
            raise ValueError(f"Unknown decoder type: {decoder_type}")


if __name__ == '__main__':
    print("BCI Decoder - SSVEP and MI Decoding")
    print("Usage: detector = BCIDecoderFactory.create_decoder('ssvep', fs=500)")