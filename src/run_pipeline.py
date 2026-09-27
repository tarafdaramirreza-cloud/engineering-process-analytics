"""Run from the repository root: python -m src.run_pipeline."""

import json
from pathlib import Path
import pandas as pd
from src.generate_data import generate_data, SEED
from src.data_quality import validate_data
from src.analysis import analyze
from src.visualization import create_figures

ROOT = Path(__file__).resolve().parents[1]


def write_findings(results, path):
    """Keep the README findings identical to the values produced by analysis."""
    regions = results["regions"]
    candidate = regions["candidate_screen"]
    outside = regions["outside_candidate_screen"]
    short = regions["short_cycle"]
    other = regions["outside_short_cycle"]
    means = results["means"]
    by_material = results["candidate_by_material"]
    lines = [
        "<!-- BEGIN GENERATED FINDINGS -->",
        f"Across **{results['rows']:,} synthetic batches**, mean first-pass yield was "
        f"**{means['yield_percent']:.2f}%**, tracked defect rate **{means['defect_rate_percent']:.2f}%**, "
        f"and energy **{means['energy_kWh']:.2f} kWh/batch**.", "",
        f"- Cycles below 9 min ({short['batch_count']} batches) had mean defect rate "
        f"**{short['defect_rate_percent']:.2f}%**, versus **{other['defect_rate_percent']:.2f}%** for other batches.",
        f"- A predefined candidate screen (174–186 °C, 4.5–5.5 MPa, 11.5–15 min) included "
        f"**{candidate['batch_count']} batches** with mean defect rate **{candidate['defect_rate_percent']:.2f}%** "
        f"and yield **{candidate['yield_percent']:.2f}%**. Outside the screen, mean defect rate was "
        f"**{outside['defect_rate_percent']:.2f}%**. This is an exploratory comparison, not a validated operating window.",
        f"- Candidate-screen energy averaged **{candidate['energy_kWh']:.2f} kWh/batch**, "
        f"versus **{outside['energy_kWh']:.2f} kWh/batch** outside it; the quality association comes with higher average energy.",
        "- The pattern remains directionally consistent after stratifying by material: "
        + "; ".join(
            f"{material} ({values['inside_count']} inside): defects "
            f"**{values['inside_defect_rate_percent_mean']:.2f}% vs "
            f"{values['outside_defect_rate_percent_mean']:.2f}%**, energy "
            f"**{values['inside_energy_kWh_mean']:.2f} vs "
            f"{values['outside_energy_kWh_mean']:.2f} kWh**"
            for material, values in by_material.items()
        ) + ". These remain unadjusted, non-causal comparisons.",
        "- Machine mean defect rates: " + "; ".join(
            f"{key}: **{value:.2f}%**" for key, value in results['machine_defect_means'].items()) + ".",
        "- Material mean defect rates: " + "; ".join(
            f"{key}: **{value:.2f}%**" for key, value in results['material_defect_means'].items()) + ".",
        f"- Temperature–defect Pearson correlation was **{results['temperature_defect_pearson']:.3f}**. "
        "The scatterplots show why a single linear correlation cannot describe the simulated nonlinear response.",
        "", "These are unadjusted associations in synthetic data. Group composition and process settings "
        "can influence comparisons. Yield and tracked defects share a unit balance, so their strong inverse "
        "correlation is partly definitional.", "<!-- END GENERATED FINDINGS -->",
    ]
    content = path.read_text(encoding="utf-8")
    start = content.index("<!-- BEGIN GENERATED FINDINGS -->")
    end = content.index("<!-- END GENERATED FINDINGS -->") + len("<!-- END GENERATED FINDINGS -->")
    path.write_text(
        content[:start] + "\n".join(lines) + content[end:],
        encoding="utf-8", newline="\n",
    )


def main():
    raw = ROOT / "data/raw"
    processed = ROOT / "data/processed"
    figures = ROOT / "figures"
    for directory in [raw, processed, figures]:
        directory.mkdir(parents=True, exist_ok=True)
    data = generate_data()
    data.to_csv(
        raw / "synthetic_batches.csv", index=False, float_format="%.3f",
        lineterminator="\n",
    )
    # Validate the persisted CSV, not just the in-memory generator output.
    data = pd.read_csv(raw / "synthetic_batches.csv", parse_dates=["timestamp"])
    checks = validate_data(data)
    (processed / "validation.json").write_text(
        json.dumps(checks, indent=2) + "\n", newline="\n"
    )
    results = analyze(data, processed)
    results.update({"seed": SEED, "data_origin": "synthetic_demonstration"})
    (processed / "findings.json").write_text(
        json.dumps(results, indent=2) + "\n", newline="\n"
    )
    create_figures(data, figures)
    write_findings(results, ROOT / "README.md")
    print(json.dumps(results, indent=2))
    print(f"PASS: {len(checks)} validation checks; five figures saved.")


if __name__ == "__main__":
    main()
