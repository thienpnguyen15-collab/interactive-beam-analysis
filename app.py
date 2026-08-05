from pathlib import Path

code = r'''
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =========================================================
# PAGE SETUP
# =========================================================
st.set_page_config(
    page_title="Interactive Beam Analysis",
    page_icon="🏗️",
    layout="wide"
)

# =========================================================
# CUSTOM STYLE
# =========================================================
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background: #1f2633;
    }

    [data-testid="stSidebar"] * {
        color: #f3f4f6;
    }

    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        min-height: 48px;
        background: transparent;
        color: #f3f4f6;
        border: 1px solid #708096;
        border-radius: 6px;
        font-size: 18px;
        text-align: left;
        padding-left: 18px;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: #2b3545;
        border-color: #5b92dc;
        color: white;
    }

    [data-testid="stSidebar"] input {
        background: white;
        color: #253047;
    }

    .menu-title {
        color: #8592a8;
        text-align: center;
        font-size: 20px;
        margin-top: 8px;
    }

    .menu-rule {
        border-top: 1px solid #6b7483;
        margin: 4px 0 14px 0;
    }

    .panel-title {
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 12px;
    }

    .or-line {
        text-align: center;
        font-size: 22px;
        font-weight: 700;
        margin: 12px 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# SESSION STATE
# =========================================================
defaults = {
    "panel": "menu",
    "L_ft": 16.0,
    "support_A": "Pinned",
    "support_B": "Roller",
    "I": 2730.0,
    "E": 29000.0,
    "Fy": 36.0,
    "FOS": 1.5,
    "section_name": "Rectangular",
    "point_loads": [
        {
            "direction": "Down",
            "position_ft": 4.0,
            "magnitude_kip": 5.0,
            "load_case": "Dead Load",
        },
        {
            "direction": "Down",
            "position_ft": 8.0,
            "magnitude_kip": 5.0,
            "load_case": "Dead Load",
        },
    ],
    "moments": [],
    "distributed_loads": [],
    "length_unit": "ft",
    "force_unit": "kip",
    "moment_unit": "kip-ft",
    "stress_unit": "ksi",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def open_panel(name):
    st.session_state.panel = name
    st.rerun()


def back_to_menu():
    st.session_state.panel = "menu"
    st.rerun()


# =========================================================
# SECTION BUILDER
# =========================================================
@st.dialog("Create Custom Section", width="large")
def section_builder():

    custom_tab, properties_tab, american_tab = st.tabs(
        ["Custom", "Section Properties", "American"]
    )

    with custom_tab:
        st.subheader("Select a Custom Section")

        search_term = st.text_input(
            "Search",
            placeholder="Search by section name"
        )

        category = st.selectbox(
            "Category",
            [
                "All",
                "Steel Sections",
                "Timber Sections",
                "Concrete Sections",
                "Custom Sections",
            ]
        )

        section_library = [
            ("I-Beam", "Steel Sections", "工"),
            ("T-Beam", "Steel Sections", "⊤"),
            ("C-Channel", "Steel Sections", "⊏"),
            ("L-Shape", "Steel Sections", "⌞"),
            ("Double Channel", "Steel Sections", "⊏⊐"),
            ("Rectangle", "Custom Sections", "▰"),
            ("Square Tube", "Steel Sections", "▣"),
            ("Solid Circle", "Custom Sections", "●"),
            ("Round Tube", "Steel Sections", "◉"),
            ("Hollow Rectangle", "Steel Sections", "▢"),
            ("Trapezoid", "Custom Sections", "▱"),
            ("Triangle", "Custom Sections", "△"),
            ("Right Triangle", "Custom Sections", "◿"),
            ("Timber Rectangle", "Timber Sections", "▭"),
            ("Concrete Rectangle", "Concrete Sections", "▮"),
        ]

        filtered = []

        for name, group, icon in section_library:
            search_ok = (
                not search_term
                or search_term.lower() in name.lower()
            )

            category_ok = (
                category == "All"
                or group == category
            )

            if search_ok and category_ok:
                filtered.append((name, group, icon))

        rows = [filtered[i:i + 5] for i in range(0, len(filtered), 5)]

        for row_index, row in enumerate(rows):
            cols = st.columns(5)

            for col_index, (name, group, icon) in enumerate(row):
                with cols[col_index]:
                    st.markdown(
                        f"""
                        <div style="
                            border:1px solid #d7dde5;
                            border-radius:8px;
                            padding:12px;
                            min-height:115px;
                            text-align:center;
                            background:white;
                        ">
                            <div style="font-size:46px;">{icon}</div>
                            <div style="font-size:13px;">{name}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if st.button(
                        "Select",
                        key=f"section_{row_index}_{col_index}",
                        use_container_width=True
                    ):
                        st.session_state.section_name = name
                        st.success(f"{name} selected.")

        st.info(
            f"Current section: {st.session_state.section_name}"
        )

    with properties_tab:
        st.subheader("Section Properties")

        st.session_state.I = st.number_input(
            "Moment of Inertia (Iz)",
            min_value=0.01,
            value=float(st.session_state.I),
            step=10.0
        )
        st.caption("Unit: in⁴")

        st.session_state.E = st.number_input(
            "Young's Modulus (E)",
            min_value=1.0,
            value=float(st.session_state.E),
            step=100.0
        )
        st.caption("Unit: ksi")

        st.markdown(
            "<div class='or-line'>OR</div>",
            unsafe_allow_html=True
        )

        b = st.number_input(
            "Rectangular Width b (in)",
            min_value=0.1,
            value=8.0,
            step=0.5
        )

        h = st.number_input(
            "Rectangular Height h (in)",
            min_value=0.1,
            value=16.0,
            step=0.5
        )

        calculated_I = b * h**3 / 12.0

        st.latex(r"I_z=\frac{bh^3}{12}")
        st.write(f"Calculated Iz = {calculated_I:,.2f} in⁴")

        if st.button(
            "Use Calculated Iz",
            type="primary",
            use_container_width=True
        ):
            st.session_state.I = calculated_I
            st.session_state.section_name = "Rectangular"
            st.success("Calculated rectangular section selected.")

    with american_tab:
        st.subheader("American Section Library")

        st.selectbox(
            "Section Family",
            ["W-Shape", "C-Channel", "L-Angle", "HSS"]
        )

        st.text_input(
            "Search Section",
            placeholder="Example: W12x26"
        )

        st.info(
            "This educational version does not include the full AISC database yet."
        )


# =========================================================
# SETTINGS
# =========================================================
@st.dialog("⚙️ Settings", width="large")
def settings_dialog():

    st.subheader("Unit System")

    st.selectbox(
        "Units",
        ["Imperial"],
        index=0
    )

    st.session_state.length_unit = st.selectbox(
        "Length",
        ["in", "ft"],
        index=0 if st.session_state.length_unit == "in" else 1
    )

    st.session_state.force_unit = st.selectbox(
        "Force",
        ["lb", "kip"],
        index=0 if st.session_state.force_unit == "lb" else 1
    )

    st.session_state.moment_unit = st.selectbox(
        "Moment",
        ["kip-in", "kip-ft"],
        index=0 if st.session_state.moment_unit == "kip-in" else 1
    )

    st.session_state.stress_unit = st.selectbox(
        "Stress",
        ["psi", "ksi"],
        index=0 if st.session_state.stress_unit == "psi" else 1
    )

    st.markdown(
        f"""
        **Section Length:** {st.session_state.length_unit}  
        **Material Strength:** {st.session_state.stress_unit}
        """
    )


# =========================================================
# SIDEBAR MENU
# =========================================================
with st.sidebar:

    if st.session_state.panel == "menu":

        st.markdown(
            '<div class="menu-title">Model</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="menu-rule"></div>',
            unsafe_allow_html=True
        )

        if st.button("Beam"):
            open_panel("beam")

        if st.button("Supports"):
            open_panel("supports")

        if st.button("Section"):
            open_panel("section")

        if st.button("Hinges"):
            open_panel("hinges")

        st.markdown(
            '<div class="menu-title">Loads</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="menu-rule"></div>',
            unsafe_allow_html=True
        )

        if st.button("Point Loads"):
            open_panel("point_loads")

        if st.button("Moments"):
            open_panel("moments")

        if st.button("Distributed Loads"):
            open_panel("distributed_loads")

        if st.button("Load Combinations"):
            open_panel("load_combinations")

    else:
        if st.button("⬅  Back"):
            back_to_menu()

        # -------------------------------------------------
        # BEAM
        # -------------------------------------------------
        if st.session_state.panel == "beam":

            st.markdown(
                '<div class="panel-title">Beam</div>',
                unsafe_allow_html=True
            )

            st.session_state.L_ft = st.number_input(
                "Beam Length",
                min_value=1.0,
                value=float(st.session_state.L_ft),
                step=1.0
            )

            st.caption("Unit: ft")

        # -------------------------------------------------
        # SUPPORTS
        # -------------------------------------------------
        elif st.session_state.panel == "supports":

            st.markdown(
                '<div class="panel-title">Support Type</div>',
                unsafe_allow_html=True
            )

            support_options = [
                "Pinned",
                "Roller",
                "Fixed",
                "Free",
            ]

            st.session_state.support_A = st.selectbox(
                "Support A",
                support_options,
                index=support_options.index(
                    st.session_state.support_A
                )
            )

            st.session_state.support_B = st.selectbox(
                "Support B",
                support_options,
                index=support_options.index(
                    st.session_state.support_B
                )
            )

            st.caption(
                "Supports are placed at the left and right ends."
            )

        # -------------------------------------------------
        # SECTION
        # -------------------------------------------------
        elif st.session_state.panel == "section":

            st.markdown(
                '<div class="panel-title">Moment of Inertia (Iz)</div>',
                unsafe_allow_html=True
            )

            st.session_state.I = st.number_input(
                "Iz",
                min_value=0.01,
                value=float(st.session_state.I),
                step=10.0,
                label_visibility="collapsed"
            )

            st.caption("in⁴")

            st.markdown(
                '<div class="panel-title">Young’s Modulus (E)</div>',
                unsafe_allow_html=True
            )

            st.session_state.E = st.number_input(
                "E",
                min_value=1.0,
                value=float(st.session_state.E),
                step=100.0,
                label_visibility="collapsed"
            )

            st.caption("ksi")

            st.markdown(
                "<div class='or-line'>OR</div>",
                unsafe_allow_html=True
            )

            if st.button(
                "Launch Section Builder",
                use_container_width=True
            ):
                section_builder()

        # -------------------------------------------------
        # HINGES
        # -------------------------------------------------
        elif st.session_state.panel == "hinges":

            st.markdown(
                '<div class="panel-title">Internal Hinges</div>',
                unsafe_allow_html=True
            )

            st.info(
                "Internal hinges are reserved for future development."
            )

        # -------------------------------------------------
        # POINT LOADS
        # -------------------------------------------------
        elif st.session_state.panel == "point_loads":

            st.markdown(
                '<div class="panel-title">Direction</div>',
                unsafe_allow_html=True
            )

            direction = st.radio(
                "Direction",
                ["Down", "Up", "Angled"],
                horizontal=True,
                label_visibility="collapsed"
            )

            position_ft = st.number_input(
                "Position",
                min_value=0.0,
                max_value=float(st.session_state.L_ft),
                value=min(
                    4.0,
                    float(st.session_state.L_ft)
                ),
                step=0.5
            )

            magnitude_kip = st.number_input(
                "Magnitude",
                min_value=0.01,
                value=5.0,
                step=0.5
            )

            load_case = st.selectbox(
                "Load Case",
                ["Dead Load", "Live Load", "Other"]
            )

            with st.expander("Repeat Loads"):
                repeat_count = st.number_input(
                    "Number of Repeated Loads",
                    min_value=1,
                    max_value=10,
                    value=1
                )

                spacing_ft = st.number_input(
                    "Spacing (ft)",
                    min_value=0.0,
                    value=0.0,
                    step=0.5
                )

            if st.button(
                "Add",
                use_container_width=True
            ):

                if direction == "Angled":
                    st.warning(
                        "Angled loads are displayed as vertical loads "
                        "in this educational version."
                    )

                for repeat_index in range(int(repeat_count)):
                    repeated_position = (
                        position_ft
                        + repeat_index * spacing_ft
                    )

                    if repeated_position <= st.session_state.L_ft:
                        st.session_state.point_loads.append(
                            {
                                "direction": (
                                    "Up"
                                    if direction == "Up"
                                    else "Down"
                                ),
                                "position_ft": repeated_position,
                                "magnitude_kip": magnitude_kip,
                                "load_case": load_case,
                            }
                        )

                st.success("Point load added.")

            if st.session_state.point_loads:
                st.markdown("#### Current Point Loads")

                for i, load in enumerate(
                    st.session_state.point_loads,
                    start=1
                ):
                    st.write(
                        f"P{i}: {load['magnitude_kip']:.2f} kip "
                        f"{load['direction'].lower()} at "
                        f"{load['position_ft']:.2f} ft"
                    )

                if st.button("Clear Point Loads"):
                    st.session_state.point_loads = []
                    st.rerun()

        # -------------------------------------------------
        # APPLIED MOMENTS
        # -------------------------------------------------
        elif st.session_state.panel == "moments":

            st.markdown(
                '<div class="panel-title">Direction</div>',
                unsafe_allow_html=True
            )

            direction = st.radio(
                "Moment Direction",
                ["Counterclockwise", "Clockwise"],
                horizontal=True,
                label_visibility="collapsed"
            )

            position_ft = st.number_input(
                "Position",
                min_value=0.0,
                max_value=float(st.session_state.L_ft),
                value=min(
                    8.0,
                    float(st.session_state.L_ft)
                ),
                step=0.5
            )

            magnitude_kipft = st.number_input(
                "Magnitude",
                min_value=0.01,
                value=10.0,
                step=1.0
            )

            load_case = st.selectbox(
                "Load Case",
                ["Dead Load", "Live Load", "Other"],
                key="moment_load_case"
            )

            if st.button(
                "Add",
                use_container_width=True,
                key="add_moment"
            ):

                st.session_state.moments.append(
                    {
                        "direction": direction,
                        "position_ft": position_ft,
                        "magnitude_kipft": magnitude_kipft,
                        "load_case": load_case,
                    }
                )

                st.success("Applied moment added.")

            if st.session_state.moments:
                st.markdown("#### Current Moments")

                for i, moment in enumerate(
                    st.session_state.moments,
                    start=1
                ):
                    st.write(
                        f"M{i}: {moment['magnitude_kipft']:.2f} kip-ft, "
                        f"{moment['direction']} at "
                        f"{moment['position_ft']:.2f} ft"
                    )

                if st.button("Clear Moments"):
                    st.session_state.moments = []
                    st.rerun()

        # -------------------------------------------------
        # DISTRIBUTED LOADS
        # -------------------------------------------------
        elif st.session_state.panel == "distributed_loads":

            st.markdown(
                '<div class="panel-title">Direction</div>',
                unsafe_allow_html=True
            )

            direction = st.radio(
                "Distributed Load Direction",
                ["Down", "Up"],
                horizontal=True,
                label_visibility="collapsed"
            )

            start_ft = st.number_input(
                "Start Position",
                min_value=0.0,
                max_value=float(st.session_state.L_ft),
                value=0.0,
                step=0.5
            )

            end_ft = st.number_input(
                "End Position",
                min_value=start_ft,
                max_value=float(st.session_state.L_ft),
                value=float(st.session_state.L_ft),
                step=0.5
            )

            start_mag = st.number_input(
                "Start Magnitude (kip/ft)",
                min_value=0.0,
                value=1.0,
                step=0.1
            )

            end_mag = st.number_input(
                "End Magnitude (kip/ft)",
                min_value=0.0,
                value=1.0,
                step=0.1
            )

            load_case = st.selectbox(
                "Load Case",
                ["Dead Load", "Live Load", "Other"],
                key="udl_load_case"
            )

            if st.button(
                "Add",
                use_container_width=True,
                key="add_udl"
            ):

                if end_ft <= start_ft:
                    st.error(
                        "End position must be greater than start position."
                    )
                else:
                    st.session_state.distributed_loads.append(
                        {
                            "direction": direction,
                            "start_ft": start_ft,
                            "end_ft": end_ft,
                            "start_mag": start_mag,
                            "end_mag": end_mag,
                            "load_case": load_case,
                        }
                    )

                    st.success("Distributed load added.")

            if st.session_state.distributed_loads:
                st.markdown("#### Current Distributed Loads")

                for i, load in enumerate(
                    st.session_state.distributed_loads,
                    start=1
                ):
                    st.write(
                        f"w{i}: {load['start_mag']:.2f} to "
                        f"{load['end_mag']:.2f} kip/ft from "
                        f"{load['start_ft']:.2f} to "
                        f"{load['end_ft']:.2f} ft"
                    )

                if st.button("Clear Distributed Loads"):
                    st.session_state.distributed_loads = []
                    st.rerun()

        # -------------------------------------------------
        # LOAD COMBINATIONS
        # -------------------------------------------------
        elif st.session_state.panel == "load_combinations":

            st.markdown(
                '<div class="panel-title">Load Combinations</div>',
                unsafe_allow_html=True
            )

            st.info(
                "Load combinations are reserved for future development."
            )


# =========================================================
# MAIN HEADER
# =========================================================
header_col1, header_col2, header_col3 = st.columns([5, 1, 1])

with header_col1:
    st.title("🏗️ Interactive Beam Analysis")

with header_col2:
    if st.button("⚙️ Settings", use_container_width=True):
        settings_dialog()

with header_col3:
    if st.button("📐 Section", use_container_width=True):
        section_builder()

st.markdown(
    """
    This educational application helps students understand how a beam
    responds to loads. It calculates support reactions, shear force,
    bending moment, stress, and deflection, then displays the results
    with interactive diagrams.
    """
)

with st.expander(
    "❓ Help, Instructions, and Frequently Asked Questions",
    expanded=False
):

    help_tab1, help_tab2, help_tab3 = st.tabs(
        ["How to Use", "Beam Basics", "FAQ & Contact"]
    )

    with help_tab1:
        st.markdown(
            """
            1. Select **Beam** and enter the beam length.
            2. Select **Supports** and choose the support types.
            3. Select **Section** and enter Iz and E or open Section Builder.
            4. Add point loads, applied moments, or distributed loads.
            5. Review the beam model and engineering diagrams.
            6. Open the Step-by-Step tab to see the equations.
            """
        )

        st.info(
            "Recommended first example: 16-ft beam, pinned support at A, "
            "roller support at B, two 5-kip loads at 4 ft and 8 ft, "
            "Iz = 2730 in⁴, E = 29000 ksi."
        )

    with help_tab2:
        st.markdown(
            """
            - **Reaction Force:** Force created by a support.
            - **Shear Force:** Internal force that tends to slide one beam segment.
            - **Bending Moment:** Internal effect that causes bending.
            - **Deflection:** Vertical movement of the beam.
            - **Utilization Ratio:** Actual stress divided by allowable stress.
            """
        )

    with help_tab3:
        with st.expander("What does PASS mean?"):
            st.write(
                "The calculated stress is less than or equal to the allowable stress."
            )

        with st.expander("What does FAIL mean?"):
            st.write(
                "The calculated stress is greater than the allowable stress."
            )

        with st.expander("Can this app replace professional design?"):
            st.write(
                "No. This app is for education and simplified beam analysis."
            )

        st.write(
            "For questions or feedback, replace this text with your email."
        )


# =========================================================
# INPUT DATA
# =========================================================
L_ft = float(st.session_state.L_ft)
L_in = L_ft * 12.0

point_loads = st.session_state.point_loads
moments = st.session_state.moments
distributed_loads = st.session_state.distributed_loads

# =========================================================
# CALCULATIONS
# Main validated case: simply supported beam
# =========================================================
if (
    st.session_state.support_A != "Pinned"
    or st.session_state.support_B != "Roller"
):
    st.warning(
        "The main validated calculation case is Pinned at A and Roller at B. "
        "Other support selections are shown for interface demonstration."
    )

total_vertical_load = 0.0
moment_about_A = 0.0

# Point loads
for load in point_loads:

    sign = 1.0 if load["direction"] == "Down" else -1.0
    P = sign * load["magnitude_kip"]
    a = load["position_ft"]

    total_vertical_load += P
    moment_about_A += P * a

# Distributed loads converted to equivalent resultants
distributed_resultants = []

for load in distributed_loads:

    sign = 1.0 if load["direction"] == "Down" else -1.0

    a = load["start_ft"]
    b = load["end_ft"]

    w1 = sign * load["start_mag"]
    w2 = sign * load["end_mag"]

    length = b - a

    if length > 0:

        total_force = 0.5 * (w1 + w2) * length

        if abs(w1 + w2) > 1e-12:
            centroid_local = (
                length
                * (w1 + 2.0 * w2)
                / (3.0 * (w1 + w2))
            )
        else:
            centroid_local = length / 2.0

        centroid = a + centroid_local

        total_vertical_load += total_force
        moment_about_A += total_force * centroid

        distributed_resultants.append(
            {
                "a": a,
                "b": b,
                "w1": w1,
                "w2": w2,
                "total_force": total_force,
                "centroid": centroid,
            }
        )

# Applied moments
# Counterclockwise is positive in the global equilibrium equation.
total_applied_moment = 0.0

for applied_moment in moments:

    sign = (
        1.0
        if applied_moment["direction"] == "Counterclockwise"
        else -1.0
    )

    total_applied_moment += (
        sign
        * applied_moment["magnitude_kipft"]
    )

# Equilibrium:
# RB*L - sum(P*x) + sum(M_external) = 0
RB = (
    moment_about_A - total_applied_moment
) / L_ft if L_ft > 0 else 0.0

RA = total_vertical_load - RB

# Beam stations
x_ft = np.linspace(0.0, L_ft, 1200)

V = np.full_like(x_ft, RA)
M = RA * x_ft

# Point-load effects
for load in point_loads:

    sign = 1.0 if load["direction"] == "Down" else -1.0
    P = sign * load["magnitude_kip"]
    a = load["position_ft"]

    active = x_ft >= a

    V[active] -= P
    M[active] -= P * (x_ft[active] - a)

# Applied-moment effects
for applied_moment in moments:

    sign = (
        1.0
        if applied_moment["direction"] == "Counterclockwise"
        else -1.0
    )

    applied_value = (
        sign
        * applied_moment["magnitude_kipft"]
    )

    active = x_ft >= applied_moment["position_ft"]

    # Positive CCW external moment creates a downward jump
    # in the internal bending-moment diagram.
    M[active] -= applied_value

# Distributed-load effects
for load in distributed_resultants:

    a = load["a"]
    b = load["b"]
    w1 = load["w1"]
    w2 = load["w2"]
    full_length = b - a

    for index, x_value in enumerate(x_ft):

        if x_value <= a:
            continue

        effective_end = min(x_value, b)
        effective_length = effective_end - a

        if effective_length <= 0:
            continue

        local_w2 = (
            w1
            + (w2 - w1)
            * effective_length
            / full_length
        )

        effective_force = (
            0.5
            * (w1 + local_w2)
            * effective_length
        )

        if abs(w1 + local_w2) > 1e-12:
            centroid_local = (
                effective_length
                * (w1 + 2.0 * local_w2)
                / (3.0 * (w1 + local_w2))
            )
        else:
            centroid_local = effective_length / 2.0

        centroid = a + centroid_local

        V[index] -= effective_force

        M[index] -= (
            effective_force
            * (x_value - centroid)
        )

# Maximum results
max_shear = float(np.max(np.abs(V)))
max_moment_kipft = float(np.max(np.abs(M)))

max_moment_index = int(np.argmax(np.abs(M)))
max_moment_location_ft = float(
    x_ft[max_moment_index]
)

# Deflection using numerical integration
M_kipin = M * 12.0
x_in = x_ft * 12.0

EI = st.session_state.E * st.session_state.I

if EI > 0:

    curvature = M_kipin / EI

    dx = x_in[1] - x_in[0]

    theta = np.zeros_like(x_in)
    deflection = np.zeros_like(x_in)

    theta[1:] = np.cumsum(
        0.5
        * (curvature[1:] + curvature[:-1])
        * dx
    )

    deflection[1:] = np.cumsum(
        0.5
        * (theta[1:] + theta[:-1])
        * dx
    )

    # Enforce zero deflection at both simple supports.
    deflection -= (
        deflection[-1]
        * x_in
        / L_in
    )

else:
    deflection = np.zeros_like(x_in)

max_deflection = float(
    np.max(np.abs(deflection))
)

deflection_limit = L_in / 360.0

# Approximate bending stress using a user-defined section depth.
# A simple educational default is used for section modulus.
default_depth_in = 16.0
section_modulus = (
    st.session_state.I
    / (default_depth_in / 2.0)
)

max_moment_kipin = max_moment_kipft * 12.0

sigma_max = (
    max_moment_kipin
    / section_modulus
    if section_modulus > 0
    else 0.0
)

sigma_allow = (
    st.session_state.Fy
    / st.session_state.FOS
)

utilization_ratio = (
    sigma_max
    / sigma_allow
    if sigma_allow > 0
    else 0.0
)

# =========================================================
# UNIT DISPLAY CONVERSIONS
# =========================================================
if st.session_state.force_unit == "lb":
    displayed_RA = RA * 1000.0
    displayed_RB = RB * 1000.0
    displayed_shear = max_shear * 1000.0
    displayed_force_unit = "lb"
else:
    displayed_RA = RA
    displayed_RB = RB
    displayed_shear = max_shear
    displayed_force_unit = "kip"

if st.session_state.moment_unit == "kip-in":
    displayed_moment = max_moment_kipft * 12.0
    displayed_moment_unit = "kip-in"
else:
    displayed_moment = max_moment_kipft
    displayed_moment_unit = "kip-ft"

if st.session_state.stress_unit == "psi":
    displayed_sigma_max = sigma_max * 1000.0
    displayed_sigma_allow = sigma_allow * 1000.0
    displayed_stress_unit = "psi"
else:
    displayed_sigma_max = sigma_max
    displayed_sigma_allow = sigma_allow
    displayed_stress_unit = "ksi"

# =========================================================
# SUMMARY
# =========================================================
metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric(
    "Reaction R_A",
    f"{displayed_RA:.2f} {displayed_force_unit}"
)

metric2.metric(
    "Reaction R_B",
    f"{displayed_RB:.2f} {displayed_force_unit}"
)

metric3.metric(
    "Maximum Shear",
    f"{displayed_shear:.2f} {displayed_force_unit}"
)

metric4.metric(
    "Maximum Deflection",
    f"{max_deflection:.4f} in"
)

st.caption(
    f"Maximum bending moment = {displayed_moment:.2f} "
    f"{displayed_moment_unit} at x = "
    f"{max_moment_location_ft:.2f} ft from A."
)

# =========================================================
# BEAM MODEL
# =========================================================
st.subheader("Beam Model")

fig_beam = go.Figure()

fig_beam.add_trace(
    go.Scatter(
        x=[0, L_ft],
        y=[0, 0],
        mode="lines",
        line=dict(
            color="#37474F",
            width=10
        ),
        showlegend=False
    )
)

# Support A
if st.session_state.support_A != "Free":
    symbol_A = (
        "circle"
        if st.session_state.support_A == "Roller"
        else "triangle-up"
    )

    fig_beam.add_trace(
        go.Scatter(
            x=[0],
            y=[-0.20],
            mode="markers",
            marker=dict(
                symbol=symbol_A,
                size=22
            ),
            showlegend=False
        )
    )

# Support B
if st.session_state.support_B != "Free":
    symbol_B = (
        "circle"
        if st.session_state.support_B == "Roller"
        else "triangle-up"
    )

    fig_beam.add_trace(
        go.Scatter(
            x=[L_ft],
            y=[-0.20],
            mode="markers",
            marker=dict(
                symbol=symbol_B,
                size=22
            ),
            showlegend=False
        )
    )

# Point loads
for i, load in enumerate(
    point_loads,
    start=1
):

    arrow_y = (
        0.95
        if load["direction"] == "Down"
        else -0.95
    )

    fig_beam.add_annotation(
        x=load["position_ft"],
        y=0,
        ax=load["position_ft"],
        ay=arrow_y,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        text=(
            f"P{i} = "
            f"{load['magnitude_kip']:.2f} kip"
        ),
        showarrow=True,
        arrowhead=2,
        arrowwidth=2.5,
        arrowcolor="#D32F2F"
    )

# Applied moments
for i, applied_moment in enumerate(
    moments,
    start=1
):

    moment_symbol = (
        "↺"
        if applied_moment["direction"] == "Counterclockwise"
        else "↻"
    )

    fig_beam.add_annotation(
        x=applied_moment["position_ft"],
        y=0.55,
        text=(
            f"{moment_symbol} M{i} = "
            f"{applied_moment['magnitude_kipft']:.2f} kip-ft"
        ),
        showarrow=False,
        font=dict(
            color="#7B1FA2",
            size=13
        )
    )

# Distributed loads
for i, load in enumerate(
    distributed_loads,
    start=1
):

    positions = np.linspace(
        load["start_ft"],
        load["end_ft"],
        9
    )

    top_y = (
        0.70
        if load["direction"] == "Down"
        else -0.70
    )

    fig_beam.add_trace(
        go.Scatter(
            x=[
                load["start_ft"],
                load["end_ft"]
            ],
            y=[top_y, top_y],
            mode="lines",
            line=dict(
                color="#F57C00",
                width=2
            ),
            showlegend=False
        )
    )

    for position in positions:
        fig_beam.add_annotation(
            x=position,
            y=0,
            ax=position,
            ay=top_y,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            text="",
            showarrow=True,
            arrowhead=2,
            arrowwidth=1.5,
            arrowcolor="#F57C00"
        )

    fig_beam.add_annotation(
        x=(
            load["start_ft"]
            + load["end_ft"]
        ) / 2.0,
        y=top_y + 0.18,
        text=(
            f"w{i}: {load['start_mag']:.2f} → "
            f"{load['end_mag']:.2f} kip/ft"
        ),
        showarrow=False,
        font=dict(
            color="#E65100",
            size=12
        )
    )

fig_beam.update_layout(
    height=360,
    template="plotly_white",
    showlegend=False,
    margin=dict(
        l=20,
        r=20,
        t=20,
        b=20
    )
)

fig_beam.update_xaxes(
    title="Beam Position (ft)",
    range=[
        -0.05 * L_ft,
        1.05 * L_ft
    ],
    showgrid=False
)

fig_beam.update_yaxes(
    visible=False,
    range=[-1.2, 1.3]
)

st.plotly_chart(
    fig_beam,
    use_container_width=True
)

# =========================================================
# RESULTS
# =========================================================
result_tab1, result_tab2, result_tab3, result_tab4 = st.tabs(
    [
        "Reactions",
        "Shear & Moment",
        "Deflection",
        "Step-by-Step",
    ]
)

with result_tab1:

    st.write(f"Reaction at A = **{RA:.3f} kip**")
    st.write(f"Reaction at B = **{RB:.3f} kip**")

    st.write(
        f"Total vertical load = "
        f"**{total_vertical_load:.3f} kip**"
    )

    st.write(
        f"Total applied moment = "
        f"**{total_applied_moment:.3f} kip-ft**"
    )

with result_tab2:

    fig_results = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=(
            "Shear Force Diagram",
            "Bending Moment Diagram",
        )
    )

    fig_results.add_trace(
        go.Scatter(
            x=x_ft,
            y=V,
            mode="lines",
            fill="tozeroy",
            line=dict(
                color="#1E88E5",
                width=2
            )
        ),
        row=1,
        col=1
    )

    fig_results.add_trace(
        go.Scatter(
            x=x_ft,
            y=M,
            mode="lines",
            fill="tozeroy",
            line=dict(
                color="#E53935",
                width=2
            )
        ),
        row=2,
        col=1
    )

    fig_results.update_layout(
        height=650,
        template="plotly_white",
        showlegend=False
    )

    fig_results.update_yaxes(
        title_text="V (kip)",
        row=1,
        col=1
    )

    fig_results.update_yaxes(
        title_text="M (kip-ft)",
        row=2,
        col=1
    )

    fig_results.update_xaxes(
        title_text="x (ft)",
        row=2,
        col=1
    )

    st.plotly_chart(
        fig_results,
        use_container_width=True
    )

with result_tab3:

    fig_deflection = go.Figure()

    fig_deflection.add_trace(
        go.Scatter(
            x=x_ft,
            y=deflection,
            mode="lines",
            fill="tozeroy",
            line=dict(
                color="#43A047",
                width=2
            )
        )
    )

    fig_deflection.update_layout(
        height=450,
        template="plotly_white",
        xaxis_title="x (ft)",
        yaxis_title="Deflection (in)",
        showlegend=False
    )

    st.plotly_chart(
        fig_deflection,
        use_container_width=True
    )

    if max_deflection <= deflection_limit:
        st.success(
            f"Deflection PASS ✅ — "
            f"{max_deflection:.4f} in ≤ "
            f"{deflection_limit:.4f} in"
        )
    else:
        st.error(
            f"Deflection FAIL ❌ — "
            f"{max_deflection:.4f} in > "
            f"{deflection_limit:.4f} in"
        )

with result_tab4:

    st.markdown("### Step 1 — Given Information")

    st.write(f"Beam length = {L_ft:.2f} ft")
    st.write(f"Section = {st.session_state.section_name}")
    st.write(f"Iz = {st.session_state.I:,.2f} in⁴")
    st.write(f"E = {st.session_state.E:,.2f} ksi")

    st.markdown("### Step 2 — Total Vertical Load")

    st.latex(
        r"\sum P = P_1 + P_2 + \cdots + W"
    )

    st.write(
        f"Total vertical load = "
        f"{total_vertical_load:.3f} kip"
    )

    st.markdown("### Step 3 — Moment Equilibrium")

    st.latex(r"\sum M_A = 0")

    st.latex(
        r"R_B L - \sum(P_i x_i) + \sum M_i = 0"
    )

    st.write(
        f"RB = {RB:.3f} kip"
    )

    st.markdown("### Step 4 — Vertical Equilibrium")

    st.latex(r"\sum F_y = 0")

    st.latex(
        r"R_A + R_B - \sum P = 0"
    )

    st.write(
        f"RA = {RA:.3f} kip"
    )

    st.markdown("### Step 5 — Internal Forces")

    st.write(
        f"Maximum shear = {max_shear:.3f} kip"
    )

    st.write(
        f"Maximum bending moment = "
        f"{max_moment_kipft:.3f} kip-ft"
    )

    st.write(
        f"Maximum moment location = "
        f"{max_moment_location_ft:.3f} ft from A"
    )

    st.markdown("### Step 6 — Bending Stress")

    st.latex(
        r"\sigma_{max}=\frac{M_{max}}{S}"
    )

    st.write(
        f"Maximum bending stress = "
        f"{sigma_max:.3f} ksi"
    )

    st.latex(
        r"\sigma_{allow}=\frac{F_y}{FOS}"
    )

    st.write(
        f"Allowable stress = "
        f"{sigma_allow:.3f} ksi"
    )

    st.markdown("### Step 7 — Utilization Ratio")

    st.latex(
        r"\text{Utilization}="
        r"\frac{\sigma_{max}}{\sigma_{allow}}"
    )

    st.write(
        f"Utilization ratio = "
        f"{utilization_ratio:.3f}"
    )

# =========================================================
# SAFETY CHECK
# =========================================================
st.subheader("🛡️ Safety Check")

safety_col1, safety_col2, safety_col3 = st.columns(3)

with safety_col1:

    if utilization_ratio <= 1.0:
        st.success(
            f"PASS ✅\n\n"
            f"Utilization = "
            f"{utilization_ratio:.1%}"
        )
    else:
        st.error(
            f"FAIL ❌\n\n"
            f"Utilization = "
            f"{utilization_ratio:.1%}"
        )

with safety_col2:

    st.write(
        f"Selected Section: "
        f"**{st.session_state.section_name}**"
    )

    st.write(
        f"Moment of Inertia: "
        f"**{st.session_state.I:,.2f} in⁴**"
    )

    st.write(
        f"Young's Modulus: "
        f"**{st.session_state.E:,.2f} ksi**"
    )

with safety_col3:

    st.write(
        f"Maximum Stress: "
        f"**{displayed_sigma_max:.2f} "
        f"{displayed_stress_unit}**"
    )

    st.write(
        f"Allowable Stress: "
        f"**{displayed_sigma_allow:.2f} "
        f"{displayed_stress_unit}**"
    )

    st.write(
        f"Deflection Limit: "
        f"**{deflection_limit:.4f} in**"
    )

# =========================================================
# DOWNLOAD RESULTS
# =========================================================
summary_csv = (
    "Result,Value,Unit\n"
    f"Reaction RA,{RA:.6f},kip\n"
    f"Reaction RB,{RB:.6f},kip\n"
    f"Maximum Shear,{max_shear:.6f},kip\n"
    f"Maximum Moment,{max_moment_kipft:.6f},kip-ft\n"
    f"Maximum Moment Location,{max_moment_location_ft:.6f},ft\n"
    f"Maximum Deflection,{max_deflection:.6f},in\n"
    f"Maximum Stress,{sigma_max:.6f},ksi\n"
    f"Allowable Stress,{sigma_allow:.6f},ksi\n"
    f"Utilization Ratio,{utilization_ratio:.6f},ratio\n"
)

st.download_button(
    "⬇️ Download Result Summary",
    data=summary_csv,
    file_name="beam_analysis_results.csv",
    mime="text/csv"
)

st.caption(
    "Educational model. The main validated calculation case is "
    "a simply supported beam with pinned and roller supports."
)
'''

output = Path("/mnt/data/final_beam_analysis_app.py")
output.write_text(code, encoding="utf-8")

compile(code, str(output), "exec")

print(f"Created: {output}")
print("Syntax check: passed")
print(f"Total lines: {len(code.splitlines())}")

