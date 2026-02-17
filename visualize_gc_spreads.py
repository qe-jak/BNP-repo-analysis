#!/usr/bin/env python3
"""
Cantor BNP Repo Market Data - GC Spread Time Series Visualization
Generates multiple charts analyzing repo rate trends across tenors and terms.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
import os

# ── Configuration ──────────────────────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "charts")
CSV_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "Cantor BNP Repo Market Data - GC spread time series.csv",
)
os.makedirs(OUTPUT_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({"figure.dpi": 150, "savefig.bbox": "tight"})

# ── Load & Clean ───────────────────────────────────────────────────────────────
df = pd.read_csv(CSV_FILE, skiprows=1)  # skip the "AVERAGE of Avg up to 7am" row
df["time"] = pd.to_datetime(df["time"], errors="coerce")
df = df.dropna(subset=["time"])

# Replace #DIV/0! and blanks with NaN, convert to float
for col in df.columns[1:]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Define column groups
base_tenors = ["2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
gc_col = "GC"

# Group by term prefix: base = same-day, O = overnight, OO = 2-day, OOO = 3-day
groups = {
    "Same-Day": base_tenors,
    "O (Overnight)": [f"O{t}" for t in base_tenors],
    "OO (2-Day)": [f"OO{t}" for t in base_tenors],
    "OOO (3-Day)": [f"OOO{t}" for t in base_tenors],
}

# Colors for tenors
tenor_colors = {
    "2Y": "#1f77b4",
    "3Y": "#ff7f0e",
    "5Y": "#2ca02c",
    "7Y": "#d62728",
    "10Y": "#9467bd",
    "20Y": "#8c564b",
    "30Y": "#e377c2",
}


def format_date_axis(ax):
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)


# ── Chart 1: GC Rate + Base Tenors Over Time ──────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(df["time"], df[gc_col], color="black", linewidth=2.5, label="GC Rate", zorder=5)
for tenor in base_tenors:
    if tenor in df.columns:
        ax.plot(
            df["time"], df[tenor], color=tenor_colors[tenor],
            linewidth=1.2, alpha=0.8, label=tenor,
        )
ax.set_title("Repo Rates: GC vs Tenor Curves (Same-Day)", fontsize=14, fontweight="bold")
ax.set_ylabel("Rate (%)", fontsize=11)
ax.legend(loc="upper right", fontsize=8, ncol=4)
format_date_axis(ax)
ax.set_ylim(bottom=max(0, df[base_tenors + [gc_col]].min().min() - 0.5))
fig.savefig(os.path.join(OUTPUT_DIR, "01_gc_vs_tenors.png"))
plt.close(fig)
print("✓ Chart 1: GC vs Tenors saved")

# ── Chart 2: Spread to GC (each tenor minus GC) ──────────────────────────────
fig, ax = plt.subplots(figsize=(14, 6))
for tenor in base_tenors:
    if tenor in df.columns:
        spread = df[tenor] - df[gc_col]
        ax.plot(
            df["time"], spread * 100, color=tenor_colors[tenor],
            linewidth=1.3, label=f"{tenor} − GC",
        )
ax.axhline(y=0, color="black", linewidth=0.8, linestyle="--")
ax.set_title("Spread to GC Rate by Tenor (bps)", fontsize=14, fontweight="bold")
ax.set_ylabel("Spread (bps)", fontsize=11)
ax.legend(loc="lower left", fontsize=8, ncol=4)
format_date_axis(ax)
fig.savefig(os.path.join(OUTPUT_DIR, "02_spread_to_gc.png"))
plt.close(fig)
print("✓ Chart 2: Spread to GC saved")

# ── Chart 3: Term Structure Comparison (Same-Day vs O vs OO vs OOO) ──────────
fig, axes = plt.subplots(2, 2, figsize=(16, 10), sharex=True, sharey=True)
for ax, (group_name, cols) in zip(axes.flat, groups.items()):
    for col in cols:
        if col in df.columns:
            # Extract tenor label
            tenor = col.lstrip("O")
            ax.plot(
                df["time"], df[col], color=tenor_colors.get(tenor, "gray"),
                linewidth=1.2, alpha=0.85, label=tenor,
            )
    ax.plot(df["time"], df[gc_col], color="black", linewidth=2, alpha=0.5, label="GC", linestyle="--")
    ax.set_title(group_name, fontsize=12, fontweight="bold")
    ax.set_ylabel("Rate (%)", fontsize=9)
    ax.legend(fontsize=7, ncol=4, loc="upper right")
    format_date_axis(ax)

fig.suptitle("Term Structure Comparison Across Settlement Periods", fontsize=14, fontweight="bold", y=1.01)
fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "03_term_structure_comparison.png"))
plt.close(fig)
print("✓ Chart 3: Term Structure Comparison saved")

# ── Chart 4: Heatmap of Rates Over Time ───────────────────────────────────────
heatmap_cols = [gc_col] + base_tenors
heatmap_df = df.set_index("time")[heatmap_cols].dropna(how="all")
heatmap_df.index = heatmap_df.index.strftime("%Y-%m-%d")

fig, ax = plt.subplots(figsize=(10, 14))
sns.heatmap(
    heatmap_df, cmap="RdYlGn_r", ax=ax, linewidths=0.3,
    cbar_kws={"label": "Rate (%)"},
    xticklabels=True, yticklabels=True,
)
ax.set_title("Daily Rate Heatmap (GC + Base Tenors)", fontsize=14, fontweight="bold")
ax.set_ylabel("")
ax.set_xlabel("")
plt.yticks(fontsize=7)
fig.savefig(os.path.join(OUTPUT_DIR, "04_rate_heatmap.png"))
plt.close(fig)
print("✓ Chart 4: Rate Heatmap saved")

# ── Chart 5: Volatility (Rolling 5-Day Std Dev) ──────────────────────────────
fig, ax = plt.subplots(figsize=(14, 6))
for tenor in base_tenors:
    if tenor in df.columns:
        rolling_std = df[tenor].rolling(window=5).std() * 100  # in bps
        ax.plot(
            df["time"], rolling_std, color=tenor_colors[tenor],
            linewidth=1.2, label=tenor,
        )
gc_std = df[gc_col].rolling(window=5).std() * 100
ax.plot(df["time"], gc_std, color="black", linewidth=2, label="GC")
ax.set_title("5-Day Rolling Volatility (Std Dev in bps)", fontsize=14, fontweight="bold")
ax.set_ylabel("Volatility (bps)", fontsize=11)
ax.legend(loc="upper right", fontsize=8, ncol=4)
format_date_axis(ax)
fig.savefig(os.path.join(OUTPUT_DIR, "05_rolling_volatility.png"))
plt.close(fig)
print("✓ Chart 5: Rolling Volatility saved")

# ── Chart 6: Term Spread Curve Snapshots ──────────────────────────────────────
# Pick a few representative dates to show the yield curve shape
snapshot_dates = df["time"].iloc[
    np.linspace(0, len(df) - 1, min(6, len(df)), dtype=int)
].tolist()

tenor_order = ["2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
fig, ax = plt.subplots(figsize=(10, 6))
cmap = plt.cm.viridis(np.linspace(0, 1, len(snapshot_dates)))

for i, date in enumerate(snapshot_dates):
    row = df[df["time"] == date].iloc[0]
    rates = [row[t] if t in df.columns and pd.notna(row[t]) else np.nan for t in tenor_order]
    ax.plot(
        tenor_order, rates, marker="o", color=cmap[i],
        linewidth=1.8, label=date.strftime("%Y-%m-%d"),
    )

ax.set_title("Repo Rate Curve Snapshots (Same-Day)", fontsize=14, fontweight="bold")
ax.set_ylabel("Rate (%)", fontsize=11)
ax.set_xlabel("Tenor", fontsize=11)
ax.legend(fontsize=9, title="Date")
ax.grid(True, alpha=0.3)
fig.savefig(os.path.join(OUTPUT_DIR, "06_curve_snapshots.png"))
plt.close(fig)
print("✓ Chart 6: Curve Snapshots saved")

# ── Chart 7: Correlation Matrix ───────────────────────────────────────────────
corr_cols = [gc_col] + base_tenors
corr_df = df[corr_cols].dropna()
corr_matrix = corr_df.corr()

fig, ax = plt.subplots(figsize=(8, 7))
sns.heatmap(
    corr_matrix, annot=True, fmt=".2f", cmap="coolwarm",
    ax=ax, vmin=0.5, vmax=1, square=True,
    linewidths=0.5, cbar_kws={"label": "Correlation"},
)
ax.set_title("Rate Correlation Matrix (GC + Base Tenors)", fontsize=14, fontweight="bold")
fig.savefig(os.path.join(OUTPUT_DIR, "07_correlation_matrix.png"))
plt.close(fig)
print("✓ Chart 7: Correlation Matrix saved")

print(f"\nAll charts saved to: {OUTPUT_DIR}/")
