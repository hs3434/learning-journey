"""
数据增强 + 分桶训练：对比 A (自由裁剪) vs B (保留 ERP)
=========================================================
- 20 档长度 ∈ [40, 106]
- 同 batch 同长度（自由分桶，无 padding）
- 不同 batch 长度不同 → Transformer 学不定长输入
- A: 随机起点（可能切掉 t=0 刺激点）
- B: 起点保证包含 t=0（约第 30 个时间点）
- 5-fold CV，对比 Transformer 在 A/B/原始 三种数据上的表现
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
from sklearn.metrics import accuracy_score

import sys
sys.path.insert(0, str(Path(__file__).parent))
from data_audvis import load_audvis_epochs as load_audvis

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "package"))
from bci.decoder.transformer import TransformerDecoder

# ── 配置 ──────────────────────────────────────────
SEED = 42
N_BUCKETS = 20
MIN_LEN = 40       # 最小窗口 (40 / 150Hz ≈ 267ms)
MAX_LEN = 106      # 最大窗口 = 原始长度
ERP_ANCHOR = 30    # t=0 对应的时间点 (tmin=-0.2, sfreq=150 → 30)

OUT_DIR = Path(__file__).parent / "reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TRANSFORMER_CFG = dict(
    d_model=64, n_heads=4, n_layers=2,
    kernel=1, stride=1, dropout=0.2,
    epochs=100, lr=5e-4,
    batch_size=32, normalize=True,
    device="cpu",
)


def _bucket_lengths() -> list[int]:
    """生成 20 档长度，从 MIN 到 MAX 等距取样"""
    return list(np.linspace(MIN_LEN, MAX_LEN, N_BUCKETS).astype(int))


def augment_free(X: np.ndarray, y: np.ndarray, rng: np.random.Generator,
                 lengths: list[int]) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """A: 自由裁剪 — 每档长度随机起点（可能切掉 t=0）"""
    buckets = {}
    for L in lengths:
        max_start = X.shape[2] - L
        # 每个 trial 在这一档下选 1 个随机窗口
        starts = rng.integers(0, max_start + 1, size=X.shape[0])
        X_aug = np.stack([
            X[i, :, starts[i]:starts[i] + L]
            for i in range(X.shape[0])
        ]).astype(np.float32)
        buckets[L] = (X_aug, y.copy())
    return buckets


def augment_erp_anchored(X: np.ndarray, y: np.ndarray,
                         rng: np.random.Generator,
                         lengths: list[int]) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """B: 保留 ERP — 起点 ∈ [0, ERP_ANCHOR]，保证 t=0 在窗口内"""
    buckets = {}
    for L in lengths:
        # 起点必须 ≤ ERP_ANCHOR (保证 t=0 在窗口内)
        # 起点 + L 必须 ≤ X.shape[2]
        max_start = min(ERP_ANCHOR, X.shape[2] - L)
        if max_start < 0:
            # 窗口太大，起点只能为 0
            starts = np.zeros(X.shape[0], dtype=int)
        else:
            starts = rng.integers(0, max_start + 1, size=X.shape[0])
        X_aug = np.stack([
            X[i, :, starts[i]:starts[i] + L]
            for i in range(X.shape[0])
        ]).astype(np.float32)
        buckets[L] = (X_aug, y.copy())
    return buckets


def fit_transformer_multilength(
    buckets_train: dict[int, tuple[np.ndarray, np.ndarray]],
    cfg: dict,
) -> TransformerDecoder:
    """跨多个长度训练 Transformer。

    策略：把所有桶的数据拼起来训练，但 fit() 内部按桶 mini-batch（同 batch 同长度）。
    简化做法：合并所有桶为一个长样本列表，自定义训练循环。
    """
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from bci.decoder.transformer import _EEGTransformer

    # 用最大长度桶初始化模型 + 计算 norm stats
    max_len = max(buckets_train.keys())
    X_max, y_max = buckets_train[max_len]
    n_channels = X_max.shape[1]
    classes = np.unique(np.concatenate([y for _, y in buckets_train.values()]))
    n_classes = len(classes)

    # 用全部数据的统计量（pooled across all lengths and samples）
    # 按通道算 mean/std（因为各桶时间长度不同，无法直接 stack）
    means, stds = [], []
    for ch in range(n_channels):
        ch_values = np.concatenate([bX[:, ch, :].reshape(-1)
                                     for bX, _ in buckets_train.values()])
        means.append(ch_values.mean())
        stds.append(ch_values.std() + 1e-8)
    mean = np.array(means, dtype=np.float32).reshape(1, n_channels, 1)
    std = np.array(stds, dtype=np.float32).reshape(1, n_channels, 1)

    # 初始化模型
    model = _EEGTransformer(
        n_channels=n_channels, n_classes=n_classes,
        d_model=cfg["d_model"], n_heads=cfg["n_heads"],
        n_layers=cfg["n_layers"],
        kernel=cfg["kernel"], stride=cfg["stride"],
        dropout=cfg["dropout"],
        max_seq_len=max_len + 16,  # 留点余量
    ).to(cfg["device"])

    opt = optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()
    bs = cfg["batch_size"]

    # 预处理：每个桶归一化 + 转 tensor
    bucket_tensors = {}
    for L, (bX, by) in buckets_train.items():
        bX_norm = (bX - mean) / std
        y_idx = np.searchsorted(classes, by)
        bucket_tensors[L] = (
            torch.tensor(bX_norm, dtype=torch.float32, device=cfg["device"]),
            torch.tensor(y_idx, dtype=torch.long, device=cfg["device"]),
        )

    # 训练循环：每个 epoch 打乱所有 (bucket_L, sample_idx) 组合
    # 然后按 bucket 分组成 mini-batch（保证同 batch 同长度）
    all_keys = []  # list of (L, sample_idx)
    for L, (bX, _) in buckets_train.items():
        for i in range(bX.shape[0]):
            all_keys.append((L, i))
    all_keys = np.array(all_keys, dtype=object)

    rng = np.random.default_rng(SEED)
    model.train()
    for epoch in range(cfg["epochs"]):
        # 打乱
        perm = rng.permutation(len(all_keys))
        shuffled = all_keys[perm]
        # 按长度分组成 mini-batch
        by_len: dict[int, list[int]] = {}
        for L, i in shuffled:
            by_len.setdefault(L, []).append(i)
        # 每个长度切 mini-batch
        all_batches = []
        for L, idxs in by_len.items():
            for s in range(0, len(idxs), bs):
                all_batches.append((L, idxs[s:s + bs]))
        # 打乱 batch 顺序（让不同长度交替）
        rng.shuffle(all_batches)
        for L, idxs in all_batches:
            Xt, yt = bucket_tensors[L]
            idx_t = torch.tensor(idxs, dtype=torch.long, device=cfg["device"])
            opt.zero_grad()
            loss = criterion(model(Xt[idx_t]), yt[idx_t])
            loss.backward()
            opt.step()
    model.eval()

    # 包装成 TransformerDecoder 对象方便复用 predict
    dec = TransformerDecoder(**cfg)
    dec.n_channels = n_channels
    dec.classes_ = classes
    dec._n_classes = n_classes
    dec._train_n_tokens = max_len  # 训练见过的最大长度
    dec._mean = mean
    dec._std = std
    dec.model = model
    return dec


def predict_on_original(dec: TransformerDecoder, X_test: np.ndarray) -> np.ndarray:
    """在原始长度（106）上预测"""
    return dec.predict(X_test)


def run_experiment(method_name: str, X: np.ndarray, y: np.ndarray,
                    augment_fn) -> dict:
    """5-fold CV，每 fold 用 augment_fn 增强训练集，在原始测试集上评估"""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    lengths = _bucket_lengths()
    scores = []
    rng = np.random.default_rng(SEED)

    for fold, (train_idx, test_idx) in enumerate(cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # 增强训练集 → 20 个桶
        buckets = augment_fn(X_train, y_train, rng, lengths)
        total_aug = sum(bX.shape[0] for bX, _ in buckets.values())

        # 训练
        dec = fit_transformer_multilength(buckets, TRANSFORMER_CFG)
        # 在原始 106 长度的测试集上评估
        y_pred = predict_on_original(dec, X_test)
        acc = accuracy_score(y_test, y_pred)
        scores.append(acc)
        print(f"  [Fold {fold + 1}] {method_name}: acc = {acc:.3f} "
              f"(train aug: {X_train.shape[0]}→{total_aug})")

    scores = np.array(scores)
    print(f"  ➡  {method_name}: {scores.mean():.3f} ± {scores.std():.3f}")
    return {
        "method": method_name,
        "scores": scores.tolist(),
        "mean": float(scores.mean()),
        "std": float(scores.std()),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["free", "erp", "both"], default="both")
    args = parser.parse_args()

    print(f"📦 加载 MNE Sample 数据...")
    X, y, _ = load_audvis()
    print(f"   X: {X.shape}, classes: {np.bincount(y)}")
    print(f"   桶长度: {_bucket_lengths()}")
    print()

    results = []
    if args.only in ("free", "both"):
        print("🚀 实验 A: 自由裁剪（可能切掉 t=0）")
        results.append(run_experiment("aug_free", X, y, augment_free))
        print()
    if args.only in ("erp", "both"):
        print("🚀 实验 B: 保留 ERP 锚点")
        results.append(run_experiment("aug_erp", X, y, augment_erp_anchored))
        print()

    print("=" * 60)
    print("   结果汇总")
    print("=" * 60)
    print(f"{'Method':<20}{'Accuracy':<15}{'Std':<10}")
    print("-" * 45)
    for r in results:
        print(f"{r['method']:<20}{r['mean']:.4f}         {r['std']:.4f}")

    # 增量保存：合并已有结果
    out_path = OUT_DIR / "results_aug.json"
    existing = []
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text())
        except Exception:
            existing = []
    # 按 method 去重，新结果覆盖旧
    by_method = {r["method"]: r for r in existing}
    for r in results:
        by_method[r["method"]] = r
    out_path.write_text(json.dumps(list(by_method.values()), indent=2, ensure_ascii=False))
    print(f"\n  报告 → {out_path}")
    print("\n✅ 完成!")


if __name__ == "__main__":
    main()
