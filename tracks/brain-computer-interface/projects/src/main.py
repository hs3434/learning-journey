"""
BCI Pipeline Main Entry
========================
BCI Signal Processing Pipeline - Engineering and Integration

Usage:
    python -m src.main --help
    python -m src.main data.edf --config config.yaml
"""

from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='BCI Signal Processing Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main data.edf
  python -m src.main data.edf --config config.yaml --output ./results
  python -m src.main data.edf --l_freq 1 --h_freq 40 --method lda
        """
    )

    parser.add_argument('filepath', type=str, help='Path to EEG file')
    parser.add_argument('--config', '-c', type=str, help='YAML config file')
    parser.add_argument('--output', '-o', type=str, default='./output',
                       help='Output directory')
    parser.add_argument('--l_freq', type=float, default=0.5,
                       help='Low frequency cutoff (Hz)')
    parser.add_argument('--h_freq', type=float, default=40.0,
                       help='High frequency cutoff (Hz)')
    parser.add_argument('--method', type=str, default='lda',
                       choices=['lda', 'svm', 'csp'],
                       help='Decoding method')
    parser.add_argument('--gui', action='store_true',
                       help='Launch GUI mode')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')

    return parser.parse_args()


def run_cli(args):
    """Run pipeline in CLI mode"""
    from config import PipelineConfig
    from pipeline import BCIPipeline

    logger = logging.getLogger(__name__)

    config = PipelineConfig()
    config.filter.l_freq = args.l_freq
    config.filter.h_freq = args.h_freq
    config.decode.method = args.method
    config.output_dir = args.output

    if args.config:
        config = PipelineConfig.from_yaml(Path(args.config))

    logger.info(f"Processing: {args.filepath}")

    pipeline = BCIPipeline(config)
    result = pipeline.run(args.filepath)

    if result.success:
        logger.info("=" * 50)
        logger.info("Pipeline completed successfully!")
        if result.accuracy is not None:
            logger.info(f"Accuracy: {result.accuracy:.3f} ± {result.std:.3f}")
        logger.info(f"Steps: {result.steps_completed}")
        logger.info("=" * 50)

        saved = pipeline.save_results()
        logger.info(f"Results saved to: {saved}")

        return 0
    else:
        logger.error(f"Pipeline failed: {result.errors}")
        return 1


def run_gui(args):
    """Run pipeline in GUI mode"""
    from gui import main as gui_main
    gui_main()


def main():
    """Main entry point"""
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.gui:
        run_gui(args)
    else:
        sys.exit(run_cli(args))


if __name__ == '__main__':
    main()