import numpy as np
import pandas as pd


def triangular_hydrograph(
    peak_discharge_m3s: float,
    formation_time_hr: float,
    total_duration_hr: float,
    time_steps: int = 160,
) -> pd.DataFrame:
    """Generate a simple triangular breach outflow hydrograph."""
    if peak_discharge_m3s <= 0:
        raise ValueError("Peak discharge must be greater than zero.")
    if formation_time_hr <= 0 or total_duration_hr <= 0:
        raise ValueError("Formation time and total duration must be greater than zero.")
    if total_duration_hr <= formation_time_hr:
        total_duration_hr = formation_time_hr * 3

    times = np.linspace(0, total_duration_hr, time_steps)
    recession_end = total_duration_hr
    flows = np.where(
        times <= formation_time_hr,
        peak_discharge_m3s * (times / formation_time_hr),
        peak_discharge_m3s * (1 - (times - formation_time_hr) / (recession_end - formation_time_hr)),
    )
    flows = np.maximum(flows, 0)
    return pd.DataFrame({"time_hr": times, "discharge_m3s": flows})


def estimate_peak_from_volume(reservoir_volume_m3: float, formation_time_hr: float) -> float:
    """Estimate peak discharge so a triangular hydrograph releases roughly the reservoir volume."""
    formation_time_seconds = formation_time_hr * 3600
    recession_time_seconds = formation_time_seconds * 2
    return (2 * reservoir_volume_m3) / max(formation_time_seconds + recession_time_seconds, 1e-6)
