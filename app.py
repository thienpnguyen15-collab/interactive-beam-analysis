import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(page_title="Professional Beam Analysis (2D)", page_icon="🏗️", layout="wide")

# Store settings and additional loads between Streamlit reruns.
if "moment_loads" not in st.session_state:
    st.session_state.moment_loads = []

if "unit_system" not in st.session_state:
    st.session_state.unit_system = "Imperial"

if "display_length_unit" not in st.session_state:
    st.session_state.display_length_unit = "Feet (ft)"

if "display_force_unit" not in st.session_state:
    st.session_state.display_force_unit = "kips (1 kip = 1,000 lbs)"

if "display_moment_unit" not in st.session_state:
    st.session_state.display_moment_unit = "kip-ft"

if "display_stress_unit" not in st.session_state:
    st.session_state.display_stress_unit = "ksi"

if "custom_Iz" not in st.session_state:
    st.session_state.custom_Iz = 2730.0

if "custom_E" not in st.session_state:
    st.session_state.custom_E = 29000.0

if "selected_section_name" not in st.session_state:
    st.session_state.selected_section_name = "Rectangular"

if "custom_S" not in st.session_state:
    st.session_state.custom_S = 341.25

if "custom_A_web" not in st.session_state:
    st.session_state.custom_A_web = 128.0

if "custom_material_name" not in st.session_state:
    st.session_state.custom_material_name = "A36 Steel"

if "custom_yield_strength" not in st.session_state:
    st.session_state.custom_yield_strength = 36.0

if "custom_factor_of_safety" not in st.session_state:
    st.session_state.custom_factor_of_safety = 1.5


# ================= SETTINGS DIALOG =================

@st.dialog("⚙️ Settings", width="large")
def open_settings():
    st.subheader("Unit System")

    imperial_tab, metric_tab = st.tabs(["Imperial", "Metric"])

    with imperial_tab:
        st.caption("Select imperial display units.")

        imperial_length = st.selectbox(
            "Length",
            ["Inches (in)", "Feet (ft)"],
            index=(
                0
                if st.session_state.display_length_unit == "Inches (in)"
                else 1
            ),
            key="imperial_length_setting"
        )

        imperial_force = st.selectbox(
            "Force",
            ["Pounds (lbs)", "kips (1 kip = 1,000 lbs)"],
            index=(
                0
                if st.session_state.display_force_unit == "Pounds (lbs)"
                else 1
            ),
            key="imperial_force_setting"
        )

        imperial_moment = st.selectbox(
            "Moment",
            ["kip-in", "kip-ft"],
            index=(
                0
                if st.session_state.display_moment_unit == "kip-in"
                else 1
            ),
            key="imperial_moment_setting"
        )

        imperial_stress = st.selectbox(
            "Stress",
            ["psi", "ksi"],
            index=(
                0
                if st.session_state.display_stress_unit == "psi"
                else 1
            ),
            key="imperial_stress_setting"
        )

        if st.button(
            "Use Imperial Units",
            type="primary",
            use_container_width=True,
            key="use_imperial_units"
        ):
            st.session_state.unit_system = "Imperial"
            st.session_state.display_length_unit = imperial_length
            st.session_state.display_force_unit = imperial_force
            st.session_state.display_moment_unit = imperial_moment
            st.session_state.display_stress_unit = imperial_stress
            st.success("Imperial units selected.")

    with metric_tab:
        st.caption("Select metric display units.")

        metric_length = st.selectbox(
            "Length",
            ["Millimeters (mm)", "Meters (m)"],
            index=1,
            key="metric_length_setting"
        )

        metric_force = st.selectbox(
            "Force",
            ["Newtons (N)", "Kilonewtons (kN)"],
            index=1,
            key="metric_force_setting"
        )

        metric_moment = st.selectbox(
            "Moment",
            ["N-m", "kN-m"],
            index=1,
            key="metric_moment_setting"
        )

        metric_stress = st.selectbox(
            "Stress",
            ["Pa", "MPa"],
            index=1,
            key="metric_stress_setting"
        )

        if st.button(
            "Use Metric Units",
            type="primary",
            use_container_width=True,
            key="use_metric_units"
        ):
            st.session_state.unit_system = "Metric"
            st.session_state.display_length_unit = metric_length
            st.session_state.display_force_unit = metric_force
            st.session_state.display_moment_unit = metric_moment
            st.session_state.display_stress_unit = metric_stress
            st.success("Metric units selected.")

    st.markdown("---")
    st.write(f"**Active system:** {st.session_state.unit_system}")
    st.write(f"**Length:** {st.session_state.display_length_unit}")
    st.write(f"**Force:** {st.session_state.display_force_unit}")
    st.write(f"**Moment:** {st.session_state.display_moment_unit}")
    st.write(f"**Stress:** {st.session_state.display_stress_unit}")


# ================= SECTION BUILDER DIALOG =================

