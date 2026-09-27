"""Validate recorded batch values before analyzing synthetic demonstration data."""

import pandas as pd

RANGES = {
    "temperature_C": (140, 220), "pressure_MPa": (2.5, 7.5),
    "cycle_time_min": (6, 19), "yield_percent": (0, 100),
    "defect_rate_percent": (0, 100), "other_loss_percent": (0, 100),
    "energy_kWh": (0.001, 200),
}
REQUIRED = ["batch_id", "timestamp", "material_type", "machine_id",
            *RANGES, "data_origin"]


def validate_data(data, expected_rows=3000):
    """Return auditable checks; stop the pipeline if any check fails."""
    missing_columns = sorted(set(REQUIRED) - set(data.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    checks = {
        "expected_row_count": len(data) == expected_rows,
        "no_missing_values": not data.isna().any().any(),
        "no_duplicate_rows": not data.duplicated().any(),
        "unique_batch_ids": data.batch_id.is_unique,
        "batch_id_format": data.batch_id.astype(str).str.fullmatch(r"B\d{5,}").all(),
        "timestamp_dtype": pd.api.types.is_datetime64_any_dtype(data.timestamp),
        "unique_timestamps": data.timestamp.is_unique,
        "ordered_timestamps": data.timestamp.is_monotonic_increasing,
        "valid_materials": data.material_type.isin(["A", "B", "C"]).all(),
        "valid_machines": data.machine_id.isin(["M1", "M2", "M3"]).all(),
        "synthetic_label": data.data_origin.eq("synthetic_demonstration").all(),
    }
    for column, (low, high) in RANGES.items():
        numeric = pd.api.types.is_numeric_dtype(data[column])
        checks[f"{column}_numeric"] = numeric
        checks[f"{column}_range"] = numeric and data[column].between(low, high).all()
    rate_columns = ["yield_percent", "defect_rate_percent", "other_loss_percent"]
    checks["unit_balance"] = all(checks[f"{c}_numeric"] for c in rate_columns)
    if checks["unit_balance"]:
        checks["unit_balance"] = data[rate_columns].sum(axis=1).sub(100).abs().lt(1e-8).all()
    checks = {name: bool(passed) for name, passed in checks.items()}
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError(f"Data validation failed: {failed}")
    return checks
