"""Create demonstration data; parameters are illustrative, not calibrated physics."""

import numpy as np
import pandas as pd

SEED = 42
ROW_COUNT = 3000


def generate_data(n_batches=ROW_COUNT, seed=SEED):
    """Simulate equal-size batches with nonlinear response and unobserved noise.

    Yield means first-pass conforming units. Defect rate means units with at
    least one tracked defect; a separate loss category accounts for the rest.
    All batches contain 1,000 units, so rates have 0.1 percentage-point steps.
    """
    if not isinstance(n_batches, int) or n_batches < 1:
        raise ValueError("n_batches must be a positive integer")
    rng = np.random.default_rng(seed)
    material = rng.choice(["A", "B", "C"], n_batches, p=[0.45, 0.35, 0.20])
    machine = rng.choice(["M1", "M2", "M3"], n_batches)
    material_shift = pd.Series(material).map({"A": 0, "B": 7, "C": -6}).to_numpy()
    machine_shift = pd.Series(machine).map({"M1": -0.12, "M2": 0, "M3": 0.16}).to_numpy()
    temperature = np.clip(rng.normal(180 + material_shift * 0.35, 12), 140, 220)
    pressure = np.clip(rng.normal(5.0, 0.75, n_batches), 2.5, 7.5)
    cycle = np.clip(rng.normal(12, 2.0, n_batches), 6, 19)
    # Use recorded precision in the response equations for reproducibility.
    temperature = temperature.round(2)
    pressure = pressure.round(3)
    cycle = cycle.round(2)
    thermal_offset = (temperature - (180 + material_shift)) / 14
    pressure_offset = (pressure - 5.0) / 0.9
    short_cycle = np.maximum(11.5 - cycle, 0) / 2
    # Squared terms create poor regions; interaction changes thermal sensitivity.
    log_odds = (-3.65 + 0.48 * thermal_offset**2
                + 0.28 * pressure_offset**2 + 0.45 * short_cycle**2
                - 0.20 * thermal_offset * pressure_offset + machine_shift
                + rng.normal(0, 0.40, n_batches))
    defect_probability = 1 / (1 + np.exp(-log_odds))
    defect_units = rng.binomial(1000, defect_probability)
    # Handling/startup losses are disjoint from tracked defects.
    other_probability = np.clip(rng.normal(0.014, 0.005, n_batches), 0.002, 0.04)
    other_loss_units = rng.binomial(1000 - defect_units, other_probability)
    good_units = 1000 - defect_units - other_loss_units
    energy_factor = pd.Series(machine).map({"M1": 0.97, "M2": 1, "M3": 1.04}).to_numpy()
    energy = (8 + 0.065 * (temperature - 20) + 0.85 * cycle
              + 0.65 * pressure + 0.018 * (temperature - 160) * cycle)
    energy *= energy_factor * rng.lognormal(0, 0.055, n_batches)
    return pd.DataFrame({
        "batch_id": [f"B{i:05d}" for i in range(1, n_batches + 1)],
        "timestamp": pd.date_range("2025-01-01", periods=n_batches, freq="30min"),
        "material_type": material, "machine_id": machine,
        "temperature_C": temperature, "pressure_MPa": pressure,
        "cycle_time_min": cycle, "yield_percent": good_units / 10,
        "defect_rate_percent": defect_units / 10,
        "other_loss_percent": other_loss_units / 10,
        "energy_kWh": energy.round(3),
        "data_origin": "synthetic_demonstration",
    })