@st.dialog("Create Custom Section", width="large")
def open_section_builder():
    setup_tab, advanced_tab, library_tab = st.tabs(
        ["Shape & Material", "Advanced Properties", "American Library"]
    )

    # =====================================================
    # SHAPE, DIMENSIONS, AND MATERIAL
    # =====================================================
    with setup_tab:
        st.subheader("Section Shape")

        shape_choice = st.selectbox(
            "Select Shape",
            [
                "Rectangular (Solid)",
                "Hollow Box / Tube",
                "I-Shape / Wide Flange",
                "Solid Circle",
                "Round Tube"
            ],
            index=0
        )

        st.markdown("### Dimensions")

        if shape_choice == "Rectangular (Solid)":
            dim_col1, dim_col2 = st.columns(2)

            with dim_col1:
                b = st.number_input(
                    "Width b (in)",
                    min_value=0.1,
                    value=8.0,
                    step=0.5,
                    key="builder_rect_b"
                )

            with dim_col2:
                h = st.number_input(
                    "Height h (in)",
                    min_value=0.1,
                    value=16.0,
                    step=0.5,
                    key="builder_rect_h"
                )

            calculated_I = b * h**3 / 12.0
            calculated_S = calculated_I / (h / 2.0)
            calculated_A = b * h

        elif shape_choice == "Hollow Box / Tube":
            dim_col1, dim_col2, dim_col3 = st.columns(3)

            with dim_col1:
                b = st.number_input(
                    "Outer Width b (in)",
                    min_value=0.2,
                    value=8.0,
                    step=0.5,
                    key="builder_box_b"
                )

            with dim_col2:
                h = st.number_input(
                    "Outer Height h (in)",
                    min_value=0.2,
                    value=16.0,
                    step=0.5,
                    key="builder_box_h"
                )

            with dim_col3:
                t = st.number_input(
                    "Wall Thickness t (in)",
                    min_value=0.05,
                    value=0.5,
                    step=0.05,
                    key="builder_box_t"
                )

            b_inner = max(0.01, b - 2.0 * t)
            h_inner = max(0.01, h - 2.0 * t)

            calculated_I = (
                b * h**3
                - b_inner * h_inner**3
            ) / 12.0

            calculated_S = calculated_I / (h / 2.0)
            calculated_A = b * h - b_inner * h_inner

        elif shape_choice == "I-Shape / Wide Flange":
            dim_col1, dim_col2 = st.columns(2)

            with dim_col1:
                b = st.number_input(
                    "Flange Width b (in)",
                    min_value=0.2,
                    value=8.0,
                    step=0.5,
                    key="builder_i_b"
                )

                tw = st.number_input(
                    "Web Thickness tw (in)",
                    min_value=0.05,
                    value=0.4,
                    step=0.05,
                    key="builder_i_tw"
                )

            with dim_col2:
                h = st.number_input(
                    "Total Height h (in)",
                    min_value=0.2,
                    value=16.0,
                    step=0.5,
                    key="builder_i_h"
                )

                tf = st.number_input(
                    "Flange Thickness tf (in)",
                    min_value=0.05,
                    value=0.6,
                    step=0.05,
                    key="builder_i_tf"
                )

            h_web = max(0.01, h - 2.0 * tf)

            calculated_I = (
                tw * h_web**3 / 12.0
                + 2.0 * (
                    b * tf**3 / 12.0
                    + b * tf * ((h - tf) / 2.0) ** 2
                )
            )

            calculated_S = calculated_I / (h / 2.0)
            calculated_A = 2.0 * b * tf + tw * h_web

        elif shape_choice == "Solid Circle":
            diameter = st.number_input(
                "Diameter d (in)",
                min_value=0.1,
                value=8.0,
                step=0.5,
                key="builder_circle_d"
            )

            calculated_I = np.pi * diameter**4 / 64.0
            calculated_S = calculated_I / (diameter / 2.0)
            calculated_A = np.pi * diameter**2 / 4.0

        else:
            dim_col1, dim_col2 = st.columns(2)

            with dim_col1:
                diameter = st.number_input(
                    "Outer Diameter D (in)",
                    min_value=0.2,
                    value=8.0,
                    step=0.5,
                    key="builder_tube_d"
                )

            with dim_col2:
                thickness = st.number_input(
                    "Wall Thickness t (in)",
                    min_value=0.05,
                    value=0.5,
                    step=0.05,
                    key="builder_tube_t"
                )

            inner_diameter = max(0.01, diameter - 2.0 * thickness)

            calculated_I = (
                np.pi
                * (diameter**4 - inner_diameter**4)
                / 64.0
            )

            calculated_S = calculated_I / (diameter / 2.0)

            calculated_A = (
                np.pi
                * (diameter**2 - inner_diameter**2)
                / 4.0
            )

        # Preview and calculated values
        preview_col, values_col = st.columns([1, 1])

        with preview_col:
            st.markdown("### Section Preview")

            preview_icons = {
                "Rectangular (Solid)": "▰",
                "Hollow Box / Tube": "▢",
                "I-Shape / Wide Flange": "工",
                "Solid Circle": "●",
                "Round Tube": "◉",
            }

            st.markdown(
                f"""
                <div style="
                    border:1px solid #d7dde5;
                    border-radius:8px;
                    min-height:190px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    background:#ffffff;
                    font-size:92px;
                ">
                    {preview_icons[shape_choice]}
                </div>
                """,
                unsafe_allow_html=True
            )

        with values_col:
            st.markdown("### Calculated Properties")
            st.metric("Moment of Inertia, Iz", f"{calculated_I:,.2f} in⁴")
            st.metric("Section Modulus, S", f"{calculated_S:,.2f} in³")
            st.metric("Cross-Section Area", f"{calculated_A:,.2f} in²")

        st.markdown("---")
        st.subheader("Material")

        material_category = st.selectbox(
            "Material Category",
            ["Steel & Metals", "Wood & Timber", "Custom"],
            key="builder_material_category"
        )

        if material_category == "Steel & Metals":
            material_choice = st.selectbox(
                "Select Material",
                [
                    "A36 Steel",
                    "A992 Steel",
                    "Aluminum 6061-T6"
                ],
                key="builder_metal_choice"
            )

            if material_choice == "A36 Steel":
                material_name = "A36 Steel"
                material_strength = 36.0
                material_E = 29000.0

            elif material_choice == "A992 Steel":
                material_name = "A992 Steel"
                material_strength = 50.0
                material_E = 29000.0

            else:
                material_name = "Aluminum 6061-T6"
                material_strength = 35.0
                material_E = 10000.0

        elif material_category == "Wood & Timber":
            material_choice = st.selectbox(
                "Select Wood",
                [
                    "Douglas Fir-Larch No.1",
                    "Southern Pine No.1",
                    "Hem-Fir No.1/No.2"
                ],
                key="builder_wood_choice"
            )

            if material_choice == "Douglas Fir-Larch No.1":
                material_name = material_choice
                material_strength = 1.5
                material_E = 1600.0

            elif material_choice == "Southern Pine No.1":
                material_name = material_choice
                material_strength = 1.7
                material_E = 1800.0

            else:
                material_name = material_choice
                material_strength = 1.2
                material_E = 1400.0

        else:
            material_name = st.text_input(
                "Material Name",
                value=st.session_state.custom_material_name,
                key="builder_custom_material_name"
            )

            material_strength = st.number_input(
                "Yield / Allowable Strength (ksi)",
                min_value=0.01,
                value=float(st.session_state.custom_yield_strength),
                step=1.0,
                key="builder_custom_strength"
            )

            material_E = st.number_input(
                "Young's Modulus E (ksi)",
                min_value=1.0,
                value=float(st.session_state.custom_E),
                step=100.0,
                key="builder_custom_E"
            )

        material_fos = st.number_input(
            "Factor of Safety",
            min_value=0.1,
            value=float(st.session_state.custom_factor_of_safety),
            step=0.1,
            key="builder_material_fos"
        )

        if st.button(
            "💾 Save Section",
            type="primary",
            use_container_width=True,
            key="save_complete_section"
        ):
            st.session_state.selected_section_name = shape_choice
            st.session_state.custom_Iz = float(calculated_I)
            st.session_state.custom_S = float(calculated_S)
            st.session_state.custom_A_web = float(calculated_A)
            st.session_state.custom_material_name = material_name
            st.session_state.custom_yield_strength = float(material_strength)
            st.session_state.custom_E = float(material_E)
            st.session_state.custom_factor_of_safety = float(material_fos)

            st.success(
                f"{shape_choice} with {material_name} was saved."
            )

    # =====================================================
    # ADVANCED PROPERTIES
    # =====================================================
    with advanced_tab:
        st.subheader("Saved Section and Material Properties")

        st.info(
            f"Current saved section: "
            f"{st.session_state.selected_section_name}"
        )

        st.session_state.custom_Iz = st.number_input(
            "Moment of Inertia, Iz (in⁴)",
            min_value=0.01,
            value=float(st.session_state.custom_Iz),
            step=10.0,
            key="advanced_Iz"
        )

        st.session_state.custom_S = st.number_input(
            "Section Modulus, S (in³)",
            min_value=0.01,
            value=float(st.session_state.custom_S),
            step=1.0,
            key="advanced_S"
        )

        st.session_state.custom_A_web = st.number_input(
            "Effective Shear Area (in²)",
            min_value=0.01,
            value=float(st.session_state.custom_A_web),
            step=1.0,
            key="advanced_A"
        )

        st.session_state.custom_E = st.number_input(
            "Young's Modulus, E (ksi)",
            min_value=1.0,
            value=float(st.session_state.custom_E),
            step=100.0,
            key="advanced_E"
        )

        st.session_state.custom_material_name = st.text_input(
            "Material Name",
            value=st.session_state.custom_material_name,
            key="advanced_material"
        )

        st.session_state.custom_yield_strength = st.number_input(
            "Yield / Allowable Strength (ksi)",
            min_value=0.01,
            value=float(st.session_state.custom_yield_strength),
            step=1.0,
            key="advanced_strength"
        )

        st.session_state.custom_factor_of_safety = st.number_input(
            "Factor of Safety",
            min_value=0.1,
            value=float(st.session_state.custom_factor_of_safety),
            step=0.1,
            key="advanced_fos"
        )

        st.success(
            "Changes in this tab are saved automatically."
        )

    # =====================================================
    # AMERICAN LIBRARY PLACEHOLDER
    # =====================================================
    with library_tab:
        st.subheader("American Section Library")

        st.selectbox(
            "Section Family",
            ["W-Shape", "C-Channel", "L-Angle", "HSS"],
            key="builder_library_family"
        )

        st.text_input(
            "Search Section",
            placeholder="Example: W12x26",
            key="builder_library_search"
        )

        st.info(
            "The complete AISC section database is not included "
            "in this educational version."
        )


# ================= MAIN HEADER =================

st.title("🏗️ Interactive Beam Analysis & Reaction Forces")

# SIDEBAR INPUTS (IMPERIAL) 

