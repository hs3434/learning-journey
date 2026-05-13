"""
Engineered BCI Pipeline
工程化的 BCI 处理 Pipeline

特点：
- 配置管理（dataclass）
- 日志系统
- 模块化设计
- 完整错误处理
- 类型提示
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
import logging
import numpy as np


# ===== 配置类 =====

@dataclass
class FilterConfig:
    """滤波配置"""
    lowcut: float = 0.5
    highcut: float = 40.0
    notch_freq: Optional[int] = 50
    order: int = 4


@dataclass
class EpochConfig:
    """Epoch 配置"""
    tmin: float = -0.2
    tmax: float = 0.5
    baseline: Tuple[Optional[float], Optional[float]] = (None, 0)


@dataclass
class PipelineConfig:
    """Pipeline 完整配置"""
    filter_params: FilterConfig = field(default_factory=FilterConfig)
    epoch_params: EpochConfig = field(default_factory=EpochConfig)
    channels: Optional[List[str]] = None
    reference: str = 'average'


# ===== 日志配置 =====

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """配置日志"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# ===== Pipeline 实现 =====

class BCIPipeline:
    """工程化 BCI Pipeline

    完整的数据处理流程：
    1. 加载数据
    2. 预处理（滤波、重参考）
    3. 创建 Epochs
    4. 特征提取
    5. 解码
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.logger = setup_logger(__name__)

        self.raw = None
        self.epochs = None
        self.events = None

        # 统计信息
        self.stats = {
            'steps_completed': [],
            'errors': []
        }

    def load(self, filepath: Path) -> 'BCIPipeline':
        """加载 EEG 数据

        Args:
            filepath: 数据文件路径

        Returns:
            self（支持链式调用）
        """
        self.logger.info(f"Loading data from: {filepath}")

        try:
            # TODO: 使用 MNE 加载
            # import mne
            # self.raw = mne.io.read_raw_xxx(filepath, preload=True)
            # self.logger.info(f"Loaded {len(self.raw.ch_names)} channels, "
            #                  f"{self.raw.n_times} samples")

            self.stats['steps_completed'].append('load')

        except Exception as e:
            self.logger.error(f"Failed to load data: {e}")
            self.stats['errors'].append(('load', str(e)))
            raise

        return self

    def preprocess(self) -> 'BCIPipeline':
        """预处理

        包含：带通滤波、notch 滤波、重参考

        Returns:
            self
        """
        if self.raw is None:
            raise RuntimeError("No data loaded. Call load() first.")

        self.logger.info("Preprocessing data")

        try:
            filt = self.config.filter_params

            # 带通滤波
            self.logger.info(f"Bandpass filter: {filt.lowcut}-{filt.highcut} Hz")
            # self.raw.filter(filt.lowcut, filt.highcut)

            # Notch 滤波
            if filt.notch_freq:
                self.logger.info(f"Notch filter: {filt.notch_freq} Hz")
                # self.raw.notch_filter(filt.notch_freq)

            # 重参考
            self.logger.info(f"Reference: {self.config.reference}")
            # self.raw.set_eeg_reference(self.config.reference)

            self.stats['steps_completed'].append('preprocess')

        except Exception as e:
            self.logger.error(f"Preprocessing failed: {e}")
            self.stats['errors'].append(('preprocess', str(e)))
            raise

        return self

    def create_epochs(
        self,
        events: np.ndarray,
        event_id: Dict[str, int]
    ) -> 'BCIPipeline':
        """创建 Epochs

        Args:
            events: 事件数组 (n_events, 3)
            event_id: 事件 ID 字典

        Returns:
            self
        """
        if self.raw is None:
            raise RuntimeError("No data loaded. Call load() first.")

        self.logger.info(f"Creating epochs with {len(events)} events")

        try:
            epoch_cfg = self.config.epoch_params

            # TODO: 使用 MNE 创建 Epochs
            # self.epochs = mne.Epochs(
            #     self.raw, events, event_id,
            #     tmin=epoch_cfg.tmin,
            #     tmax=epoch_cfg.tmax,
            #     baseline=epoch_cfg.baseline,
            #     preload=True
            # )

            self.logger.info(f"Created {len(self.epochs)} epochs")
            self.stats['steps_completed'].append('create_epochs')

        except Exception as e:
            self.logger.error(f"Failed to create epochs: {e}")
            self.stats['errors'].append(('create_epochs', str(e)))
            raise

        return self

    def extract_features(self) -> np.ndarray:
        """提取特征

        Returns:
            特征矩阵 (n_epochs, n_features)
        """
        if self.epochs is None:
            raise RuntimeError("No epochs. Call create_epochs() first.")

        self.logger.info("Extracting features")

        # TODO: 实现特征提取
        # - 频带功率 (delta, theta, alpha, beta, gamma)
        # - ERP 特征
        # - 时间/频率特征

        features = np.array([])
        self.stats['steps_completed'].append('extract_features')

        return features

    def decode(self, labels: np.ndarray) -> Dict[str, Any]:
        """解码

        Args:
            labels: 标签数组

        Returns:
            解码结果字典
        """
        self.logger.info("Decoding")

        try:
            # 提取特征
            features = self.extract_features()

            # TODO: 分类器训练与评估
            # from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
            # clf = LinearDiscriminantAnalysis()
            # scores = cross_val_score(clf, features, labels, cv=5)

            results = {
                'accuracy': 0.0,
                'std': 0.0,
                'features_shape': features.shape,
                'labels_shape': labels.shape
            }

            self.logger.info(f"Accuracy: {results['accuracy']:.3f}")
            self.stats['steps_completed'].append('decode')

            return results

        except Exception as e:
            self.logger.error(f"Decode failed: {e}")
            self.stats['errors'].append(('decode', str(e)))
            raise

    def run(self, filepath: Path, events: np.ndarray, event_id: Dict[str, int]) -> Dict[str, Any]:
        """运行完整 pipeline

        Args:
            filepath: 数据文件路径
            events: 事件数组
            event_id: 事件 ID

        Returns:
            完整结果
        """
        self.logger.info("=" * 50)
        self.logger.info("Starting BCI Pipeline")
        self.logger.info("=" * 50)

        try:
            results = self.load(filepath).preprocess().create_epochs(events, event_id).decode(np.array([]))

            self.logger.info("Pipeline completed successfully")
            self.logger.info(f"Steps: {self.stats['steps_completed']}")

            return {
                'success': True,
                'results': results,
                'stats': self.stats
            }

        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats
            }


def main():
    """演示用法"""
    # 配置
    config = PipelineConfig()

    # 创建 pipeline
    pipeline = BCIPipeline(config)

    # 运行
    # results = pipeline.run(Path("data.edf"), events, event_id)


if __name__ == '__main__':
    print("BCI Pipeline - Engineered BCI Processing")
    print("Usage: pipeline = BCIPipeline(config)")
    print("       pipeline.run(filepath, events, event_id)")