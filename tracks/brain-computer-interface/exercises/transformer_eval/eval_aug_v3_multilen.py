"""
v3 多长度测试集评估
=========================
复用 v3 已训好的 5 个 fold checkpoint，测试集分别裁成 {106, 100, 95, 90, 85, 80}：

- 方案 A (mean_logits)：每 trial 全部切片 softmax 平均 → argmax （ensemble 能力上限）
- 方案 B (single_slice)：每 trial 随机 1 个切片 → 预测（实时推理实际表现）

不重训练，只 load ckpt + 评估。
"""
from __future__ import annotations
import json
from pathlib import Path
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="bci")

import numpy as np
import torch
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score

import sys
sys.path.insert(0, str(Path(__file__).parent))
from data_audvis import load_audvis_epochs as load_audvis

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "package"))
from bci.decoder.transformer import _EEGTransformer

# v3 配置（与 eval_aug_v3.py 一致）
SEED = 42
N_TIMES = 106
TEST_LENGTHS = [106, 100, 95, 90, 85, 80]
V3_DIR = Path(__file__).parent / "reports" / "aug_v3"
OUT_DIR = Path(__file__).parent / "reports" / "aug_v3_multilen"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_CFG = dict(
    d_model=64, n_heads=4, n_layers=2,
    kernel=1, stride=1, dropout=0.4,
    max_seq_len=128,
)


def slice_test_set(X_test, L):
    """裁出长度 L 的所有非重叠+重叠切片。返回 (n_trial, n_slice, ch, L) 和 n_slice。

    用「所有可能的起点」一次性切，保证 mean_logits 用最多信息。
    起点：0, 1, ..., N_TIMES-L
    """
    if L == N_TIMES:
        return X_test[:, None, :, :], 1  # (N,1,C,L)
    n_starts = N_TIMES - L + 1
    n_trial, n_ch = X_test.shape[0], X_test.shape[1]
    out = np.empty((n_trial, n_starts, n_ch, L), dtype=np.float32)
    for s in range(n_starts):
        out[:, s, :, :] = X_test[:, :, s:s + L]
    return out, n_starts


def eval_one_length(model, X_test, y_test, mean, std, classes, L, device, rng):
    """返回 (acc_mean_logits, acc_single_slice)"""
    sliced, n_slices = slice_test_set(X_test, L)
    # shape: (N, S, C, L)
    N = sliced.shape[0]

    # 归一化（按通道）
    sliced = (sliced - mean[None, :, :, :]) / std[None, :, :, :]
    # 注意：mean/std shape (1, C, 1) → broadcast 到 (N, S, C, L) ok

    # 方案 A: mean logits over all slices
    model.eval()
    flat = sliced.reshape(N * n_slices, sliced.shape[2], L)
    with torch.no_grad():
        Xt = torch.tensor(flat, dtype=torch.float32, device=device)
        logits = model(Xt).cpu().numpy()  # (N*S, n_classes)
    logits = logits.reshape(N, n_slices, -1)
    # mean over slices
    mean_probs = torch.softmax(torch.tensor(logits), dim=-1).mean(dim=1).numpy()
    pred_idx_A = mean_probs.argmax(axis=-1)
    acc_A = float(accuracy_score(y_test, classes[pred_idx_A]))

    # 方案 B: single random slice per trial
    picks = rng.integers(0, n_slices, size=N)
    pred_idx_B = logits[np.arange(N), picks].argmax(axis=-1)
    acc_B = float(accuracy_score(y_test, classes[pred_idx_B]))

    # 额外：所有切片平均的「单切片 acc」（不靠 ensemble）
    all_slice_pred = logits.argmax(axis=-1)  # (N, S)
    all_slice_correct = (classes[all_slice_pred] == y_test[:, None]).mean()

    return {
        "L": L,
        "n_slices_per_trial": n_slices,
        "acc_mean_logits": acc_A,
        "acc_single_random": acc_B,
        "acc_per_slice_avg": float(all_slice_correct),
    }


def run_fold(fold_idx, X, y):
    fold_dir = V3_DIR / f"fold_{fold_idx}"
    ckpt_path = fold_dir / "ckpt.pt"
    if not ckpt_path.exists():
        print(f"  [Fold {fold_idx+1}] ❌ 无 ckpt，跳过")
        return None

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    train_idx, test_idx = list(cv.split(X, y))[fold_idx]
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    classes = np.unique(y_train)
    n_channels = X_train.shape[1]

    # 重算 mean/std（与训练时一致：用训练桶 pool）
    # 简化：直接用训练原始 X_train 的 (channel, time) 统计
    # 注意：v3 训练时是 pool 所有桶所有时间点，这里用 X_train pool 全时间点近似
    mean = X_train.mean(axis=(0, 2), keepdims=False).reshape(1, n_channels, 1).astype(np.float32)
    std = (X_train.std(axis=(0, 2), keepdims=False).reshape(1, n_channels, 1) + 1e-8).astype(np.float32)

    device = "cpu"
    model = _EEGTransformer(
        n_channels=n_channels, n_classes=len(classes), **MODEL_CFG,
    ).to(device)
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model"])

    eval_rng = np.random.default_rng(SEED + fold_idx * 7)
    fold_results = []
    print(f"  [Fold {fold_idx+1}] eval over lengths {TEST_LENGTHS}")
    for L in TEST_LENGTHS:
        r = eval_one_length(model, X_test, y_test, mean, std, classes, L, device, eval_rng)
        fold_results.append(r)
        print(f"    L={L:3d} | n_slices={r['n_slices_per_trial']:2d} | "
              f"mean_logits={r['acc_mean_logits']:.4f} | "
              f"single_random={r['acc_single_random']:.4f} | "
              f"per_slice_avg={r['acc_per_slice_avg']:.4f}")
    return {"fold": fold_idx, "results": fold_results}


def main():
    print("📦 加载 MNE Sample 数据...")
    X, y, _ = load_audvis()
    print(f"   X: {X.shape}")
    print()

    all_results = []
    for fi in range(5):
        r = run_fold(fi, X, y)
        if r is not None:
            all_results.append(r)
        print()

    # 汇总：每个 L 跨 fold 算 mean ± std
    print("=" * 70)
    print("跨 fold 汇总")
    print("=" * 70)
    summary = {"per_length": []}
    for li, L in enumerate(TEST_LENGTHS):
        accs_A = [fr["results"][li]["acc_mean_logits"] for fr in all_results]
        accs_B = [fr["results"][li]["acc_single_random"] for fr in all_results]
        accs_C = [fr["results"][li]["acc_per_slice_avg"] for fr in all_results]
        n_slices = all_results[0]["results"][li]["n_slices_per_trial"]
        entry = {
            "L": L,
            "n_slices": n_slices,
            "mean_logits": {"mean": float(np.mean(accs_A)), "std": float(np.std(accs_A))},
            "single_random": {"mean": float(np.mean(accs_B)), "std": float(np.std(accs_B))},
            "per_slice_avg": {"mean": float(np.mean(accs_C)), "std": float(np.std(accs_C))},
        }
        summary["per_length"].append(entry)
        print(f"  L={L:3d} ({n_slices:2d} slc/trial) | "
              f"mean_logits={entry['mean_logits']['mean']:.4f}±{entry['mean_logits']['std']:.4f} | "
              f"single={entry['single_random']['mean']:.4f}±{entry['single_random']['std']:.4f} | "
              f"per_slice={entry['per_slice_avg']['mean']:.4f}")

    summary["folds"] = all_results
    (OUT_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\n→ {OUT_DIR}/summary.json")


if __name__ == "__main__":
    main()