with st.sidebar:
    st.header("⚙️ Beam & Load Parameters")

    if st.button(
        "⚙️ Settings",
        use_container_width=True,
        key="sidebar_settings_button"
    ):
        open_settings()

    st.markdown("---")

    st.markdown("### Active Units")
    st.write(f"System: **{st.session_state.unit_system}**")
    st.write(f"Length: **{st.session_state.display_length_unit}**")
    st.write(f"Force: **{st.session_state.display_force_unit}**")

    # Internal calculations remain in imperial units.
    if st.session_state.unit_system == "Metric":
        L_m = st.number_input(
            "Beam Length L (m)",
            min_value=0.01,
            value=4.8768,
            step=0.1
        )
        L = L_m * 39.37007874
        len_unit = "Meters (m)"
        force_unit = "Kilonewtons (kN)"
    else:
        if st.session_state.display_length_unit == "Feet (ft)":
            L_ft = st.number_input(
                "Beam Length L (ft)",
                min_value=0.1,
                value=16.0,
                step=1.0
            )
            L = L_ft * 12.0
            len_unit = "Feet (ft)"
        else:
            L = st.number_input(
                "Beam Length L (in)",
                min_value=1.0,
                value=192.0,
                step=12.0
            )
            len_unit = "Inches (in)"

        force_unit = st.session_state.display_force_unit

    st.subheader("Support Configurations (Boundary Conditions)")
    support_options = ["Pinned (Hinged)", "Roller", "Fixed (Ngàm)", "Free (Tự do)"]

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        support_A = st.selectbox("Support A (Left)", support_options, index=0)
    with col_s2:
        support_B = st.selectbox("Support B (Right)", support_options, index=1)

    st.subheader("1. Point Loads")

    n_loads = st.number_input(
        "Number of Point Loads",
        min_value=0,
        max_value=8,
        value=1
    )

    # P stores the signed vertical component in kips:
    # positive = downward, negative = upward.
    P = []
    x_load = []
    point_load_meta = []

    load_case_options = [
        "Dead",
        "Live",
        "Wind",
        "Earthquake",
        "Pedestrian",
        "Vehicle",
        "Other"
    ]

    for i in range(int(n_loads)):
        with st.expander(f"Load P{i + 1}", expanded=True):
            load_case = st.selectbox(
                "Load Case",
                load_case_options,
                index=1,
                key=f"load_case_{i}"
            )

            direction_display = st.radio(
                "Direction",
                ["⬇ Down", "⬆ Up", "↙ Angled"],
                horizontal=True,
                key=f"load_direction_{i}"
            )

            load_direction = {
                "⬇ Down": "Down",
                "⬆ Up": "Up",
                "↙ Angled": "Angled",
            }[direction_display]

            if "Pounds" in force_unit:
                input_magnitude_lb = st.number_input(
                    f"Magnitude P{i + 1} (lbs)",
                    min_value=1.0,
                    value=5000.0,
                    step=100.0,
                    key=f"p_{i}"
                )
                input_magnitude_kip = input_magnitude_lb / 1000.0
            elif st.session_state.unit_system == "Metric":
                input_magnitude_kn = st.number_input(
                    f"Magnitude P{i + 1} (kN)",
                    min_value=0.01,
                    value=22.24,
                    step=1.0,
                    key=f"p_{i}"
                )
                input_magnitude_kip = input_magnitude_kn / 4.448221615
            else:
                input_magnitude_kip = st.number_input(
                    f"Magnitude P{i + 1} (kips)",
                    min_value=0.01,
                    value=5.0,
                    step=0.5,
                    key=f"p_{i}"
                )

            # Engineering angle convention:
            # theta is measured counterclockwise from the positive beam axis (+x).
            # 0° = right, 90° = up, 180° = left, 270° = down.
            if load_direction == "Down":
                angle_deg = 270.0
            elif load_direction == "Up":
                angle_deg = 90.0
            else:
                angle_deg = st.number_input(
                    "Load Angle θ (degrees)",
                    min_value=0.0,
                    max_value=360.0,
                    value=315.0,
                    step=1.0,
                    key=f"load_angle_{i}",
                    help=(
                        "Angle is measured counterclockwise from the beam axis "
                        "pointing to the right. Examples: 0° right, 90° up, "
                        "180° left, 270° down."
                    )
                )

                st.caption(
                    "Angle convention: 0° → right, 90° ↑ up, "
                    "180° ← left, 270° ↓ down."
                )

            if "Feet" in len_unit:
                x_val_ft = st.number_input(
                    f"Position x{i + 1} from A (ft)",
                    min_value=0.0,
                    max_value=float(L / 12.0),
                    value=min(4.0, float(L / 12.0)),
                    key=f"x_{i}"
                )
                x_val = x_val_ft * 12.0
            elif "Meters" in len_unit:
                x_val_m = st.number_input(
                    f"Position x{i + 1} from A (m)",
                    min_value=0.0,
                    max_value=float(L / 39.37007874),
                    value=min(1.2, float(L / 39.37007874)),
                    key=f"x_{i}"
                )
                x_val = x_val_m * 39.37007874
            else:
                x_val = st.number_input(
                    f"Position x{i + 1} from A (in)",
                    min_value=0.0,
                    max_value=float(L),
                    value=min(48.0, float(L)),
                    key=f"x_{i}"
                )

            angle_rad = np.deg2rad(angle_deg)

            # Standard Cartesian components.
            horizontal_component = (
                input_magnitude_kip * np.cos(angle_rad)
            )
            vertical_component_cartesian = (
                input_magnitude_kip * np.sin(angle_rad)
            )

            # Existing beam calculations use positive values for downward loads.
            vertical_component = -vertical_component_cartesian

            if load_direction == "Angled":
                horizontal_word = (
                    "right"
                    if horizontal_component >= 0
                    else "left"
                )

                vertical_word = (
                    "up"
                    if vertical_component_cartesian >= 0
                    else "down"
                )

                st.caption(
                    f"Fx = {abs(horizontal_component):.3f} kip "
                    f"toward {horizontal_word}; "
                    f"Fy = {abs(vertical_component_cartesian):.3f} kip "
                    f"toward {vertical_word}. "
                    "SFD, BMD, deflection, and bending checks use Fy."
                )

            P.append(vertical_component)
            x_load.append(x_val)

            point_load_meta.append(
                {
                    "case": load_case,
                    "direction": load_direction,
                    "angle_deg": angle_deg,
                    "input_magnitude_kip": input_magnitude_kip,
                    "vertical_component_kip": vertical_component,
                    "horizontal_component_kip": horizontal_component,
                }
            )

    # ======================================================
    # CUSTOM LOAD
    # ======================================================
    st.subheader("➕ Custom Load")

    enable_walker = st.toggle(
        "Enable Custom Load",
        value=True
    )

    if enable_walker:
        moving_case = st.selectbox(
            "Load Case",
            [
                "Live",
                "Pedestrian",
                "Vehicle",
                "Wind",
                "Earthquake",
                "Tension / Pull",
                "Compression / Push",
                "Other"
            ],
            index=1
        )

        load_type = st.selectbox(
            "Load Type",
            [
                "🚶 Pedestrian (~180 lbs)",
                "🚲 Bicycle + Rider (~250 lbs)",
                "🛒 Cart / Hand Truck (~500 lbs)",
                "🚙 Small Vehicle Wheel Load (~2,000 lbs)",
                "🚜 Forklift / Heavy Cart (~3,000 lbs)",
                "🪢 Tension / Pulling Force",
                "🧱 Compression / Pushing Force",
                "🌬️ Wind Force",
                "🌎 Earthquake Force",
                "⚙️ Fully Custom Load"
            ]
        )

        if "Pedestrian" in load_type:
            default_wt_lb = 180.0
            icon_str = "🚶"
        elif "Bicycle" in load_type:
            default_wt_lb = 250.0
            icon_str = "🚲"
        elif "Cart / Hand" in load_type:
            default_wt_lb = 500.0
            icon_str = "🛒"
        elif "Small Vehicle" in load_type:
            default_wt_lb = 2000.0
            icon_str = "🚙"
        elif "Forklift" in load_type:
            default_wt_lb = 3000.0
            icon_str = "🚜"
        elif "Tension" in load_type:
            default_wt_lb = 1000.0
            icon_str = "🪢"
            moving_case = "Tension / Pull"
        elif "Compression" in load_type:
            default_wt_lb = 1000.0
            icon_str = "🧱"
            moving_case = "Compression / Push"
        elif "Wind" in load_type:
            default_wt_lb = 500.0
            icon_str = "🌬️"
            moving_case = "Wind"
        elif "Earthquake" in load_type:
            default_wt_lb = 1000.0
            icon_str = "🌎"
            moving_case = "Earthquake"
        else:
            default_wt_lb = 1000.0
            icon_str = "⚙️"

        st.markdown("**Direction:**")

        moving_direction_display = st.radio(
            "Custom Load Direction",
            ["⬇ Down", "⬆ Up", "↙ Angled"],
            horizontal=True,
            label_visibility="collapsed"
        )

        moving_direction = {
            "⬇ Down": "Down",
            "⬆ Up": "Up",
            "↙ Angled": "Angled",
        }[moving_direction_display]

        if "Pounds" in force_unit:
            moving_input_lb = st.number_input(
                "Load Magnitude (lbs)",
                min_value=1.0,
                value=default_wt_lb,
                step=50.0
            )
            moving_input_kip = moving_input_lb / 1000.0
        elif st.session_state.unit_system == "Metric":
            moving_input_kn = st.number_input(
                "Load Magnitude (kN)",
                min_value=0.01,
                value=default_wt_lb * 0.004448221615,
                step=0.5
            )
            moving_input_kip = moving_input_kn / 4.448221615
        else:
            moving_input_kip = st.number_input(
                "Load Magnitude (kips)",
                min_value=0.001,
                value=default_wt_lb / 1000.0,
                step=0.1
            )

        # Engineering angle convention:
        # theta is measured counterclockwise from the positive beam axis (+x).
        if moving_direction == "Down":
            moving_angle_deg = 270.0
        elif moving_direction == "Up":
            moving_angle_deg = 90.0
        else:
            moving_angle_deg = st.number_input(
                "Load Angle θ (degrees)",
                min_value=0.0,
                max_value=360.0,
                value=315.0,
                step=1.0,
                key="custom_load_angle",
                help=(
                    "Angle is measured counterclockwise from the beam axis "
                    "pointing to the right. Examples: 0° right, 90° up, "
                    "180° left, 270° down."
                )
            )

            st.caption(
                "Angle convention: 0° → right, 90° ↑ up, "
                "180° ← left, 270° ↓ down."
            )

        if "Feet" in len_unit:
            walker_pos_ft = st.slider(
                "Load Position (ft)",
                min_value=0.0,
                max_value=float(L / 12.0),
                value=float(L / 24.0),
                step=0.5
            )
            walker_pos = walker_pos_ft * 12.0
        elif "Meters" in len_unit:
            walker_pos_m = st.slider(
                "Load Position (m)",
                min_value=0.0,
                max_value=float(L / 39.37007874),
                value=float(L / 78.74015748),
                step=0.1
            )
            walker_pos = walker_pos_m * 39.37007874
        else:
            walker_pos = st.slider(
                "Load Position (in)",
                min_value=0.0,
                max_value=float(L),
                value=float(L / 2.0),
                step=1.0
            )

        moving_angle_rad = np.deg2rad(moving_angle_deg)

        moving_horizontal_component = (
            moving_input_kip * np.cos(moving_angle_rad)
        )

        moving_vertical_cartesian = (
            moving_input_kip * np.sin(moving_angle_rad)
        )

        # Existing beam calculations use positive values for downward loads.
        walker_load = -moving_vertical_cartesian

        if moving_direction == "Angled":
            horizontal_word = (
                "right"
                if moving_horizontal_component >= 0
                else "left"
            )

            vertical_word = (
                "up"
                if moving_vertical_cartesian >= 0
                else "down"
            )

            st.caption(
                f"Fx = {abs(moving_horizontal_component):.3f} kip "
                f"toward {horizontal_word}; "
                f"Fy = {abs(moving_vertical_cartesian):.3f} kip "
                f"toward {vertical_word}."
            )

        st.info(
            "SFD, BMD, deflection, and bending checks use the vertical "
            "component. The horizontal component is displayed for future "
            "axial-force analysis."
        )

    else:
        walker_load = 0.0
        walker_pos = 0.0
        icon_str = "⚙️"
        moving_case = "None"
        moving_direction = "Down"
        moving_angle_deg = 90.0
        moving_horizontal_component = 0.0

    st.subheader("2. Applied Moments")

    enable_moment = st.toggle(
        "Enable Applied Moment",
        value=False
    )

    if enable_moment:
        moment_direction = st.radio(
            "Moment Direction",
            ["Counterclockwise", "Clockwise"],
            horizontal=True
        )

        if "Feet" in len_unit:
            moment_position_ft = st.number_input(
                "Moment Position from A (ft)",
                min_value=0.0,
                max_value=float(L / 12.0),
                value=float(L / 24.0),
                step=0.5
            )
            moment_position = moment_position_ft * 12.0
        else:
            moment_position = st.number_input(
                "Moment Position from A (in)",
                min_value=0.0,
                max_value=float(L),
                value=float(L / 2.0),
                step=1.0
            )

        if st.session_state.display_moment_unit == "kip-ft":
            moment_magnitude_input = st.number_input(
                "Moment Magnitude (kip-ft)",
                min_value=0.01,
                value=10.0,
                step=1.0
            )
            moment_magnitude_kipin = moment_magnitude_input * 12.0
        else:
            moment_magnitude_input = st.number_input(
                "Moment Magnitude (kip-in)",
                min_value=0.01,
                value=120.0,
                step=5.0
            )
            moment_magnitude_kipin = moment_magnitude_input

        moment_load_case = st.selectbox(
            "Moment Load Case",
            ["Dead Load", "Live Load", "Other"]
        )

        st.caption(
            "Counterclockwise moments are treated as positive."
        )
    else:
        moment_direction = "Counterclockwise"
        moment_position = 0.0
        moment_magnitude_kipin = 0.0

    st.subheader("3. Distributed Load (UDL)")
    enable_udl = st.toggle(
        "Enable Distributed Load (UDL)",
        value=False,
        key="enable_udl"
    )

    # Keep UDL start/end values independent and valid.
    if "udl_start_display" not in st.session_state:
        st.session_state.udl_start_display = 0.0

    if "udl_end_display" not in st.session_state:
        if st.session_state.unit_system == "Metric":
            st.session_state.udl_end_display = float(L / 39.37007874)
        elif "Feet" in len_unit:
            st.session_state.udl_end_display = float(L / 12.0)
        else:
            st.session_state.udl_end_display = float(L)

    # Internal UDL intensity is always stored in kip/in.
    # The sidebar input follows the active display units.
    if enable_udl:
        if st.session_state.unit_system == "Metric":
            w_input = st.number_input(
                "Intensity w (kN/m)",
                min_value=0.001,
                value=14.594,
                step=0.5
            )

            # kN/m -> kip/in
            w_magnitude = (
                w_input
                / 4.448221615
                / 39.37007874
            )
            udl_display_unit = "kN/m"
            udl_display_intensity = w_input

            max_udl_position = float(L / 39.37007874)

            st.session_state.udl_start_display = min(
                max(st.session_state.udl_start_display, 0.0),
                max_udl_position
            )
            st.session_state.udl_end_display = min(
                max(st.session_state.udl_end_display, 0.0),
                max_udl_position
            )

            col_u1, col_u2 = st.columns(2)
            with col_u1:
                x_start_display = st.number_input(
                    "Start x₁ (m)",
                    min_value=0.0,
                    max_value=max_udl_position,
                    step=0.1,
                    key="udl_start_display"
                )
            with col_u2:
                x_end_display = st.number_input(
                    "End x₂ (m)",
                    min_value=0.0,
                    max_value=max_udl_position,
                    step=0.1,
                    key="udl_end_display"
                )

            x_start = x_start_display * 39.37007874
            x_end = x_end_display * 39.37007874
            udl_position_unit = "m"

        elif "Feet" in len_unit:
            if "Pounds" in force_unit:
                w_input = st.number_input(
                    "Intensity w (lb/ft)",
                    min_value=1.0,
                    value=1000.0,
                    step=50.0
                )

                # lb/ft -> kip/in
                w_magnitude = w_input / 12000.0
                udl_display_unit = "lb/ft"
            else:
                w_input = st.number_input(
                    "Intensity w (kip/ft)",
                    min_value=0.001,
                    value=1.0,
                    step=0.1
                )

                # kip/ft -> kip/in
                w_magnitude = w_input / 12.0
                udl_display_unit = "kip/ft"

            udl_display_intensity = w_input

            max_udl_position = float(L / 12.0)

            st.session_state.udl_start_display = min(
                max(st.session_state.udl_start_display, 0.0),
                max_udl_position
            )
            st.session_state.udl_end_display = min(
                max(st.session_state.udl_end_display, 0.0),
                max_udl_position
            )

            col_u1, col_u2 = st.columns(2)
            with col_u1:
                x_start_display = st.number_input(
                    "Start x₁ (ft)",
                    min_value=0.0,
                    max_value=max_udl_position,
                    step=0.5,
                    key="udl_start_display"
                )
            with col_u2:
                x_end_display = st.number_input(
                    "End x₂ (ft)",
                    min_value=0.0,
                    max_value=max_udl_position,
                    step=0.5,
                    key="udl_end_display"
                )

            x_start = x_start_display * 12.0
            x_end = x_end_display * 12.0
            udl_position_unit = "ft"

        else:
            if "Pounds" in force_unit:
                w_input = st.number_input(
                    "Intensity w (lb/in)",
                    min_value=1.0,
                    value=83.333,
                    step=10.0
                )

                # lb/in -> kip/in
                w_magnitude = w_input / 1000.0
                udl_display_unit = "lb/in"
            else:
                w_input = st.number_input(
                    "Intensity w (kip/in)",
                    min_value=0.0001,
                    value=1.0 / 12.0,
                    step=0.01
                )

                w_magnitude = w_input
                udl_display_unit = "kip/in"

            udl_display_intensity = w_input

            max_udl_position = float(L)

            st.session_state.udl_start_display = min(
                max(st.session_state.udl_start_display, 0.0),
                max_udl_position
            )
            st.session_state.udl_end_display = min(
                max(st.session_state.udl_end_display, 0.0),
                max_udl_position
            )

            col_u1, col_u2 = st.columns(2)
            with col_u1:
                x_start_display = st.number_input(
                    "Start x₁ (in)",
                    min_value=0.0,
                    max_value=max_udl_position,
                    step=1.0,
                    key="udl_start_display"
                )
            with col_u2:
                x_end_display = st.number_input(
                    "End x₂ (in)",
                    min_value=0.0,
                    max_value=max_udl_position,
                    step=1.0,
                    key="udl_end_display"
                )

            x_start = x_start_display
            x_end = x_end_display
            udl_position_unit = "in"

    else:
        w_magnitude = 0.0
        x_start, x_end = 0.0, 0.0
        x_start_display, x_end_display = 0.0, 0.0
        udl_display_intensity = 0.0
        udl_display_unit = ""
        udl_position_unit = ""

    # ================= SECTION PROPERTIES =================
    st.subheader("4. Section Properties")

    st.session_state.custom_Iz = st.number_input(
        "Moment of Inertia, Iz (in⁴)",
        min_value=0.01,
        value=float(st.session_state.custom_Iz),
        step=10.0
    )

    st.session_state.custom_E = st.number_input(
        "Young's Modulus, E (ksi)",
        min_value=1.0,
        value=float(st.session_state.custom_E),
        step=100.0
    )

    st.caption(
        "Enter Iz and E directly for a quick beam analysis."
    )

    if st.button(
        "📐 Launch Section Builder",
        type="primary",
        use_container_width=True,
        key="section_builder_only_button"
    ):
        open_section_builder()

    st.caption(
        "Use Section Builder to create a custom section and choose "
        "its shape, dimensions, material, strength, section modulus, "
        "shear area, and factor of safety."
    )

    # Values used by all downstream calculations.
    section_shape = st.session_state.selected_section_name
    I = float(st.session_state.custom_Iz)
    E_modulus = float(st.session_state.custom_E)

    # Advanced values are stored and edited inside Section Builder.
    S = float(st.session_state.custom_S)
    A_web = float(st.session_state.custom_A_web)
    mat_name = st.session_state.custom_material_name
    yield_strength = float(
        st.session_state.custom_yield_strength
    )
    factor_of_safety = float(
        st.session_state.custom_factor_of_safety
    )

    beam_color = "#455A64"
    theme_name = "Custom Section"


