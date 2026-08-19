from models.breach_equations import run_breach_method
from models.hydrograph import triangular_hydrograph
from models.lake_volume import estimate_lake_volume


def test_froehlich_1995_returns_positive_values():
    result = run_breach_method("Froehlich 1995", 5_000_000, 25, 22, "Overtopping", 1.4)

    assert result.average_breach_width_m > 0
    assert result.formation_time_hr > 0
    assert result.peak_discharge_m3s is not None
    assert result.peak_discharge_m3s > 0


def test_lake_volume_estimate_has_uncertainty_range():
    estimate = estimate_lake_volume("Huggel et al. 2002", 750_000)

    assert estimate.volume_m3 > 0
    assert estimate.low_volume_m3 < estimate.volume_m3 < estimate.high_volume_m3


def test_triangular_hydrograph_starts_and_ends_at_zero():
    hydrograph = triangular_hydrograph(1000, 1.5, 6, time_steps=20)

    assert hydrograph.iloc[0]["discharge_m3s"] == 0
    assert hydrograph.iloc[-1]["discharge_m3s"] == 0
    assert hydrograph["discharge_m3s"].max() > 900
