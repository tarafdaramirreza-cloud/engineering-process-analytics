"""Matplotlib figures labeled explicitly as synthetic demonstration data."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.analysis import INPUTS, OUTCOMES, region_masks

LABELS = {
    "temperature_C": "Temperature (°C)", "pressure_MPa": "Pressure (MPa)",
    "cycle_time_min": "Cycle time (min)", "yield_percent": "First-pass yield (%)",
    "defect_rate_percent": "Tracked defect rate (%)", "energy_kWh": "Energy per batch (kWh)",
}


def save_figure(fig, output_dir, name, title):
    fig.suptitle(title, fontsize=16, fontweight="bold")
    fig.text(0.5, 0.014, "SYNTHETIC DATA • Demonstration only • Descriptive associations",
             ha="center", fontsize=9, color="#526173")
    fig.tight_layout(rect=(0, 0.045, 1, 0.95))
    fig.savefig(output_dir / f"{name}.png", dpi=180, facecolor="white")
    plt.close(fig)


def create_figures(data, output_dir):
    """Save five recruiter-facing views of the synthetic process."""
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.titlepad": 10})
    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    for ax, column in zip(axes.flat, INPUTS + OUTCOMES):
        ax.hist(data[column], bins=35, color="#276C8E", edgecolor="white", linewidth=0.3)
        ax.set(xlabel=LABELS[column], ylabel="Batches")
    save_figure(fig, output_dir, "distributions",
                f"Process settings and batch outcomes | n = {len(data):,}")

    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    for row, group in enumerate(["machine_id", "material_type"]):
        for ax, outcome in zip(axes[row], OUTCOMES):
            levels = sorted(data[group].unique())
            ax.boxplot([data.loc[data[group].eq(level), outcome] for level in levels],
                       tick_labels=levels, showfliers=False, widths=0.5)
            ax.set(xlabel="Machine" if row == 0 else "Material", ylabel=LABELS[outcome])
    save_figure(fig, output_dir, "group_comparisons", "Batch variability across groups | outlier markers omitted")

    fig, axes = plt.subplots(3, 3, figsize=(13, 11))
    colors = {"A": "#276C8E", "B": "#D27835", "C": "#728644"}
    for row, outcome in enumerate(OUTCOMES):
        for ax, setting in zip(axes[row], INPUTS):
            for material, color in colors.items():
                subset = data[data.material_type.eq(material)]
                ax.scatter(subset[setting], subset[outcome], s=5, alpha=0.22,
                           color=color, label=material, rasterized=True)
            ax.set(xlabel=LABELS[setting], ylabel=LABELS[outcome])
    axes[0, 0].legend(title="Material", markerscale=3)
    save_figure(fig, output_dir, "process_relationships", "Process–outcome associations | nonlinear response and noise")

    columns = INPUTS + OUTCOMES
    corr = data[columns].corr()
    fig, ax = plt.subplots(figsize=(10, 8))
    heat = ax.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(6), [LABELS[c] for c in columns], rotation=35, ha="right")
    ax.set_yticks(range(6), [LABELS[c] for c in columns])
    for i, j in np.ndindex(corr.shape):
        value = corr.iloc[i, j]
        ax.text(j, i, f"{value:.2f}", ha="center", va="center",
                color="white" if abs(value) > 0.65 else "#182737")
    fig.colorbar(heat, ax=ax, label="Pearson correlation (linear association)", shrink=0.8)
    save_figure(fig, output_dir, "correlations", "Linear correlations can miss nonlinear process behavior")

    candidate = region_masks(data)["candidate_screen"]
    labels = ["Inside candidate region", "Outside candidate region"]
    inside = data.loc[candidate]
    outside = data.loc[~candidate]
    defect_values = [inside.defect_rate_percent.mean(), outside.defect_rate_percent.mean()]
    energy_values = [inside.energy_kWh.mean(), outside.energy_kWh.mean()]
    fig, axes = plt.subplots(1, 2, figsize=(10, 5.8))
    colors = ["#2A7F62", "#64748B"]
    for ax, values, ylabel, heading in [
        (axes[0], defect_values, "Mean tracked defect rate (%)", "Quality"),
        (axes[1], energy_values, "Mean energy per batch (kWh)", "Energy"),
    ]:
        bars = ax.bar(labels, values, color=colors, width=0.62)
        ax.set(ylabel=ylabel, title=heading)
        ax.tick_params(axis="x", rotation=12)
        ax.bar_label(bars, fmt="%.2f", padding=4, fontweight="bold")
        ax.set_ylim(0, max(values) * 1.25)
    save_figure(
        fig, output_dir, "candidate_region_tradeoff",
        "Candidate region: lower defects with higher energy use",
    )