# ================= INPUT VALIDATION =================

input_errors = []

if L <= 0:
    input_errors.append("Beam length must be greater than zero.")

for i, location in enumerate(x_load, start=1):
    if location < 0 or location > L:
        input_errors.append(
            f"Point load P{i} must be located between 0 and the beam length."
        )

if enable_walker and (walker_pos < 0 or walker_pos > L):
    input_errors.append("The custom load must be located on the beam.")

if enable_udl:
    if x_end <= x_start:
        input_errors.append(
            "The distributed-load end position must be greater than the start position."
        )
    if x_start < 0 or x_end > L:
        input_errors.append("The distributed load must stay within the beam length.")

if input_errors:
    for message in input_errors:
        st.error(message)
    st.stop()

if is_advanced_support := (
    "Fixed" in support_A
    or "Fixed" in support_B
    or "Free" in support_A
    or "Free" in support_B
):
    st.warning(
        "Advanced support configurations are included as simplified educational features. "
        "The pinned–roller case is the recommended validated example."
    )


# ================= CALCULATIONS BASED ON SUPPORTS =================

all_P = list(P) + ([walker_load] if enable_walker else [])
all_x = list(x_load) + ([walker_pos] if enable_walker else [])

# Applied moment sign convention:
# Counterclockwise is positive, clockwise is negative.
applied_moment_sign = (
    1.0
    if moment_direction == "Counterclockwise"
    else -1.0
)

applied_moment_kipin = (
    applied_moment_sign * moment_magnitude_kipin
    if enable_moment
    else 0.0
)

if enable_udl and x_end > x_start:
    udl_length = x_end - x_start
    udl_total_force = w_magnitude * udl_length
    udl_center = x_start + udl_length / 2.0
else:
    udl_total_force = 0.0
    udl_center = 0.0
    udl_length = 0.0

x = np.linspace(0, L, 1000)
V = np.zeros_like(x)
M = np.zeros_like(x)

RA, RB, MA_fix, MB_fix = 0.0, 0.0, 0.0, 0.0

