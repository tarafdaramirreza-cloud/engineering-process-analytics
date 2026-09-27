"""Descriptive associations only; these comparisons do not establish causality."""

OUTCOMES = ["yield_percent", "defect_rate_percent", "energy_kWh"]
INPUTS = ["temperature_C", "pressure_MPa", "cycle_time_min"]


def region_masks(data):
    """Predefined illustrative screens, not optimized operating recommendations."""
    return {
        "candidate_screen": (data.temperature_C.between(174, 186)
                             & data.pressure_MPa.between(4.5, 5.5)
                             & data.cycle_time_min.between(11.5, 15)),
        "short_cycle": data.cycle_time_min.lt(9),
        "temperature_tails": ~data.temperature_C.between(160, 200),
    }


def analyze(data, output_dir):
    """Save transparent tables and return the findings used in the README."""
    import pandas as pd

    data.describe(include="all").to_csv(output_dir / "summary_statistics.csv")
    for group in ["machine_id", "material_type"]:
        data.groupby(group)[OUTCOMES].agg(["count", "mean", "std"]).to_csv(
            output_dir / f"by_{group}.csv")
    correlation = data[INPUTS + OUTCOMES].corr()
    correlation.to_csv(output_dir / "correlations.csv")
    regions = []
    for name, mask in region_masks(data).items():
        for label, selected in [(name, mask), (f"outside_{name}", ~mask)]:
            row = {"region": label, "batch_count": int(selected.sum())}
            row.update(data.loc[selected, OUTCOMES].mean().to_dict())
            regions.append(row)
    region_table = pd.DataFrame(regions).set_index("region")
    region_table.to_csv(output_dir / "region_comparisons.csv")
    return {
        "rows": len(data), "means": data[OUTCOMES].mean().to_dict(),
        "regions": region_table.to_dict(orient="index"),
        "machine_defect_means": data.groupby("machine_id").defect_rate_percent.mean().to_dict(),
        "material_defect_means": data.groupby("material_type").defect_rate_percent.mean().to_dict(),
        "temperature_defect_pearson": float(correlation.loc["temperature_C", "defect_rate_percent"]),
    }
