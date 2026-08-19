from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    name: str
    plain_description: str
    typical_triggers: tuple[str, ...]
    recommended_first_methods: tuple[str, ...]
    cautions: tuple[str, ...]


SCENARIOS = {
    "Earthfill / embankment dam": Scenario(
        name="Earthfill / embankment dam",
        plain_description="A constructed dam made mainly from compacted soil or rockfill.",
        typical_triggers=("Overtopping", "Piping / internal erosion", "Slope failure"),
        recommended_first_methods=("Froehlich 1995", "Froehlich 2008", "MacDonald & Langridge-Monopolis 1984"),
        cautions=("Empirical equations are approximate and should be compared side by side.",),
    ),
    "Moraine-dammed glacial lake": Scenario(
        name="Moraine-dammed glacial lake",
        plain_description="A glacial lake held back by loose moraine material, sometimes with buried ice.",
        typical_triggers=("Avalanche / icefall impulse wave", "Overtopping", "Ice-core degradation", "Piping"),
        recommended_first_methods=("Lake volume-area estimate", "Froehlich 1995 as a rough comparison"),
        cautions=(
            "Moraine dams are not the same as engineered earth dams.",
            "Show uncertainty clearly when bathymetry or material data are missing.",
        ),
    ),
    "Landslide dam": Scenario(
        name="Landslide dam",
        plain_description="A natural dam formed when landslide debris blocks a valley or river.",
        typical_triggers=("Overtopping", "Seepage", "Progressive erosion"),
        recommended_first_methods=("Simple overtopping hydrograph", "Scenario comparison"),
        cautions=("Material is usually very heterogeneous, so parameters are uncertain.",),
    ),
    "Tailings dam": Scenario(
        name="Tailings dam",
        plain_description="A dam retaining mine tailings, often requiring special geotechnical treatment.",
        typical_triggers=("Static liquefaction", "Overtopping", "Foundation failure", "Piping"),
        recommended_first_methods=("Conservative scenario comparison",),
        cautions=("Do not treat tailings like ordinary reservoir water without specialist review.",),
    ),
}