is_cantilever = ("Fixed" in support_A and "Free" in support_B) or ("Free" in support_A and "Fixed" in support_B)
is_fixed_fixed = ("Fixed" in support_A and "Fixed" in support_B)
is_propped = ("Fixed" in support_A and ("Pinned" in support_B or "Roller" in support_B)) or (("Pinned" in support_A or "Roller" in support_A) and "Fixed" in support_B)

if is_cantilever:
    if "Fixed" in support_A:
        total_downward = sum(all_P) + (udl_total_force if enable_udl else 0.0)
        RA = total_downward
        RB = 0.0
        sum_moments_fixed = sum(p * x_pos for p, x_pos in zip(all_P, all_x)) + (udl_total_force * udl_center if enable_udl else 0.0)
        MA_fix = sum_moments_fixed
        MB_fix = 0.0
    else:
        total_downward = sum(all_P) + (udl_total_force if enable_udl else 0.0)
        RA = 0.0
        RB = total_downward
        sum_moments_fixed = sum(p * (L - x_pos) for p, x_pos in zip(all_P, all_x)) + (udl_total_force * (L - udl_center) if enable_udl else 0.0)
        MA_fix = 0.0
        MB_fix = sum_moments_fixed

    if "Fixed" in support_A:
        V = np.full_like(x, RA)
        M = -MA_fix + RA * x
        for load, loc in zip(all_P, all_x):
            active = x >= loc
            V[active] -= load
            M[active] += load * (x[active] - loc)
        if enable_udl and udl_length > 0:
            for idx, xi in enumerate(x):
                if xi > x_start:
                    effective_len = min(xi, x_end) - x_start
                    if effective_len > 0:
                        V[idx] -= w_magnitude * effective_len
                        lever_arm = xi - (x_start + effective_len / 2.0)
                        M[idx] += w_magnitude * effective_len * lever_arm
    else:
        V = np.zeros_like(x)
        M = np.zeros_like(x)
        for idx, xi in enumerate(x):
            v_sum, m_sum = 0.0, 0.0
            for load, loc in zip(all_P, all_x):
                if xi >= loc:
                    v_sum += load
                    m_sum += load * (xi - loc)
            if enable_udl and udl_length > 0:
                if xi > x_start:
                    eff_len = min(xi, x_end) - x_start
                    if eff_len > 0:
                        v_sum += w_magnitude * eff_len
                        m_sum += w_magnitude * eff_len * (xi - (x_start + eff_len / 2.0))
            V[idx] = v_sum
            M[idx] = m_sum

elif is_fixed_fixed:
    total_downward = sum(all_P) + (udl_total_force if enable_udl else 0.0)
    RA = total_downward / 2.0
    RB = total_downward / 2.0
    sum_m = sum(p * x_pos for p, x_pos in zip(all_P, all_x)) + (udl_total_force * udl_center if enable_udl else 0.0)
    MA_fix = sum_m / 2.0
    MB_fix = sum_m / 2.0

    V = np.full_like(x, RA)
    M = RA * x - MA_fix
    for load, loc in zip(all_P, all_x):
        active = x >= loc
        V[active] -= load
        M[active] -= load * (x[active] - loc)
    if enable_udl and udl_length > 0:
        for idx, xi in enumerate(x):
            if xi > x_start:
                effective_len = min(xi, x_end) - x_start
                if effective_len > 0:
                    V[idx] -= w_magnitude * effective_len
                    lever_arm = xi - (x_start + effective_len / 2.0)
                    M[idx] -= w_magnitude * effective_len * lever_arm

elif is_propped:
    if "Fixed" in support_A:
        sum_m_free = sum(p * (L - x_pos) for p, x_pos in zip(all_P, all_x))
        if enable_udl and udl_length > 0:
            sum_m_free += w_magnitude * udl_length * (L - udl_center)
        RB = sum_m_free / (0.5 * (L**2)) if L > 0 else 0.0
        total_downward = sum(all_P) + (udl_total_force if enable_udl else 0.0)
        RA = total_downward - RB
        MA_fix = sum(p * x_pos for p, x_pos in zip(all_P, all_x)) + (udl_total_force * udl_center if enable_udl else 0.0) - RB * L
        MB_fix = 0.0
    else:
        sum_m_free = sum(p * x_pos for p, x_pos in zip(all_P, all_x))
        if enable_udl and udl_length > 0:
            sum_m_free += w_magnitude * udl_length * udl_center
        RA = sum_m_free / (0.5 * (L**2)) if L > 0 else 0.0
        total_downward = sum(all_P) + (udl_total_force if enable_udl else 0.0)
        RB = total_downward - RA
        MA_fix = 0.0
        MB_fix = sum_m_free

    V = np.full_like(x, RA)
    M = RA * x - MA_fix
    for load, loc in zip(all_P, all_x):
        active = x >= loc
        V[active] -= load
        M[active] -= load * (x[active] - loc)
    if enable_udl and udl_length > 0:
        for idx, xi in enumerate(x):
            if xi > x_start:
                effective_len = min(xi, x_end) - x_start
                if effective_len > 0:
                    V[idx] -= w_magnitude * effective_len
                    lever_arm = xi - (x_start + effective_len / 2.0)
                    M[idx] -= w_magnitude * effective_len * lever_arm

else: # Simply Supported
    sum_moments_A = (
        sum(p * x_pos for p, x_pos in zip(all_P, all_x))
        + (udl_total_force * udl_center if enable_udl else 0.0)
    )

    # RB*L - load moments + external applied moment = 0
    RB = (
        (sum_moments_A - applied_moment_kipin) / L
        if L > 0
        else 0.0
    )
    total_downward = sum(all_P) + (udl_total_force if enable_udl else 0.0)
    RA = total_downward - RB
    MA_fix, MB_fix = 0.0, 0.0

    V = np.full_like(x, RA)
    M = RA * x
    for load, loc in zip(all_P, all_x):
        active = x >= loc
        V[active] -= load
        M[active] -= load * (x[active] - loc)

    if enable_moment:
        moment_active = x >= moment_position
        M[moment_active] -= applied_moment_kipin

    if enable_udl and udl_length > 0:
        for idx, xi in enumerate(x):
            if xi > x_start:
                effective_len = min(xi, x_end) - x_start
                if effective_len > 0:
                    V[idx] -= w_magnitude * effective_len
                    lever_arm = xi - (x_start + effective_len / 2.0)
                    M[idx] -= w_magnitude * effective_len * lever_arm

max_v = np.max(np.abs(V)) if len(V) > 0 else 0.0
max_m = np.max(np.abs(M)) if len(M) > 0 else 0.0
max_m_kipft = max_m / 12.0

max_m_index = int(np.argmax(np.abs(M))) if len(M) > 0 else 0
max_m_location_in = float(x[max_m_index]) if len(x) > 0 else 0.0
max_m_location_ft = max_m_location_in / 12.0

dx = x[1] - x[0]
EI = E_modulus * I

if EI > 0:
    curvature = M / EI

    # First integration: curvature -> raw slope.
    theta_raw = np.zeros_like(x)
    theta_raw[1:] = np.cumsum(
        0.5 * (curvature[1:] + curvature[:-1]) * dx
    )

    # Second integration: raw slope -> raw deflection.
    deflection_raw = np.zeros_like(x)
    deflection_raw[1:] = np.cumsum(
        0.5 * (theta_raw[1:] + theta_raw[:-1]) * dx
    )

    if is_cantilever and "Fixed" in support_A:
        # Fixed at the left end:
        # theta(0) = 0 and v(0) = 0.
        theta = theta_raw
        v_deflection = deflection_raw

    elif is_cantilever and "Fixed" in support_B:
        # Right-fixed cantilever remains a simplified educational case.
        # Apply zero deflection and zero rotation at x = L.
        slope_constant = -theta_raw[-1]
        deflection_constant = -(
            deflection_raw[-1] + slope_constant * L
        )

        theta = theta_raw + slope_constant
        v_deflection = (
            deflection_raw
            + slope_constant * x
            + deflection_constant
        )

    else:
        # Simply supported boundary conditions:
        # v(0) = 0 and v(L) = 0.
        #
        # The unknown integration constant is the initial slope C1.
        # Since deflection_raw(0) = 0:
        # 0 = deflection_raw(L) + C1*L
        initial_slope = -deflection_raw[-1] / L

        theta = theta_raw + initial_slope
        v_deflection = deflection_raw + initial_slope * x

    max_deflection = np.max(np.abs(v_deflection))

else:
    theta = np.zeros_like(x)
    v_deflection = np.zeros_like(x)
    max_deflection = 0.0

sigma_max = max_m / S if S > 0 else 0.0
tau_max = max_v / A_web if A_web > 0 else 0.0
sigma_allow = yield_strength / factor_of_safety if factor_of_safety > 0 else 1.0
tau_allow = (0.577 * yield_strength) / factor_of_safety
utilization_ratio = sigma_max / sigma_allow

# ================= DISPLAY UNIT CONVERSIONS =================

if st.session_state.unit_system == "Metric":
    displayed_RA_metric = RA * 4.448221615
    displayed_RB_metric = RB * 4.448221615
    displayed_max_v_metric = max_v * 4.448221615
    displayed_max_m_metric = max_m_kipft * 1.355817948
    displayed_max_deflection_metric = max_deflection * 25.4
    displayed_sigma_max_metric = sigma_max * 6.894757293
    displayed_sigma_allow_metric = sigma_allow * 6.894757293

# Summary Metrics Display

if st.session_state.unit_system == "Metric":
    m1_val, m1_lbl = displayed_RA_metric, "Reaction R_A (kN)"
    m2_val, m2_lbl = displayed_RB_metric, "Reaction R_B (kN)"
    m3_val, m3_lbl = displayed_max_v_metric, "Max Shear V (kN)"
    fmt_str = "{:.2f} kN"
