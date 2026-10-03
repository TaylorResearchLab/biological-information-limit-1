#!/usr/bin/env python3
"""Generate the three manuscript figures from the reported numerical values."""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

OUT = Path(__file__).resolve().parent
OUT.mkdir(exist_ok=True)

# Figure 1: TCR proofreading.
N = np.array([1, 2, 3, 4, 8])
info = np.array([0.560503, 0.612789, 0.546158, 0.475227, 0.285260])
log10_ratio = np.array([1, 2, 3, 4, 8])

fig, ax1 = plt.subplots(figsize=(7.2, 4.6))
line1, = ax1.plot(N, info, marker="o", linewidth=2, label="Mutual information")
ax1.set_xlabel("Required proofreading steps")
ax1.set_ylabel("Information in completion outcome (bits)")
ax1.set_ylim(0, 0.7)
ax1.set_xticks(N)
ax1.grid(axis="y", alpha=0.25)

ax2 = ax1.twinx()
line2, = ax2.plot(N, log10_ratio, marker="s", linewidth=2,
                  label="log10 agonist/self passage ratio")
ax2.set_ylabel("log10 agonist/self full-proofreading passage ratio")
ax2.set_ylim(0, 8.8)
ax2.yaxis.set_major_locator(MaxNLocator(integer=True))
for x, y, r in zip(N, log10_ratio, [10, 100, 1000, 10000, 100000000]):
    ax2.annotate(f"{r:,}×", (x, y), xytext=(0, 7),
                 textcoords="offset points", ha="center", fontsize=8)
ax1.legend([line1, line2], [line1.get_label(), line2.get_label()],
           loc="lower left", frameon=False)
fig.tight_layout()
fig.savefig(OUT / "Figure1_TCR_proofreading.png", dpi=350, bbox_inches="tight")
plt.close(fig)

# Figure 2: Ribosome staged inference.
fig, ax = plt.subplots(figsize=(8.6, 4.8))
ax.set_axis_off()
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
box = dict(boxstyle="round,pad=0.42", fill=False, linewidth=1.4)

y = 0.80
xs = [0.09, 0.36, 0.63, 0.90]
labels = ["Original tRNA\nencounter", "Initial selection", "Proofreading",
          "Accepted peptide\nproduct"]
for x, label in zip(xs, labels):
    ax.text(x, y, label, ha="center", va="center", bbox=box, fontsize=10.5)
for x0, x1 in [(0.17, 0.28), (0.44, 0.55), (0.71, 0.82)]:
    ax.annotate("", xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle="->", linewidth=1.4))

ax.text(0.34, 0.52,
        "Upstream passage $a_s$\nsets how many and which tRNAs\nreach proofreading",
        ha="center", va="center", fontsize=8.8)
ax.text(0.64, 0.52,
        "Published proofreading acceptance\nconstrains local information\n"
        "WT: 0.616–0.859 bits\nRestrictive: 0.713–0.990 bits",
        ha="center", va="center", fontsize=8.5)
ax.text(0.88, 0.52,
        "Final peptide-product ratio\nalso depends on upstream\nfactor $U$",
        ha="center", va="center", fontsize=8.8)
ax.axhline(0.34, linewidth=0.8)
ax.text(0.50, 0.23,
        "Holding proofreading fixed: passage 1.0 → 0.1 → 0.01\n"
        "information per original encounter 0.825 → 0.0465 → 0.00450 bits",
        ha="center", va="center", fontsize=9.2)
ax.text(0.50, 0.07,
        "Local proofreading information and whole-encounter information are different quantities.",
        ha="center", va="center", fontsize=9.5)
fig.tight_layout()
fig.savefig(OUT / "Figure2_Ribosome_stages.png", dpi=350, bbox_inches="tight")
plt.close(fig)

# Figure 3: Msn2 compatible information ranges.
labels = [
    "1-copy: 100 nM vs 3 μM",
    "1-copy: 175 nM vs 7 pulses",
    "2-copy: 7 vs 8 pulses",
    "",
    "175 nM vs 7 pulses: neither paired",
    "  sustained condition paired",
    "  7-pulse condition paired",
    "  both conditions paired",
]
lo = np.array([0.617718, 0.008983, 0.008233, np.nan,
               0.008983, 0.012823, 0.011679, 0.013934])
hi = np.array([0.944468, 0.916266, 0.726611, np.nan,
               0.916266, 0.395666, 0.281039, 0.013934])
obs = np.array([0.775954, 0.013934, 0.009197, np.nan,
                0.013934, 0.013934, 0.013934, 0.013934])
y = np.arange(len(labels))[::-1]

fig, ax = plt.subplots(figsize=(7.4, 5.5))
for yi, l, h, o, lab in zip(y, lo, hi, obs, labels):
    if not lab:
        continue
    ax.plot([l, h], [yi, yi], linewidth=5, solid_capstyle="butt")
    ax.plot(o, yi, marker="o", markersize=6)
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=9)
ax.set_xlim(0, 1)
ax.set_xlabel("Mutual information (bits)")
ax.grid(axis="x", alpha=0.25)
ax.set_title("Information compatible with incomplete versus paired Msn2 reporter observations",
             fontsize=11)
ax.text(0.0, y[4] + 0.65, "Progressive restoration of same-cell pairing",
        fontsize=9.5, fontweight="bold")
fig.tight_layout()
fig.savefig(OUT / "Figure3_Msn2_information_ranges.png", dpi=350, bbox_inches="tight")
plt.close(fig)
