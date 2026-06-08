"""
数据增强 v2：金字塔分桶 + epoch-level 断点续跑
==========================================
桶配置：{106: 1, 100: 2, 95: 4, 90: 8, 85: 16, 80: 27} → 58 切片/trial
训练：每桶独立 bs=23 mini-batch，跨桶随机交替
断点续跑：每个 epoch 保存 checkpoint，可分多次跑完

用法：
  python eval_aug_v2.py --fold 0 --max-epochs 10  # 跑前 10 个 epoch
  python eval_aug_v2.py --fold 0 --max-epochs 10  # 继续跑 (11-20)
  python eval_aug_v2.py --fold 0                   # 跑到 EPOCHS_TOTAL 结束
  python eval_aug_v2.py --all --max-epochs 5      # 5 个 fold 各跑 5 epoch
"""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="bci")

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score

import sys
sys.path.insert(0, str(Path(__file__).parent))
from data_audvis import load_audvis_epochs as load_audvis

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "package"))
from bci.decoder.transformer import TransformerDecoder, _EEGTransformer

# ── 配置 ──────────────────────────────────────────
SEED = 42
ERP_ANCHOR = 30
N_TIMES = 106
BATCH_SIZE = 23
EPOCHS_TOTAL = 5  # v3: 等效 epoch ≈ 5×58 = 290，足够；降低过拟合

BUCKET_CONFIG = {
    106: 1, 100: 2, 95: 4, 90: 8, 85: 16, 80: 27,
}

OUT_DIR = Path(__file__).parent / "reports" / "aug_v3"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_CFG = dict(
    d_model=64, n_heads=4, n_layers=2,
    kernel=1, stride=1, dropout=0.4,  # v3: 0.2 → 0.4
    max_seq_len=128,
)
TRAIN_CFG = dict(lr=5e-4, weight_decay=1e-3)  # v3: 1e-4 → 1e-3


def augment_pyramid(X: np.ndarray, y: np.ndarray, rng: np.random.Generator
                    ) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """金字塔分桶（参考之前讨论）"""
    n_samples = X.shape[0]
    buckets = {}
    for L, n_slices in BUCKET_CONFIG.items():
        if L == N_TIMES:
            buckets[L] = (X.astype(np.float32), y.copy())
            continue
        max_start = N_TIMES - L
        n_unique = max_start + 1
        actual = min(n_slices, n_unique)
        bucket_X = np.empty((n_samples * actual, X.shape[1], L), dtype=np.float32)
        bucket_y = np.empty(n_samples * actual, dtype=y.dtype)
        for i in range(n_samples):
            starts = rng.choice(n_unique, size=actual, replace=False)
            for j, s in enumerate(starts):
                bucket_X[i * actual + j] = X[i, :, s:s + L]
                bucket_y[i * actual + j] = y[i]
        buckets[L] = (bucket_X, bucket_y)
    return buckets


def compute_norm_stats(buckets: dict) -> tuple[np.ndarray, np.ndarray]:
    """按通道算 mean/std（pool 所有桶所有时间点）"""
    n_channels = next(iter(buckets.values()))[0].shape[1]
    means, stds = [], []
    for ch in range(n_channels):
        vals = np.concatenate([bX[:, ch, :].reshape(-1) for bX, _ in buckets.values()])
        means.append(vals.mean())
        stds.append(vals.std() + 1e-8)
    return (np.array(means, dtype=np.float32).reshape(1, n_channels, 1),
            np.array(stds, dtype=np.float32).reshape(1, n_channels, 1))


def prepare_bucket_tensors(buckets, mean, std, classes, device):
    out = {}
    for L, (bX, by) in buckets.items():
        bX_norm = (bX - mean) / std
        y_idx = np.searchsorted(classes, by)
        out[L] = (
            torch.tensor(bX_norm, dtype=torch.float32, device=device),
            torch.tensor(y_idx, dtype=torch.long, device=device),
        )
    return out