elif "Pounds" in force_unit:
    m1_val, m1_lbl = RA * 1000.0, "Reaction R_A (lbs)"
    m2_val, m2_lbl = RB * 1000.0, "Reaction R_B (lbs)"
    m3_val, m3_lbl = max_v * 1000.0, "Max Shear V (lbs)"
    fmt_str = "{:,.1f} lbs"
else:
    m1_val, m1_lbl = RA, "Reaction R_A (kips)"
    m2_val, m2_lbl = RB, "Reaction R_B (kips)"
    m3_val, m3_lbl = max_v, "Max Shear V (kips)"
    fmt_str = "{:.2f} kips"

m1, m2, m3, m4 = st.columns(4)
m1.metric(m1_lbl, fmt_str.format(m1_val))
m2.metric(m2_lbl, fmt_str.format(m2_val))
m3.metric(m3_lbl, fmt_str.format(m3_val))
m4.metric("Max Deflection", f"{max_deflection:.4f} in", delta=f"Limit: L/360 = {L/360:.2f} in")

st.caption(
    f"Maximum bending moment occurs at x = {max_m_location_ft:.2f} ft "
    f"from support A."
)

summary_csv = (
    "Result,Value,Unit\n"
    f"Reaction RA,{RA:.6f},kips\n"
    f"Reaction RB,{RB:.6f},kips\n"
    f"Maximum Shear,{max_v:.6f},kips\n"
    f"Maximum Moment,{max_m_kipft:.6f},kip-ft\n"
    f"Maximum Moment Location,{max_m_location_ft:.6f},ft\n"
    f"Maximum Bending Stress,{sigma_max:.6f},ksi\n"
    f"Allowable Bending Stress,{sigma_allow:.6f},ksi\n"
    f"Maximum Deflection,{max_deflection:.6f},in\n"
    f"Deflection Limit,{L/360:.6f},in\n"
    f"Utilization Ratio,{utilization_ratio:.6f},ratio\n"
)

st.download_button(
    "⬇️ Download Result Summary",
    data=summary_csv,
    file_name="beam_analysis_results.csv",
    mime="text/csv"
)

st.divider()

# ================= 0. PROBLEM DIAGRAM / BEAM SCHEMATIC =================

st.subheader("0. Problem Diagram / Beam Schematic")

fig_problem = go.Figure()

# Beam body
fig_problem.add_trace(go.Scatter(
    x=[0, L],
    y=[0, 0],
    mode="lines",
    line=dict(color=beam_color, width=12),
    hoverinfo="skip",
    showlegend=False
))

# Support A
if "Fixed" in support_A:
    fig_problem.add_trace(go.Scatter(x=[0, 0], y=[-0.45, 0.45], mode="lines", line=dict(color="#424242", width=8), showlegend=False))
elif "Free" not in support_A:
    fig_problem.add_trace(go.Scatter(x=[0], y=[-0.28], mode="markers", marker=dict(symbol="triangle-up", size=22, color="#424242"), showlegend=False))

# Support B
if "Fixed" in support_B:
    fig_problem.add_trace(go.Scatter(x=[L, L], y=[-0.45, 0.45], mode="lines", line=dict(color="#424242", width=8), showlegend=False))
elif "Free" not in support_B:
    support_symbol_B = "circle" if "Roller" in support_B else "triangle-up"
    fig_problem.add_trace(go.Scatter(x=[L], y=[-0.28], mode="markers", marker=dict(symbol=support_symbol_B, size=22, color="#616161"), showlegend=False))

# Labels A and B
fig_problem.add_annotation(x=0, y=0.25, text="A", showarrow=False, font=dict(size=14, color="black"))
fig_problem.add_annotation(x=L, y=0.25, text="B", showarrow=False, font=dict(size=14, color="black"))

# Point loads
for i, (p_val, x_val, meta) in enumerate(
    zip(P, x_load, point_load_meta)
):
    p_display = abs(p_val)

    p_label = (
        f"P{i + 1} [{meta['case']}] = {p_display * 1000:.0f} lbs"
        if "Pounds" in force_unit
        else f"P{i + 1} [{meta['case']}] = {p_display:.2f} kips"
    )

    arrow_tail_y = 0.95 if p_val >= 0 else -0.95

    if meta["direction"] == "Angled":
        normalized_angle = meta["angle_deg"] % 360.0

        if 0.0 <= normalized_angle < 90.0:
            angle_symbol = "↗"
        elif 90.0 <= normalized_angle < 180.0:
            angle_symbol = "↖"
        elif 180.0 <= normalized_angle < 270.0:
            angle_symbol = "↙"
        else:
            angle_symbol = "↘"
        p_label = (
            f"{angle_symbol} {p_label} @ {meta['angle_deg']:.0f}°"
        )

    fig_problem.add_annotation(
        x=x_val,
        y=0,
        ax=x_val,
        ay=arrow_tail_y,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        text=p_label,
        showarrow=True,
        arrowhead=2,
        arrowsize=1.2,
        arrowwidth=2.5,
        arrowcolor="#D32F2F",
        font=dict(
            color="#D32F2F",
            size=11,
            family="Arial Black"
        )
    )

# Moving load
if enable_walker:
    moving_display = abs(walker_load)

    moving_label = (
        f"{icon_str} [{moving_case}] {moving_display * 1000:.0f} lbs"
        if "Pounds" in force_unit
        else f"{icon_str} [{moving_case}] {moving_display:.2f} kips"
    )

    if moving_direction == "Angled":
        normalized_angle = moving_angle_deg % 360.0

        if 0.0 <= normalized_angle < 90.0:
            moving_symbol = "↗"
        elif 90.0 <= normalized_angle < 180.0:
            moving_symbol = "↖"
        elif 180.0 <= normalized_angle < 270.0:
            moving_symbol = "↙"
        else:
            moving_symbol = "↘"
        moving_label = (
            f"{moving_symbol} {moving_label} @ {moving_angle_deg:.0f}°"
        )

    moving_tail_y = 1.15 if walker_load >= 0 else -1.15

    fig_problem.add_annotation(
        x=walker_pos,
        y=0,
        ax=walker_pos,
        ay=moving_tail_y,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        text=moving_label,
        showarrow=True,
        arrowhead=2,
        arrowsize=1.2,
        arrowwidth=2.5,
        arrowcolor="#2E7D32",
        font=dict(
            color="#2E7D32",
            size=11,
            family="Arial Black"
        )
    )

# Applied moment
if enable_moment:
    moment_symbol = (
        "↺"
        if moment_direction == "Counterclockwise"
        else "↻"
    )

    displayed_input_moment = (
        moment_magnitude_kipin / 12.0
        if st.session_state.display_moment_unit == "kip-ft"
        else moment_magnitude_kipin
    )

    fig_problem.add_annotation(
        x=moment_position,
        y=0.45,
        text=(
            f"{moment_symbol} M = "
            f"{displayed_input_moment:.2f} "
            f"{st.session_state.display_moment_unit}"
        ),
        showarrow=False,
        font=dict(
            color="#7B1FA2",
            size=13,
            family="Arial Black"
        )
    )

# UDL
if enable_udl and udl_length > 0:
    udl_positions = np.linspace(x_start, x_end, 9)
    for udl_x in udl_positions:
        fig_problem.add_annotation(
            x=udl_x, y=0,
            ax=udl_x, ay=0.6,
            xref="x", yref="y",
            axref="x", ayref="y",
            text="",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#F57C00"
        )
    fig_problem.add_trace(go.Scatter(
        x=[x_start, x_end],
        y=[0.6, 0.6],
        mode="lines",
        line=dict(color="#F57C00", width=2),
        hoverinfo="skip",
        showlegend=False
    ))
    w_label = (
        f"w = {udl_display_intensity:.3f} "
        f"{udl_display_unit}"
    )
    fig_problem.add_annotation(
        x=(x_start + x_end) / 2,
        y=0.78,
        text=w_label,
        showarrow=False,
        font=dict(color="#E65100", size=11, family="Arial Black")
    )

fig_problem.update_layout(
    title=f"Beam Schematic — A: {support_A}, B: {support_B}",
    height=340,
    showlegend=False,
    template="plotly_white",
    margin=dict(l=25, r=25, t=60, b=30)
)
fig_problem.update_xaxes(title_text="Beam Position x (in)", range=[-0.05 * L, 1.05 * L], showgrid=False, zeroline=False)
fig_problem.update_yaxes(visible=False, range=[-0.65, 1.35], showgrid=False, zeroline=False)

st.plotly_chart(fig_problem, use_container_width=True)

st.divider()

# ================= 1. FREE BODY DIAGRAM (FBD) =================

st.subheader("0. Free Body Diagram (FBD)")

fig_fbd = go.Figure()

# Thin beam reference line, similar to a hand-drawn engineering FBD
fig_fbd.add_trace(go.Scatter(
    x=[0, L],
    y=[0, 0],
    mode="lines",
    line=dict(color="black", width=3),
    hoverinfo="skip",
    showlegend=False
))

# End labels
fig_fbd.add_annotation(x=0, y=0.08, text="A", showarrow=False, xanchor="center", font=dict(size=14, color="black"))
fig_fbd.add_annotation(x=L, y=0.08, text="B", showarrow=False, xanchor="center", font=dict(size=14, color="black"))

