"""
Transformer vs LDA vs CNN — MNE Sample 数据集对比评估
==============================================
- 5-fold CV, 记录每个 fold 的准确率 + 混淆矩阵
- Transformer 额外记录训练 loss 曲线
- 生成对比图
"""
from __future__ import annotations
import json
from pathlib import Path
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="bci")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, accuracy_score

import torch

from bci.decoder.transformer import TransformerDecoder
from bci.decoder.lda import LDADecoder
from bci.decoder.deep import CNNDecoder

from data_audvis import load_audvis_epochs

OUT_DIR = Path(__file__).parent / "reports"
CP_DIR = Path(__file__).parent / "checkpoints"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CP_DIR.mkdir(parents=True, exist_ok=True)
DEVICE = "cpu"

# ── 模型配置（各自最优配方，不强求统一） ──────────
# 设计原则：每个模型按它最适合的训练方式调，对比的是「架构能力」而非「统一配方」
CFG = {
    # Transformer：需要 mini-batch + 输入归一化（参数多 + 无 BN）
    "transformer": dict(d_model=64, n_heads=4, n_layers=2,
                        kernel=1, stride=1, dropout=0.2,
                        epochs=100, lr=5e-4,
                        batch_size=32, normalize=True,
                        device=DEVICE),
    # CNN：用 EEGNet 默认配方（内部带 BN，全量 batch 够用）
    "cnn": dict(epochs=30, lr=1e-3, device=DEVICE),
    # LDA：线性模型，PCA 白化即可
    "lda": dict(n_components=0.95),
}


def _plot_loss_curve(losses: list[float], fold: int, save_path: Path):
    """训练 loss 曲线"""
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(losses, color="#2b6cb0", linewidth=1.5)
    ax.set_xlabel("Epoch"); ax.set_ylabel("Loss")
    ax.set_title(f"Transformer Training Loss — Fold {fold + 1}")
    ax.grid(ls=":", alpha=0.4)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def evaluate_one_method(
    method: str,
    X: np.ndarray,
    y: np.ndarray,
    cv: StratifiedKFold,
) -> dict:
    """运行一个方法的 5-fold CV 评估"""
    scores = []
    all_y_true, all_y_pred = [], []
    fold_losses = []

    for fold, (train_idx, test_idx) in enumerate(cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        if method == "lda":
            dec = LDADecoder(**CFG["lda"])
            dec.fit(X_train, y_train)
            y_pred = dec.predict(X_test)
            losses = None

        elif method == "cnn":
            dec = CNNDecoder(**CFG["cnn"])
            dec.fit(X_train, y_train)
            y_pred = dec.predict(X_test)
            losses = None

        elif method == "transformer":
            dec = TransformerDecoder(**CFG["transformer"])
            dec.fit(X_train, y_train)
            y_pred = dec.predict(X_test)
            losses = None

        acc = accuracy_score(y_test, y_pred)
        scores.append(acc)
        all_y_true.extend(y_test.tolist())
        all_y_pred.extend(y_pred.tolist())

        print(f"  [Fold {fold + 1}] {method}: acc = {acc:.3f}")

    scores = np.array(scores)
    cm = confusion_matrix(all_y_true, all_y_pred)

    return {
        "method": method,
        "mean_acc": float(scores.mean()),
        "std_acc": float(scores.std()),
        "cv_scores": scores.tolist(),
        "confusion_matrix": cm.tolist(),
    }


def plot_comparison(results: list[dict], save_path: Path):
    """三模型准确率对比柱状图"""
    names = [r["method"].capitalize() for r in results]
    means = [r["mean_acc"] for r in results]
    stds = [r["std_acc"] for r in results]

    colors = ["#38a169", "#3182ce", "#d69e2e"]
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(names, means, yerr=stds, capsize=6, color=colors,
                  edgecolor="white", linewidth=1.2)
    for bar, m, s in zip(bars, means, stds):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{m:.3f}±{s:.3f}", ha="center", va="bottom", fontsize=10)
    ax.set_ylabel("Accuracy"); ax.set_ylim(0, 1.1)
    ax.set_title("MNE Sample — 听觉 vs 视觉 Decoding")
    ax.axhline(0.5, ls="--", color="grey", alpha=0.5, label="Chance")
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"  对比图 → {save_path}")


def plot_cm(results: list[dict], save_dir: Path):
    """逐模型混淆矩阵"""
    for r in results:
        cm = np.array(r["confusion_matrix"])
        fig, ax = plt.subplots(figsize=(4, 4))
        disp = ConfusionMatrixDisplay(cm, display_labels=["Audio", "Visual"])
        disp.plot(ax=ax, values_format="d", cmap="Blues", colorbar=False)
        ax.set_title(f"{r['method'].capitalize()} — Confusion Matrix")
        path = save_dir / f"cm_{r['method']}.png"
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print(f"  混淆矩阵 → {path}")


def main():
    print("=" * 60)
    print("  MNE Sample 数据加载...")
    X, y, ch_names = load_audvis_epochs()
    print(f"  Shape: {X.shape} ({len(ch_names)} ch)")
    print(f"  Classes: {np.unique(y, return_counts=True)}")
    print("=" * 60)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    methods = ["lda", "cnn", "transformer"]

    results = []
    for method in methods:
        print(f"\n─── {method.upper()} ───")
        result = evaluate_one_method(method, X, y, cv)
        print(f"  ➡  {method}: {result['mean_acc']:.3f} ± {result['std_acc']:.3f}")
        results.append(result)

    # ── 输出汇总 ──────────────────────────
    print("\n" + "=" * 60)
    print("   结果汇总")
    print("=" * 60)
    print(f"{'Method':<15} {'Accuracy':<15} {'Std':<10}")
    print("-" * 40)
    for r in sorted(results, key=lambda x: -x["mean_acc"]):
        print(f"{r['method']:<15} {r['mean_acc']:.4f}          {r['std_acc']:.4f}")

    # 绘图
    plot_comparison(results, OUT_DIR / "comparison_bar.png")
    plot_cm(results, OUT_DIR)

    # 保存 JSON
    report = {
        "dataset": "MNE Sample (auditory vs visual)",
        "n_trials": int(X.shape[0]),
        "n_channels": int(X.shape[1]),
        "n_times": int(X.shape[2]),
        "cv_folds": 5,
        "results": results,
    }
    json_path = OUT_DIR / "results.json"
    json_path.write_text(json.dumps(report, indent=2))
    print(f"\n  报告 → {json_path}")
    print(f"\n✅ 完成!")


if __name__ == "__main__":
    main()