def train_one_epoch(model, opt, criterion, bucket_tensors, rng, bs):
    """跨桶随机交替 mini-batch 训练一个 epoch，返回平均 loss"""
    all_batches = []
    for L, (Xt, _) in bucket_tensors.items():
        n = Xt.shape[0]
        perm = rng.permutation(n)
        for s in range(0, n, bs):
            batch_idx = perm[s:s + bs]
            all_batches.append((L, torch.tensor(batch_idx, dtype=torch.long,
                                                 device=Xt.device)))
    rng.shuffle(all_batches)
    model.train()
    total_loss = 0.0
    for L, idx_t in all_batches:
        Xt, yt = bucket_tensors[L]
        opt.zero_grad()
        loss = criterion(model(Xt[idx_t]), yt[idx_t])
        loss.backward()
        opt.step()
        total_loss += loss.item()
    return total_loss / len(all_batches), len(all_batches)


def evaluate(model, X_test, mean, std, classes, device):
    model.eval()
    X_norm = (X_test.astype(np.float32) - mean) / std
    Xt = torch.tensor(X_norm, dtype=torch.float32, device=device)
    with torch.no_grad():
        logits = model(Xt)
    pred_idx = logits.argmax(dim=-1).cpu().numpy()
    return classes[pred_idx]


def run_fold(fold_idx: int, X: np.ndarray, y: np.ndarray, max_epochs: int):
    """跑一个 fold，最多 max_epochs 个 epoch，支持断点续跑"""
    fold_dir = OUT_DIR / f"fold_{fold_idx}"
    fold_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = fold_dir / "ckpt.pt"
    progress_path = fold_dir / "progress.json"
    result_path = fold_dir / "result.json"

    if result_path.exists():
        result = json.loads(result_path.read_text())
        print(f"  [Fold {fold_idx + 1}] 已完成: acc={result['acc']:.3f}")
        return result

    # 数据准备（固定 random seed，每次都生成一样的增强数据）
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    train_idx, test_idx = list(cv.split(X, y))[fold_idx]
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    classes = np.unique(y_train)

    aug_rng = np.random.default_rng(SEED + fold_idx)
    buckets = augment_pyramid(X_train, y_train, aug_rng)
    mean, std = compute_norm_stats(buckets)
    device = "cpu"
    bucket_tensors = prepare_bucket_tensors(buckets, mean, std, classes, device)
    n_channels = X_train.shape[1]

    # 模型 + optimizer
    model = _EEGTransformer(
        n_channels=n_channels, n_classes=len(classes), **MODEL_CFG,
    ).to(device)
    opt = optim.AdamW(model.parameters(), lr=TRAIN_CFG["lr"],
                      weight_decay=TRAIN_CFG["weight_decay"])
    criterion = nn.CrossEntropyLoss()

    # 加载 checkpoint（如果存在）
    start_epoch = 0
    losses = []
    if ckpt_path.exists():
        ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
        model.load_state_dict(ckpt["model"])
        opt.load_state_dict(ckpt["opt"])
        start_epoch = ckpt["epoch"] + 1
        losses = ckpt.get("losses", [])
        print(f"  [Fold {fold_idx + 1}] 从 epoch {start_epoch} 恢复（已训 {start_epoch}/{EPOCHS_TOTAL}）")
    else:
        print(f"  [Fold {fold_idx + 1}] 从头开始训练")

    if start_epoch >= EPOCHS_TOTAL:
        print(f"  [Fold {fold_idx + 1}] 已训满 {EPOCHS_TOTAL} epoch，直接评估")
    else:
        # 训练循环：每 epoch 保存 checkpoint
        train_rng = np.random.default_rng(SEED + fold_idx * 100 + start_epoch)
        end_epoch = min(start_epoch + max_epochs, EPOCHS_TOTAL)
        print(f"  [Fold {fold_idx + 1}] 训练 epoch {start_epoch+1}..{end_epoch}")
        for epoch in range(start_epoch, end_epoch):
            t0 = time.time()
            avg_loss, n_batches = train_one_epoch(
                model, opt, criterion, bucket_tensors, train_rng, BATCH_SIZE)
            dt = time.time() - t0
            losses.append(avg_loss)
            print(f"    epoch {epoch+1}/{EPOCHS_TOTAL} | loss={avg_loss:.4f} | {n_batches}b/{dt:.1f}s")
            # 保存 checkpoint
            torch.save({
                "model": model.state_dict(),
                "opt": opt.state_dict(),
                "epoch": epoch,
                "losses": losses,
            }, ckpt_path)
            progress_path.write_text(json.dumps({
                "current_epoch": epoch + 1,
                "total_epochs": EPOCHS_TOTAL,
                "losses": losses,
            }, indent=2))

    # 训练完成检查
    final_epoch = json.loads(progress_path.read_text()).get("current_epoch", 0) \
        if progress_path.exists() else 0
    if final_epoch < EPOCHS_TOTAL:
        print(f"  [Fold {fold_idx + 1}] 部分完成 {final_epoch}/{EPOCHS_TOTAL}，请重跑继续")
        return None

    # 评估
    y_pred = evaluate(model, X_test, mean, std, classes, device)
    acc = float(accuracy_score(y_test, y_pred))
    print(f"  [Fold {fold_idx + 1}] ✓ 完成 acc={acc:.4f}")
    result = {
        "fold": fold_idx,
        "acc": acc,
        "n_train_orig": int(X_train.shape[0]),
        "n_train_aug": sum(bX.shape[0] for bX, _ in buckets.values()),
        "n_test": int(X_test.shape[0]),
        "final_losses": losses[-5:],
    }
    result_path.write_text(json.dumps(result, indent=2))
    return result