# Coordinate axes
axis_x0 = -0.10 * L
axis_y0 = -0.65
fig_fbd.add_annotation(
    x=axis_x0 + 0.18 * L, y=axis_y0,
    ax=axis_x0, ay=axis_y0,
    xref="x", yref="y",
    axref="x", ayref="y",
    text="x",
    showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2, arrowcolor="black",
    font=dict(size=14, color="black")
)
fig_fbd.add_annotation(
    x=axis_x0, y=0.15,
    ax=axis_x0, ay=axis_y0,
    xref="x", yref="y",
    axref="x", ayref="y",
    text="y",
    showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2, arrowcolor="black",
    font=dict(size=14, color="black")
)

# Reaction at A
if "Free" not in support_A and abs(RA) > 1e-12:
    ra_text = (f"R_A = {RA*1000:.0f} lbs" if "Pounds" in force_unit else f"R_A = {RA:.2f} kips")
    fig_fbd.add_annotation(
        x=0, y=0,
        ax=0, ay=-0.55 if RA >= 0 else 0.55,
        xref="x", yref="y",
        axref="x", ayref="y",
        text=ra_text,
        showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor="#D32F2F",
        font=dict(color="#D32F2F", size=11, family="Arial Black")
    )

# Reaction at B
if "Free" not in support_B and abs(RB) > 1e-12:
    rb_text = (f"R_B = {RB*1000:.0f} lbs" if "Pounds" in force_unit else f"R_B = {RB:.2f} kips")
    fig_fbd.add_annotation(
        x=L, y=0,
        ax=L, ay=-0.55 if RB >= 0 else 0.55,
        xref="x", yref="y",
        axref="x", ayref="y",
        text=rb_text,
        showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor="#D32F2F",
        font=dict(color="#D32F2F", size=11, family="Arial Black")
    )

# Fixed-end moments
if "Fixed" in support_A and abs(MA_fix) > 1e-12:
    fig_fbd.add_annotation(x=0.04 * L, y=0.45, text=f"M_A = {MA_fix/12.0:.2f} kip-ft", showarrow=False, font=dict(color="#D32F2F", size=11, family="Arial Black"))

if "Fixed" in support_B and abs(MB_fix) > 1e-12:
    fig_fbd.add_annotation(x=0.96 * L, y=0.45, text=f"M_B = {MB_fix/12.0:.2f} kip-ft", showarrow=False, font=dict(color="#D32F2F", size=11, family="Arial Black"))

# Concentrated point loads
for i, (p_val, x_val, meta) in enumerate(
    zip(P, x_load, point_load_meta)
):
    p_display = abs(p_val)

    p_label_text = (
        f"P{i + 1} [{meta['case']}] = {p_display * 1000:.0f} lbs"
        if "Pounds" in force_unit
        else f"P{i + 1} [{meta['case']}] = {p_display:.2f} kips"
    )

    if meta["direction"] == "Angled":
        normalized_angle = meta["angle_deg"] % 360.0

        if 0.0 <= normalized_angle < 90.0:
            angle_symbol = "↗"
        elif 90.0 <= normalized_angle < 180.0:
            angle_symbol = "↖"
        elif 180.0 <= normalized_angle < 270.0:
            angle_symbol = "↙"
        else:
            angle_symbol = "↘"
        p_label_text = (
            f"{angle_symbol} {p_label_text} @ {meta['angle_deg']:.0f}°"
        )

    fbd_tail_y = 0.75 if p_val >= 0 else -0.75

    fig_fbd.add_annotation(
        x=x_val,
        y=0,
        ax=x_val,
        ay=fbd_tail_y,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        text=p_label_text,
        showarrow=True,
        arrowhead=2,
        arrowsize=1.2,
        arrowwidth=2.5,
        arrowcolor="#1565C0",
        font=dict(
            color="#1565C0",
            size=11,
            family="Arial Black"
        )
    )

# Moving load
if enable_walker:
    moving_display = abs(walker_load)

    moving_text = (
        f"{icon_str} [{moving_case}] {moving_display * 1000:.0f} lbs"
        if "Pounds" in force_unit
        else f"{icon_str} [{moving_case}] {moving_display:.2f} kips"
    )

    if moving_direction == "Angled":
        normalized_angle = moving_angle_deg % 360.0

        if 0.0 <= normalized_angle < 90.0:
            moving_symbol = "↗"
        elif 90.0 <= normalized_angle < 180.0:
            moving_symbol = "↖"
        elif 180.0 <= normalized_angle < 270.0:
            moving_symbol = "↙"
        else:
            moving_symbol = "↘"
        moving_text = (
            f"{moving_symbol} {moving_text} @ {moving_angle_deg:.0f}°"
        )

    moving_fbd_tail_y = 1.0 if walker_load >= 0 else -1.0

    fig_fbd.add_annotation(
        x=walker_pos,
        y=0,
        ax=walker_pos,
        ay=moving_fbd_tail_y,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        text=moving_text,
        showarrow=True,
        arrowhead=2,
        arrowsize=1.2,
        arrowwidth=2.5,
        arrowcolor="#2E7D32",
        font=dict(
            color="#2E7D32",
            size=11,
            family="Arial Black"
        )
    )

# Applied moment
if enable_moment:
    moment_symbol = (
        "↺"
        if moment_direction == "Counterclockwise"
        else "↻"
    )

    displayed_input_moment = (
        moment_magnitude_kipin / 12.0
        if st.session_state.display_moment_unit == "kip-ft"
        else moment_magnitude_kipin
    )

    fig_fbd.add_annotation(
        x=moment_position,
        y=0.42,
        text=(
            f"{moment_symbol} M = "
            f"{displayed_input_moment:.2f} "
            f"{st.session_state.display_moment_unit}"
        ),
        showarrow=False,
        font=dict(
            color="#7B1FA2",
            size=12,
            family="Arial Black"
        )
    )

# Distributed load represented by multiple downward arrows
if enable_udl and udl_length > 0:
    n_udl_arrows = 9
    udl_positions = np.linspace(x_start, x_end, n_udl_arrows)
    for udl_x in udl_positions:
        fig_fbd.add_annotation(
            x=udl_x, y=0,
            ax=udl_x, ay=0.55,
            xref="x", yref="y",
            axref="x", ayref="y",
            text="",
            showarrow=True, arrowhead=2, arrowsize=1.0, arrowwidth=2, arrowcolor="#F57C00"
        )
    fig_fbd.add_trace(go.Scatter(
        x=[x_start, x_end],
        y=[0.55, 0.55],
        mode="lines",
        line=dict(color="#F57C00", width=2),
        hoverinfo="skip",
        showlegend=False
    ))
    w_label_text = (
        f"w = {udl_display_intensity:.3f} "
        f"{udl_display_unit}"
    )
    fig_fbd.add_annotation(
        x=(x_start + x_end) / 2, y=0.72,
        text=w_label_text,
        showarrow=False,
        font=dict(color="#E65100", size=11, family="Arial Black")
    )

fig_fbd.update_layout(
    title=f"Free Body Diagram — A: {support_A}, B: {support_B}",
    height=390,
    showlegend=False,
    template="plotly_white",
    margin=dict(l=25, r=25, t=60, b=30),
    plot_bgcolor="white"
)
fig_fbd.update_xaxes(title_text="Beam Position x (in)", range=[-0.15 * L, 1.05 * L], showgrid=False, zeroline=False)
fig_fbd.update_yaxes(visible=False, range=[-0.9, 1.25], showgrid=False, zeroline=False)

st.plotly_chart(fig_fbd, use_container_width=True)

st.divider()

# ================= 2. INTERNAL FORCE & DEFLECTION DIAGRAMS =================

st.subheader("1. Internal Force and Deflection Diagrams")

fig_results = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.08,
    subplot_titles=(
        "Shear Force Diagram (SFD)",
        f"Bending Moment Diagram (BMD) - Max: {max_m_kipft:.2f} kip-ft",
        f"Deflection Curve (Elastic Line) - Max: {max_deflection:.4f} in"
    )
)

V_plot = V * 1000.0 if "Pounds" in force_unit else V
v_unit_label = "Shear V (lbs)" if "Pounds" in force_unit else "Shear V (kips)"

fig_results.add_trace(go.Scatter(
    x=x, y=V_plot,
    mode="lines", fill="tozeroy",
    line=dict(color="#1E88E5", width=2),
    name="Shear",
    hovertemplate="Position x: %{x:.1f} in<br>Shear V: %{y:.2f}<extra></extra>"
), row=1, col=1)

fig_results.add_trace(go.Scatter(
    x=x, y=M / 12.0,
    mode="lines", fill="tozeroy",
    line=dict(color="#E53935", width=2),
    name="Moment",
    hovertemplate="Position x: %{x:.1f} in<br>Moment M: %{y:.2f} kip-ft<extra></extra>"
), row=2, col=1)

fig_results.add_trace(go.Scatter(
    x=x, y=v_deflection,
    mode="lines", fill="tozeroy",
    line=dict(color="#43A047", width=2),
    name="Deflection",
    hovertemplate="Position x: %{x:.1f} in<br>Deflection: %{y:.4f} in<extra></extra>"
), row=3, col=1)

for x_val in all_x:
    for row_number in [1, 2, 3]:
        fig_results.add_vline(x=x_val, line_width=1, line_dash="dash", line_color="gray", opacity=0.7, row=row_number, col=1)

fig_results.update_layout(height=720, showlegend=False, hovermode="x unified", template="plotly_white")
fig_results.update_yaxes(title_text=v_unit_label, row=1, col=1)
fig_results.update_yaxes(title_text="Moment (kip-ft)", row=2, col=1)
fig_results.update_yaxes(title_text="Deflection (in)", row=3, col=1)
fig_results.update_xaxes(title_text="Beam Position x (in)", row=3, col=1)

st.plotly_chart(fig_results, use_container_width=True)

st.divider()


# ================= STEP-BY-STEP CALCULATIONS =================

