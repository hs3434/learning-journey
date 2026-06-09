"""
BERT v1: bidirectional Transformer + CLS readout
================================================
Single-variable ablation vs aug_v3:
  - causal mask     → bidirectional (no mask)
  - last-token head → learnable [CLS] token + classifier(CLS_output)

All other settings IDENTICAL to eval_aug_v3.py:
  - pyramid bucket aug {106:1, 100:2, 95:4, 90:8, 85:16, 80:27}
  - 5-fold StratifiedKFold (seed=42)
  - kernel=1, stride=1, n_layers=2, d_model=64, n_heads=4, dropout=0.4
  - lr=5e-4, weight_decay=1e-3, batch_size=23, epochs=5
  - per-channel mean/std normalization pooled across buckets

Usage:
  python eval_bert_v1.py --all --max-epochs 5     # run all 5 folds
  python eval_bert_v1.py --fold 0 --max-epochs 3  # one fold, 3 epochs
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
from bci.decoder.transformer_bert import _EEGTransformerBert

# ── Config — KEEP IDENTICAL TO eval_aug_v3.py ──────────────────
SEED = 42
N_TIMES = 106
BATCH_SIZE = 23
EPOCHS_TOTAL = 5

BUCKET_CONFIG = {
    106: 1, 100: 2, 95: 4, 90: 8, 85: 16, 80: 27,
}

OUT_DIR = Path(__file__).parent / "reports" / "bert_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_CFG = dict(
    d_model=64, n_heads=4, n_layers=2,
    kernel=1, stride=1, dropout=0.4,
    max_seq_len=128,
)
TRAIN_CFG = dict(lr=5e-4, weight_decay=1e-3)


def augment_pyramid(X: np.ndarray, y: np.ndarray, rng: np.random.Generator
                    ) -> dict[int, tuple[np.ndarray, np.ndarray]]:
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
    fold_dir = OUT_DIR / f"fold_{fold_idx}"
    fold_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = fold_dir / "ckpt.pt"
    progress_path = fold_dir / "progress.json"
    result_path = fold_dir / "result.json"

    if result_path.exists():
        result = json.loads(result_path.read_text())
        print(f"  [Fold {fold_idx + 1}] 已完成: acc={result['acc']:.3f}")
        return result

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

    # ── ONLY DIFFERENCE: use _EEGTransformerBert instead of _EEGTransformer ──
    model = _EEGTransformerBert(
        n_channels=n_channels, n_classes=len(classes), **MODEL_CFG,
    ).to(device)
    opt = optim.AdamW(model.parameters(), lr=TRAIN_CFG["lr"],
                      weight_decay=TRAIN_CFG["weight_decay"])
    criterion = nn.CrossEntropyLoss()

    start_epoch = 0
    losses = []
    if ckpt_path.exists():
        ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
        model.load_state_dict(ckpt["model"])
        opt.load_state_dict(ckpt["opt"])
        start_epoch = ckpt["epoch"] + 1
        losses = ckpt.get("losses", [])
        print(f"  [Fold {fold_idx + 1}] 从 epoch {start_epoch} 恢复")
    else:
        print(f"  [Fold {fold_idx + 1}] 从头开始训练")

    if start_epoch >= EPOCHS_TOTAL:
        print(f"  [Fold {fold_idx + 1}] 已训满 {EPOCHS_TOTAL} epoch，直接评估")
    else:
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

    final_epoch = json.loads(progress_path.read_text()).get("current_epoch", 0) \
        if progress_path.exists() else 0
    if final_epoch < EPOCHS_TOTAL:
        print(f"  [Fold {fold_idx + 1}] 部分完成 {final_epoch}/{EPOCHS_TOTAL}")
        return None

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
    if not results:
        return
    accs = [r["acc"] for r in results]
    print(f"\n{'='*60}\n汇总（{len(results)}/5 完成）\n{'='*60}")
    for r in results:
        print(f"  Fold {r['fold']+1}: acc={r['acc']:.4f}")
    print(f"  mean={np.mean(accs):.4f} ± {np.std(accs):.4f}")
    if len(results) == 5:
        summary = {
            "method": "bert_v1_bidirectional_cls",
            "mean_acc": float(np.mean(accs)),
            "std_acc": float(np.std(accs)),
            "folds": results,
            "bucket_config": BUCKET_CONFIG,
            "ablation_vs_aug_v3": {
                "attention": "bidirectional (was causal)",
                "readout": "CLS token (was last token)",
                "everything_else": "identical",
            },
        }
        (OUT_DIR / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False))
        print(f"  → summary.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fold", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--max-epochs", type=int, default=10)
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