def summarize():
    fold_dirs = sorted(OUT_DIR.glob("fold_*"))
    results = []
    for fd in fold_dirs:
        rp = fd / "result.json"
        if rp.exists():
            results.append(json.loads(rp.read_text()))
        else:
            pp = fd / "progress.json"
            if pp.exists():
                p = json.loads(pp.read_text())
                print(f"  [{fd.name}] 进行中 {p['current_epoch']}/{p['total_epochs']}")
    if not results:
        return
    accs = [r["acc"] for r in results]
    print(f"\n{'='*60}\n汇总（{len(results)}/5 完成）\n{'='*60}")
    for r in results:
        print(f"  Fold {r['fold']+1}: acc={r['acc']:.4f}")
    print(f"  mean={np.mean(accs):.4f} ± {np.std(accs):.4f}")
    if len(results) == 5:
        summary = {
            "method": "aug_pyramid_free",
            "mean_acc": float(np.mean(accs)),
            "std_acc": float(np.std(accs)),
            "folds": results,
            "bucket_config": BUCKET_CONFIG,
        }
        (OUT_DIR / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False))
        print(f"  → summary.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fold", type=int, default=None,
                        help="fold index 0-4，不指定则跑所有未完成的 fold")
    parser.add_argument("--all", action="store_true",
                        help="跑所有 fold（每个最多 max-epochs 个 epoch）")
    parser.add_argument("--max-epochs", type=int, default=10,
                        help="本次最多跑几个 epoch（防超时）")
    args = parser.parse_args()

    print(f"📦 加载 MNE Sample 数据...")
    X, y, _ = load_audvis()
    print(f"   X: {X.shape}, 桶: {BUCKET_CONFIG}")
    print()

    if args.fold is not None:
        run_fold(args.fold, X, y, args.max_epochs)
    elif args.all:
        for fi in range(5):
            run_fold(fi, X, y, args.max_epochs)
    else:
        # 自动找第一个未完成 fold
        for fi in range(5):
            result_path = OUT_DIR / f"fold_{fi}" / "result.json"
            if not result_path.exists():
                run_fold(fi, X, y, args.max_epochs)
                break
        else:
            print("✅ 所有 5 个 fold 已完成")

    summarize()


if __name__ == "__main__":
    main()
