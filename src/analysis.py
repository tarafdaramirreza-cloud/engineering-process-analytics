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

    numeric_summary = data.select_dtypes(include="number").describe().T.round(3)
    numeric_summary.to_csv(
        output_dir / "summary_statistics.csv", lineterminator="\n"
    )
    timestamp_summary = pd.DataFrame({
        "start_timestamp": [data.timestamp.min().isoformat(sep=" ")],
        "end_timestamp": [data.timestamp.max().isoformat(sep=" ")],
        "duration": [str(data.timestamp.max() - data.timestamp.min())],
        "observation_count": [len(data)],
    })
    timestamp_summary.to_csv(
        output_dir / "timestamp_summary.csv", index=False, lineterminator="\n"
    )
    for group in ["machine_id", "material_type"]:
        summary = data.groupby(group)[OUTCOMES].agg(["count", "mean", "std"])
        summary.columns = [f"{column}_{stat}" for column, stat in summary.columns]
        summary.reset_index().round(3).to_csv(
            output_dir / f"by_{group}.csv", index=False, lineterminator="\n"
        )
    correlation = data[INPUTS + OUTCOMES].corr()
    correlation.to_csv(output_dir / "correlations.csv", lineterminator="\n")
    regions = []
    for name, mask in region_masks(data).items():
        for label, selected in [(name, mask), (f"outside_{name}", ~mask)]:
            row = {"region": label, "batch_count": int(selected.sum())}
            row.update(data.loc[selected, OUTCOMES].mean().to_dict())
            regions.append(row)
    region_table = pd.DataFrame(regions).set_index("region")
    region_table.round(3).to_csv(
        output_dir / "region_comparisons.csv", lineterminator="\n"
    )
    candidate_mask = region_masks(data)["candidate_screen"]
    material_rows = []
    for material in sorted(data.material_type.unique()):
        material_mask = data.material_type.eq(material)
        inside = data.loc[material_mask & candidate_mask]
        outside = data.loc[material_mask & ~candidate_mask]
        material_rows.append({
            "material_type": material,
            "inside_count": len(inside),
            "outside_count": len(outside),
            "inside_defect_rate_percent_mean": inside.defect_rate_percent.mean(),
            "outside_defect_rate_percent_mean": outside.defect_rate_percent.mean(),
            "inside_energy_kWh_mean": inside.energy_kWh.mean(),
            "outside_energy_kWh_mean": outside.energy_kWh.mean(),
        })
    material_region_table = pd.DataFrame(material_rows)
    material_region_table.round(3).to_csv(
        output_dir / "candidate_region_by_material.csv", index=False,
        lineterminator="\n",
    )
    return {
        "rows": len(data), "means": data[OUTCOMES].mean().to_dict(),
        "regions": region_table.to_dict(orient="index"),
        "machine_defect_means": data.groupby("machine_id").defect_rate_percent.mean().to_dict(),
        "material_defect_means": data.groupby("material_type").defect_rate_percent.mean().to_dict(),
        "candidate_by_material": material_region_table.set_index(
            "material_type"
        ).to_dict(orient="index"),
        "temperature_defect_pearson": float(correlation.loc["temperature_C", "defect_rate_percent"]),
        "maximum_defect_rate_percent": float(data.defect_rate_percent.max()),
    }
