from io import StringIO
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.diagrams import dam_cross_section_figure, glof_trigger_figure
from models.breach_equations import run_breach_method
from models.hydrograph import estimate_peak_from_volume, triangular_hydrograph
from models.lake_volume import estimate_lake_volume
from models.scenarios import SCENARIOS


st.set_page_config(page_title="Dam Breach Studio", layout="wide")

st.title("Dam Breach Studio")
st.caption("A transparent prototype for breach-parameter, GLOF, and hydrograph analysis.")

with st.sidebar:
    st.header("Project")
    project_name = st.text_input("Project name", "Example breach study")
    scenario_name = st.selectbox("Scenario type", list(SCENARIOS.keys()))
    failure_mode = st.selectbox("Failure mode", ["Overtopping", "Piping / internal erosion", "Unknown"])

scenario = SCENARIOS[scenario_name]

overview_tab, breach_tab, glof_tab, results_tab, library_tab = st.tabs(
    ["Overview", "Breach Model", "GLOF / Lake Volume", "Results", "Equation Library"]
)

with overview_tab:
    left, right = st.columns([1.1, 1])
    with left:
        st.subheader(project_name)
        st.write(scenario.plain_description)
        st.markdown("**Typical triggers**")
        st.write(", ".join(scenario.typical_triggers))
        st.markdown("**Suggested first methods**")
        st.write(", ".join(scenario.recommended_first_methods))
        for caution in scenario.cautions:
            st.warning(caution)
    with right:
        if scenario_name == "Moraine-dammed glacial lake":
            st.plotly_chart(glof_trigger_figure(), width="stretch", key="overview_glof_trigger_chart")
        else:
            st.plotly_chart(
                dam_cross_section_figure(28, 35, 30),
                width="stretch",
                key="overview_dam_cross_section_chart",
            )

with breach_tab:
    st.subheader("Breach Parameter Calculator")
    st.write("Use this page to estimate breach width, breach formation time, and peak discharge.")

    col1, col2, col3 = st.columns(3)
    with col1:
        reservoir_volume_m3 = st.number_input("Reservoir volume at failure (m3)", min_value=1.0, value=5_000_000.0)
        breach_height_m = st.number_input("Final breach height (m)", min_value=0.1, value=25.0)
    with col2:
        water_height_above_breach_m = st.number_input("Water height above breach bottom (m)", min_value=0.1, value=22.0)
        side_slope_h_to_v = st.number_input("Side slope H:V", min_value=0.1, value=1.4)
    with col3:
        method = st.selectbox(
            "Breach method",
            ["Froehlich 1995", "Froehlich 2008", "MacDonald & Langridge-Monopolis 1984"],
        )
        duration_factor = st.slider("Hydrograph duration factor", 2.0, 8.0, 4.0, 0.5)

    st.plotly_chart(
        dam_cross_section_figure(water_height_above_breach_m, breach_height_m, breach_height_m),
        width="stretch",
        key="breach_cross_section_chart",
    )

    try:
        breach_result = run_breach_method(
            method,
            reservoir_volume_m3,
            breach_height_m,
            water_height_above_breach_m,
            failure_mode,
            side_slope_h_to_v,
        )
        peak = breach_result.peak_discharge_m3s or estimate_peak_from_volume(
            reservoir_volume_m3, breach_result.formation_time_hr
        )
        hydrograph = triangular_hydrograph(
            peak,
            breach_result.formation_time_hr,
            breach_result.formation_time_hr * duration_factor,
        )
        st.session_state["breach_result"] = breach_result
        st.session_state["hydrograph"] = hydrograph
        st.session_state["peak"] = peak

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Average breach width", f"{breach_result.average_breach_width_m:,.1f} m")
        m2.metric("Formation time", f"{breach_result.formation_time_hr:,.2f} hr")
        m3.metric("Side slope", f"{breach_result.side_slope_h_to_v:,.1f} H:1V")
        m4.metric("Peak discharge", f"{peak:,.0f} m3/s")

        for note in breach_result.notes:
            st.info(note)
    except ValueError as exc:
        st.error(str(exc))

