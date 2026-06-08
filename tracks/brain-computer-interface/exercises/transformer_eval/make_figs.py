#!/usr/bin/env python3
"""Generate experiment summary plots."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPORTS = Path(__file__).parent / "reports"
OUT = Path(__file__).parent / "reports" / "figs"
OUT.mkdir(exist_ok=True)

# ---- Plot 1: 4-experiment progression ----
exps = [
    ("baseline\n(Transformer)", 0.806, 0.033, "#888"),
    ("aug_v2\n(pyramid)",       0.844, 0.047, "#4a90e2"),
    ("aug_v3\n(strong reg)",    0.844, 0.025, "#2c6eb6"),
    ("multilen L=85",           0.878, 0.031, "#1abc9c"),
]
cnn_acc, lda_acc = 0.944, 0.910

fig, ax = plt.subplots(figsize=(10, 5.5))
labels = [e[0] for e in exps]
means  = [e[1] for e in exps]
stds   = [e[2] for e in exps]
colors = [e[3] for e in exps]
x = np.arange(len(exps))
bars = ax.bar(x, means, yerr=stds, capsize=6, color=colors,
              edgecolor="#222", linewidth=1.2)

# Reference lines
ax.axhline(cnn_acc, color="#e74c3c", ls="--", lw=1.6, label=f"CNN baseline = {cnn_acc:.3f}")
ax.axhline(lda_acc, color="#f39c12", ls=":",  lw=1.6, label=f"LDA baseline = {lda_acc:.3f}")

# Bar labels
for bar, m, s in zip(bars, means, stds):
    ax.text(bar.get_x() + bar.get_width()/2, m + s + 0.005,
            f"{m:.3f}\n±{s:.3f}", ha="center", va="bottom", fontsize=9)

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=10)
ax.set_ylabel("5-fold CV accuracy")
ax.set_ylim(0.75, 1.0)
ax.set_title("Transformer Experiment Progression — MNE Sample ERP", fontsize=12, pad=12)
ax.legend(loc="lower right", fontsize=9)
ax.grid(True, axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(OUT / "progression.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"saved {OUT / 'progression.png'}")

# ---- Plot 2: Multi-length curve ----
multilen = json.loads((REPORTS / "aug_v3_multilen/summary.json").read_text())["per_length"]
Ls       = [e["L"] for e in multilen]
ml_mean  = [e["mean_logits"]["mean"] for e in multilen]
ml_std   = [e["mean_logits"]["std"]  for e in multilen]
sr_mean  = [e["single_random"]["mean"] for e in multilen]
ps_mean  = [e["per_slice_avg"]["mean"] for e in multilen]

fig, ax = plt.subplots(figsize=(10, 5.5))
ax.errorbar(Ls, ml_mean, yerr=ml_std, marker="o", lw=2, capsize=4,
            color="#1abc9c", label="mean_logits (ensemble)")
ax.plot(Ls, sr_mean, marker="s", lw=1.5, ls="--", color="#3498db",
        label="single_random (1 slice)")
ax.plot(Ls, ps_mean, marker="^", lw=1.5, ls=":",  color="#9b59b6",
        label="per_slice_avg")
ax.axhline(0.944, color="#e74c3c", ls="--", lw=1.4, alpha=0.7, label="CNN @ L=106 = 0.944")
ax.axhline(0.806, color="#888",    ls=":",  lw=1.4, alpha=0.7, label="Transformer baseline @ L=106 = 0.806")

# annotate best
best_i = int(np.argmax(ml_mean))
ax.annotate(f"best: L={Ls[best_i]}\n{ml_mean[best_i]:.3f}",
            xy=(Ls[best_i], ml_mean[best_i]), xytext=(Ls[best_i]+2, ml_mean[best_i]+0.012),
            arrowprops={"arrowstyle": "->", "color": "#16a085"},
            fontsize=10, color="#16a085", fontweight="bold")

ax.invert_xaxis()  # so shorter windows are to the right
ax.set_xlabel("Test window length L (time points)")
ax.set_ylabel("Accuracy")
ax.set_ylim(0.78, 0.96)
ax.set_title("Multi-length Test Evaluation (using v3 ckpt, no retraining)", fontsize=12, pad=12)
ax.legend(loc="lower right", fontsize=9)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUT / "multilen.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"saved {OUT / 'multilen.png'}")
