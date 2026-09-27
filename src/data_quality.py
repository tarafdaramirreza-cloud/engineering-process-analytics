"""Validate recorded batch values before analyzing synthetic demonstration data."""

import pandas as pd

from src.generate_data import START_TIMESTAMP, TIMESTAMP_FREQUENCY

RANGES = {
    "temperature_C": (140, 220), "pressure_MPa": (2.5, 7.5),
    "cycle_time_min": (6, 19), "yield_percent": (0, 100),
    "defect_rate_percent": (0, 100), "other_loss_percent": (0, 100),
    "energy_kWh": (0.001, 200),
}
EXPECTED_SCHEMA = [
    "batch_id", "timestamp", "material_type", "machine_id",
    "temperature_C", "pressure_MPa", "cycle_time_min", "yield_percent",
    "defect_rate_percent", "other_loss_percent", "energy_kWh", "data_origin",
]
# Retained as a readable compatibility alias for callers and tests.
REQUIRED = EXPECTED_SCHEMA

STRING_COLUMNS = ["batch_id", "material_type", "machine_id", "data_origin"]
NUMERIC_COLUMNS = list(RANGES)


def validate_data(data, expected_rows=3000):
    """Return auditable checks; stop the pipeline if any check fails."""
    expected_ids = pd.Series([f"B{i:05d}" for i in range(1, expected_rows + 1)])
    expected_start = pd.Timestamp(START_TIMESTAMP)
    expected_step = pd.Timedelta(TIMESTAMP_FREQUENCY)
    checks = {
        "exact_schema": list(data.columns) == EXPECTED_SCHEMA,
        "expected_row_count": len(data) == expected_rows,
        "no_missing_values": not data.isna().any().any(),
        "no_duplicate_rows": not data.duplicated().any(),
    }
    if checks["exact_schema"]:
        timestamp_is_datetime = pd.api.types.is_datetime64_any_dtype(data.timestamp)
        checks.update({
            "string_dtypes": all(
                pd.api.types.is_object_dtype(data[column])
                or pd.api.types.is_string_dtype(data[column])
                for column in STRING_COLUMNS
            ),
            "numeric_dtypes": all(
                pd.api.types.is_numeric_dtype(data[column])
                for column in NUMERIC_COLUMNS
            ),
            "timestamp_dtype": timestamp_is_datetime,
            "sequential_batch_ids": data.batch_id.reset_index(drop=True).equals(
                expected_ids.reset_index(drop=True)
            ),
            "timestamp_start": timestamp_is_datetime and len(data) > 0
            and data.timestamp.iloc[0] == expected_start,
            "timestamp_cadence": timestamp_is_datetime and len(data) > 1
            and data.timestamp.diff().iloc[1:].eq(expected_step).all(),
            "timestamps_strictly_increasing": timestamp_is_datetime
            and data.timestamp.is_monotonic_increasing
            and data.timestamp.is_unique,
            "valid_materials": data.material_type.isin(["A", "B", "C"]).all(),
            "valid_machines": data.machine_id.isin(["M1", "M2", "M3"]).all(),
            "synthetic_label": data.data_origin.eq("synthetic_demonstration").all(),
        })
    else:
        checks["schema_dependent_checks"] = False
    for column, (low, high) in RANGES.items():
        present = column in data.columns
        numeric = present and pd.api.types.is_numeric_dtype(data[column])
        checks[f"{column}_range"] = numeric and data[column].between(low, high).all()
    rate_columns = ["yield_percent", "defect_rate_percent", "other_loss_percent"]
    checks["unit_balance"] = all(
        column in data.columns and pd.api.types.is_numeric_dtype(data[column])
        for column in rate_columns
    )
    if checks["unit_balance"]:
        checks["unit_balance"] = data[rate_columns].sum(axis=1).sub(100).abs().lt(1e-8).all()
    checks = {name: bool(passed) for name, passed in checks.items()}
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError(f"Data validation failed: {failed}")
    return checks