st.divider()
st.subheader("🧮 Step-by-Step Calculations")

with st.expander("Show Detailed Calculations", expanded=False):

    # Step 1: Given information
    st.markdown("### Step 1: Given Information")

    st.write(f"Beam Length, L = {L / 12.0:.2f} ft")
    st.write(f"Beam Length, L = {L:.2f} in")

    for i, (load, location) in enumerate(zip(P, x_load)):
        meta = point_load_meta[i]

        direction_text = (
            meta["direction"]
            if meta["direction"] != "Angled"
            else f"Angled at θ = {meta['angle_deg']:.0f}°"
        )

        st.write(
            f"Load P{i + 1} [{meta['case']}] = "
            f"{abs(load):.3f} kip vertical component, "
            f"{direction_text}, at "
            f"x{i + 1} = {location / 12.0:.2f} ft from A"
        )

    if enable_walker:
        st.write(
            f"Custom Load [{moving_case}] = "
            f"{abs(walker_load):.3f} kip vertical component "
            f"at x = {walker_pos / 12.0:.2f} ft from A"
        )

    if enable_udl and udl_length > 0:
        st.write(
            f"Distributed Load, w = "
            f"{udl_display_intensity:.3f} {udl_display_unit} "
            f"from {x_start_display:.2f} {udl_position_unit} "
            f"to {x_end_display:.2f} {udl_position_unit}"
        )

    st.write(f"Section Shape = {section_shape}")
    st.write(f"Material = {mat_name}")
    st.write(f"Factor of Safety = {factor_of_safety:.2f}")

    # Step 2: Total applied load
    st.markdown("### Step 2: Total Applied Load")

    total_point_load = sum(all_P)

    st.latex(r"\sum P = P_1 + P_2 + \cdots + P_n")
    st.write(f"Total Point Load = {total_point_load:.2f} kips")

    if enable_udl and udl_length > 0:
        st.latex(r"W = wL_{UDL}")
        st.write(
            f"Equivalent UDL Force = "
            f"{udl_display_intensity:.3f} {udl_display_unit} × "
            f"{(x_end_display - x_start_display):.2f} "
            f"{udl_position_unit} "
            f"= {udl_total_force:.2f} kips"
        )

    total_downward_step = total_point_load + udl_total_force
    st.write(f"Total Downward Load = {total_downward_step:.2f} kips")

    if enable_moment:
        displayed_step_moment = (
            moment_magnitude_kipin / 12.0
            if st.session_state.display_moment_unit == "kip-ft"
            else moment_magnitude_kipin
        )

        st.write(
            f"Applied Moment = {displayed_step_moment:.2f} "
            f"{st.session_state.display_moment_unit} "
            f"({moment_direction})"
        )

    # Step 3: Reaction at support B
    st.markdown("### Step 3: Reaction at Support B")

    if not is_cantilever and not is_fixed_fixed and not is_propped:
        st.latex(r"\sum M_A = 0")
        st.latex(r"R_B L = \sum(P_i x_i) + W x_W")
        st.latex(r"R_B=\frac{\sum(P_i x_i)+W x_W}{L}")

        point_moment_terms = [
            f"({load:.2f})({location / 12.0:.2f})"
            for load, location in zip(all_P, all_x)
        ]

        moment_expression = " + ".join(point_moment_terms) if point_moment_terms else "0"

        if enable_udl and udl_length > 0:
            moment_expression += (
                f" + ({udl_total_force:.2f})"
                f"({udl_center / 12.0:.2f})"
            )

        st.write(
            f"RB × {L / 12.0:.2f} = {moment_expression}"
        )
        st.write(f"RB = {RB:.2f} kips")
    else:
        st.info(
            "The reaction equations depend on the selected support configuration. "
            "The calculated reactions are shown below."
        )
        st.write(f"RA = {RA:.2f} kips")
        st.write(f"RB = {RB:.2f} kips")

    # Step 4: Reaction at support A
    st.markdown("### Step 4: Reaction at Support A")

    st.latex(r"\sum F_y = 0")
    st.latex(r"R_A + R_B - \sum P - W = 0")
    st.latex(r"R_A = \sum P + W - R_B")

    st.write(
        f"RA = {total_downward_step:.2f} - {RB:.2f}"
    )
    st.write(f"RA = {RA:.2f} kips")

    # Step 5: Shear force
    st.markdown("### Step 5: Shear Force")

    st.latex(r"V(x)=R_A-\sum P_i-wx")
    st.write(f"Maximum Shear Force = {max_v:.2f} kips")

    # Step 6: Bending moment
    st.markdown("### Step 6: Bending Moment")

    st.latex(r"M(x)=R_Ax-\sum P_i(x-a_i)-\frac{wx^2}{2}")
    st.write(f"Maximum Bending Moment = {max_m_kipft:.2f} kip-ft")
    st.write(
        f"Maximum Moment Location = {max_m_location_ft:.2f} ft from A"
    )

    # Step 7: Section properties
    st.markdown("### Step 7: Section Properties")

    if section_shape == "Rectangular (Solid)":
        st.latex(r"I=\frac{bh^3}{12}")
        st.write(
            f"I = ({b:.2f})({h:.2f})³ / 12 "
            f"= {I:,.2f} in⁴"
        )

        st.latex(r"S=\frac{I}{h/2}")
        st.write(f"S = {S:,.2f} in³")
    else:
        st.write(f"**Moment of Inertia, I = {I:,.2f} in⁴**")
        st.write(f"**Section Modulus, S = {S:,.2f} in³**")

    # Step 8: Maximum bending stress
    st.markdown("### Step 8: Maximum Bending Stress")

    st.latex(r"\sigma_{max}=\frac{M_{max}}{S}")
    st.write(
        f"σmax = {max_m:.2f} kip-in / {S:.2f} in³"
    )
    st.write(f"Maximum Bending Stress = {sigma_max:.2f} ksi")

    # Step 9: Allowable stress
    st.markdown("### Step 9: Allowable Stress")

    st.latex(r"\sigma_{allow}=\frac{F_y}{FOS}")
    st.write(
        f"σallow = {yield_strength:.2f} / "
        f"{factor_of_safety:.2f}"
    )
    st.write(f"Allowable Stress = {sigma_allow:.2f} ksi")

    # Step 10: Utilization ratio
    st.markdown("### Step 10: Utilization Ratio")

    st.latex(
        r"\text{Utilization Ratio}"
        r"=\frac{\sigma_{max}}{\sigma_{allow}}"
    )

    st.write(
        f"Utilization Ratio = "
        f"{sigma_max:.2f} / {sigma_allow:.2f}"
    )
    st.write(f"Utilization Ratio = {utilization_ratio:.3f}")
    st.write(f"Utilization Percentage = {utilization_ratio:.1%}")

    # Step 11: Bending safety result
    st.markdown("### Step 11: Bending Safety Result")

    if utilization_ratio <= 1.0:
        st.success(
            f"PASS ✅ — {sigma_max:.2f} ksi ≤ "
            f"{sigma_allow:.2f} ksi"
        )
    else:
        st.error(
            f"FAIL ❌ — {sigma_max:.2f} ksi > "
            f"{sigma_allow:.2f} ksi"
        )

    # Step 12: Deflection check
    st.markdown("### Step 12: Deflection Check")

    deflection_limit = L / 360.0

    st.latex(r"\delta_{allow}=\frac{L}{360}")
    st.write(
        f"Allowable Deflection = {L:.2f} / 360 "
        f"= {deflection_limit:.4f} in"
    )
    st.write(
        f"Maximum Calculated Deflection = "
        f"{max_deflection:.4f} in"
    )

    if (
        not is_cantilever
        and not is_fixed_fixed
        and not is_propped
        and len(all_P) == 1
        and not enable_udl
        and not enable_moment
    ):
        st.caption(
            "For a simply supported beam with one point load, "
            "the numerical result should closely match the standard "
            "closed-form beam formula."
        )

    if max_deflection <= deflection_limit:
        st.success(
            f"Deflection PASS ✅ — "
            f"{max_deflection:.4f} in ≤ {deflection_limit:.4f} in"
        )
    else:
        st.error(
            f"Deflection FAIL ❌ — "
            f"{max_deflection:.4f} in > {deflection_limit:.4f} in"
        )


# ================= 2. SAFETY CHECK & PROPERTIES =================

st.subheader("🛡️ Safety Check & Properties")
col_st1, col_st2, col_st3 = st.columns(3)

with col_st1:
    if utilization_ratio <= 1.0:
        st.success(f"### PASS ✅\nBending Utilization: {utilization_ratio:.1%}")
    else:
        st.error(f"### FAIL ❌\nBending Utilization: {utilization_ratio:.1%}")

with col_st2:
    st.write(f"- Support A: {support_A} | Support B: {support_B}")
    st.write(f"- Selected Material: {mat_name} ({theme_name})")
    st.write(
        f"- Section Builder Selection: "
        f"{st.session_state.selected_section_name}"
    )
    st.write(
        f"- Active Iz: {I:,.1f} in⁴"
    )
    st.write(
        f"- Active E: {E_modulus:,.1f} ksi"
    )
    st.write(f"- Section Shape: {section_shape}")
    st.write(f"- Moment of Inertia I: {I:,.1f} in^4")

with col_st3:
    st.write(f"- Max Bending Stress ($\\sigma_{{max}}$): {sigma_max:.2f} ksi (Allowable: {sigma_allow:.2f} ksi)")
    st.write(f"- Max Shear Stress ($\\tau_{{max}}$): {tau_max:.3f} ksi (Allowable: {tau_allow:.2f} ksi)")
    st.write(f"- Max Deflection: {max_deflection:.4f} in (Limit L/360: {L/360:.2f} in)")
