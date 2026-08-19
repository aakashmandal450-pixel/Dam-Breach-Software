from dataclasses import dataclass


@dataclass(frozen=True)
class LakeVolumeEstimate:
    method: str
    lake_area_m2: float
    mean_depth_m: float | None
    volume_m3: float
    low_volume_m3: float
    high_volume_m3: float
    note: str


def huggel_2002(lake_area_m2: float) -> LakeVolumeEstimate:
    mean_depth = 0.104 * lake_area_m2**0.42
    volume = 0.104 * lake_area_m2**1.42
    return _with_uncertainty(
        "Huggel et al. 2002",
        lake_area_m2,
        mean_depth,
        volume,
        "General glacial-lake relationship. Good for first estimates, but local bathymetry can vary strongly.",
    )


def evans_1986(lake_area_m2: float) -> LakeVolumeEstimate:
    volume = 0.035 * lake_area_m2**1.5
    return _with_uncertainty(
        "Evans 1986 / Canadian Inland Water Directorate",
        lake_area_m2,
        None,
        volume,
        "Commonly cited ice-dammed lake relationship. Use cautiously for moraine-dammed lakes.",
    )


def oconnor_2001(lake_area_m2: float) -> LakeVolumeEstimate:
    volume = 3.114 * lake_area_m2 + 0.0001685 * lake_area_m2**2
    mean_depth = volume / lake_area_m2
    return _with_uncertainty(
        "O'Connor et al. 2001",
        lake_area_m2,
        mean_depth,
        volume,
        "Developed from moraine-dammed lakes in the Oregon Cascades. May not transfer well to Himalayan lakes.",
    )


def _with_uncertainty(
    method: str,
    lake_area_m2: float,
    mean_depth_m: float | None,
    volume_m3: float,
    note: str,
) -> LakeVolumeEstimate:
    if lake_area_m2 <= 0:
        raise ValueError("Lake area must be greater than zero.")
    return LakeVolumeEstimate(
        method=method,
        lake_area_m2=lake_area_m2,
        mean_depth_m=mean_depth_m,
        volume_m3=volume_m3,
        low_volume_m3=volume_m3 * 0.5,
        high_volume_m3=volume_m3 * 1.75,
        note=note,
    )


def sakai_2012(lake_area_m2: float) -> LakeVolumeEstimate:
    volume = 43.24 * lake_area_m2**1.530
    mean_depth = volume / lake_area_m2
    return _with_uncertainty(
        "Sakai 2012",
        lake_area_m2,
        mean_depth,
        volume,
        "Calibrated for Himalayan/Tibetan glacial lakes. Recommended default for this region.",
    )


def cook_quincey_2015(lake_area_m2: float) -> LakeVolumeEstimate:
    mean_depth = 0.1217 * lake_area_m2**0.4129
    volume = 0.1217 * lake_area_m2**1.4129
    return _with_uncertainty(
        "Cook & Quincey 2015",
        lake_area_m2,
        mean_depth,
        volume,
        "Updated global relationship based on Huggel. Shows high uncertainty for supraglacial lakes or complex bathymetry.",
    )


def estimate_lake_volume(method: str, lake_area_m2: float) -> LakeVolumeEstimate:
    if method == "Sakai 2012":
        return sakai_2012(lake_area_m2)
    if method == "Cook & Quincey 2015":
        return cook_quincey_2015(lake_area_m2)
    if method == "Huggel et al. 2002":
        return huggel_2002(lake_area_m2)
    if method == "Evans 1986":
        return evans_1986(lake_area_m2)
    if method == "O'Connor et al. 2001":
        return oconnor_2001(lake_area_m2)
    raise ValueError(f"Unknown lake volume method: {method}")