with glof_tab:
    st.subheader("Lake Volume Estimator")
    st.write("Use this when bathymetry is missing and only lake surface area is available.")

    lake_col, trigger_col = st.columns([1, 1])
    with lake_col:
        lake_area_m2 = st.number_input("Lake surface area (m2)", min_value=1.0, value=750_000.0)
        volume_method = st.selectbox(
            "Volume-area method",
            [
                "Sakai 2012",
                "Cook & Quincey 2015",
                "Huggel et al. 2002",
                "Evans 1986",
                "O'Connor et al. 2001",
            ],
        )
        estimate = estimate_lake_volume(volume_method, lake_area_m2)
        st.metric("Estimated volume", f"{estimate.volume_m3:,.0f} m3")
        if estimate.mean_depth_m:
            st.metric("Estimated mean depth", f"{estimate.mean_depth_m:,.1f} m")
        st.write(f"Uncertainty display range: {estimate.low_volume_m3:,.0f} to {estimate.high_volume_m3:,.0f} m3")
        st.warning(estimate.note)
    with trigger_col:
        st.plotly_chart(glof_trigger_figure(), width="stretch", key="glof_trigger_chart")
        st.checkbox("Avalanche / icefall trigger possible")
        st.checkbox("Buried ice core suspected")
        st.checkbox("Low freeboard observed")
        st.checkbox("Piping or seepage observed")

with results_tab:
    st.subheader("Hydrograph Results")
    hydrograph = st.session_state.get("hydrograph")
    breach_result = st.session_state.get("breach_result")
    peak = st.session_state.get("peak")

    if hydrograph is None or breach_result is None:
        st.info("Run the breach calculator first.")
    else:
        fig = px.line(hydrograph, x="time_hr", y="discharge_m3s", markers=False)
        fig.update_layout(
            xaxis_title="Time (hr)",
            yaxis_title="Discharge (m3/s)",
            height=420,
            margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(fig, width="stretch", key="results_hydrograph_chart")

        summary = pd.DataFrame(
            [
                {
                    "project": project_name,
                    "scenario": scenario_name,
                    "failure_mode": failure_mode,
                    "method": breach_result.method,
                    "average_breach_width_m": breach_result.average_breach_width_m,
                    "formation_time_hr": breach_result.formation_time_hr,
                    "side_slope_h_to_v": breach_result.side_slope_h_to_v,
                    "peak_discharge_m3s": peak,
                }
            ]
        )
        st.dataframe(summary, width="stretch", key="results_summary_table")

        csv = StringIO()
        hydrograph.to_csv(csv, index=False)
        st.download_button(
            "Download hydrograph CSV",
            data=csv.getvalue(),
            file_name=f"{project_name.lower().replace(' ', '_')}_hydrograph.csv",
            mime="text/csv",
            key="download_hydrograph_csv",
        )

with library_tab:
    st.subheader("Equation Library")
    st.write("This section explains methods in simple language. It will grow as more models are added.")

    with st.expander("Froehlich 1995"):
        st.write(
            "Estimates average breach width, breach formation time, and peak discharge from reservoir volume, "
            "breach height, water height, and failure mode. It is useful for quick embankment-dam estimates."
        )
        st.code("B_avg = 0.1803 * K0 * Vw^0.32 * hb^0.19\n"
                "tf = 0.00254 * Vw^0.53 * hb^-0.90\n"
                "Qp = 0.607 * Vw^0.295 * hw^1.24")

    with st.expander("Froehlich 2008"):
        st.write(
            "An updated empirical method for breach width and formation time. In this prototype, peak discharge "
            "is estimated from released volume and the generated hydrograph shape."
        )
        st.code("B_avg = 0.27 * K0 * Vw^0.32 * hb^0.04\n"
                "tf_seconds = 63.2 * sqrt(Vw / (g * hb^2))")

    with st.expander("Lake volume-area methods"):
        st.write(
            "These methods estimate lake volume from mapped lake area. They are useful when bathymetry is missing, "
            "but uncertainty can be large because real lake basins have different shapes."
        )
        st.code("Sakai (Himalaya): V = 43.24 * A^1.530\n"
                "Cook & Quincey (Global): V = 0.1217 * A^1.4129\n"
                "Huggel: V = 0.104 * A^1.42\n"
                "Evans: V = 0.035 * A^1.5\n"
                "O'Connor (Cascades): V = 3.114 * A + 0.0001685 * A^2")
