import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(page_title="Professional Beam Analysis (2D)", page_icon="🏗️", layout="wide")

# Store settings and additional loads between Streamlit reruns.
if "moment_loads" not in st.session_state:
    st.session_state.moment_loads = []

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


# ================= SETTINGS DIALOG =================

@st.dialog("⚙️ Settings", width="large")
def open_settings():
    st.subheader("Unit System")

    st.selectbox(
        "Units",
        ["Imperial"],
        index=0,
        help="The current application uses imperial units internally."
    )

    st.session_state.display_length_unit = st.selectbox(
        "Length",
        ["Inches (in)", "Feet (ft)"],
        index=(
            0
            if st.session_state.display_length_unit == "Inches (in)"
            else 1
        )
    )

    st.session_state.display_force_unit = st.selectbox(
        "Force",
        ["Pounds (lbs)", "kips (1 kip = 1,000 lbs)"],
        index=(
            0
            if st.session_state.display_force_unit == "Pounds (lbs)"
            else 1
        )
    )

    st.session_state.display_moment_unit = st.selectbox(
        "Moment",
        ["kip-in", "kip-ft"],
        index=(
            0
            if st.session_state.display_moment_unit == "kip-in"
            else 1
        )
    )

    st.session_state.display_stress_unit = st.selectbox(
        "Stress",
        ["psi", "ksi"],
        index=(
            0
            if st.session_state.display_stress_unit == "psi"
            else 1
        )
    )

    st.markdown(
        f"""
        **Section Length:** {st.session_state.display_length_unit}  
        **Material Strength:** {st.session_state.display_stress_unit}
        """
    )


# ================= SECTION BUILDER DIALOG =================

@st.dialog("Create Custom Section", width="large")
def open_section_builder():
    custom_tab, properties_tab, library_tab = st.tabs(
        ["Custom Shapes", "Section Properties", "American Library"]
    )

    with custom_tab:
        st.subheader("Select a Section Shape")

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
            search_ok = not search_term or search_term.lower() in name.lower()
            category_ok = category == "All" or group == category
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
                            text-align:center;
                            min-height:110px;
                            background:#ffffff;
                        ">
                            <div style="font-size:44px;">{icon}</div>
                            <div style="font-size:13px;">{name}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if st.button(
                        "Select",
                        key=f"old_ui_section_{row_index}_{col_index}",
                        use_container_width=True
                    ):
                        st.session_state.selected_section_name = name
                        st.success(f"{name} selected.")

        st.info(
            f"Current selection: {st.session_state.selected_section_name}"
        )

    with properties_tab:
        st.subheader("Section Properties")

        st.session_state.custom_Iz = st.number_input(
            "Moment of Inertia (Iz)",
            min_value=0.01,
            value=float(st.session_state.custom_Iz),
            step=10.0
        )
        st.caption("Unit: in⁴")

        st.session_state.custom_E = st.number_input(
            "Young's Modulus (E)",
            min_value=1.0,
            value=float(st.session_state.custom_E),
            step=100.0
        )
        st.caption("Unit: ksi")

        st.markdown(
            "<div style='text-align:center;font-size:22px;font-weight:700;'>OR</div>",
            unsafe_allow_html=True
        )

        builder_b = st.number_input(
            "Rectangular Width b (in)",
            min_value=0.1,
            value=8.0,
            step=0.5
        )

        builder_h = st.number_input(
            "Rectangular Height h (in)",
            min_value=0.1,
            value=16.0,
            step=0.5
        )

        calculated_Iz = builder_b * builder_h**3 / 12.0

        st.latex(r"I_z=\frac{bh^3}{12}")
        st.write(f"Calculated Iz = {calculated_Iz:,.2f} in⁴")

        if st.button(
            "Use Calculated Iz",
            type="primary",
            use_container_width=True
        ):
            st.session_state.custom_Iz = calculated_Iz
            st.session_state.selected_section_name = "Rectangular"
            st.success("Calculated section properties saved.")

    with library_tab:
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
            "The full AISC database is not included in this educational version."
        )


# ================= MAIN HEADER =================

header_col1, header_col2, header_col3 = st.columns([5, 1, 1])

with header_col1:
    st.title("🏗️ Interactive Beam Analysis & Reaction Forces")

with header_col2:
    if st.button("⚙️ Settings", use_container_width=True):
        open_settings()

with header_col3:
    if st.button("📐 Section", use_container_width=True):
        open_section_builder()

st.markdown("""
This educational application helps students study how beams respond to loads.
It calculates support reactions, shear force, bending moment, stress, and deflection,
then displays the results using interactive diagrams.
""")

with st.expander("❓ Help, Instructions, and FAQ", expanded=False):
    help_tab1, help_tab2, help_tab3 = st.tabs(
        ["How to Use", "Beam Basics", "FAQ & Contact"]
    )

    with help_tab1:
        st.markdown("""
        1. Select the beam length and force units.
        2. Choose the support conditions.
        3. Add point loads, a moving load, or a distributed load.
        4. Select the cross section and material.
        5. Review the beam diagram, FBD, shear, moment, and deflection results.
        6. Open **Step-by-Step Calculations** to see the main equations.
        """)

        st.info(
            "Recommended first example: 16-ft beam, pinned support at A, "
            "roller support at B, two 5-kip loads at 4 ft and 8 ft, "
            "8 in × 16 in rectangular section, A36 steel, and FOS = 1.5."
        )

    with help_tab2:
        st.markdown("""
        - **Reaction Force:** Force created by a support.
        - **Shear Force:** Internal force that tends to slide one beam segment.
        - **Bending Moment:** Internal effect that causes bending.
        - **Bending Stress:** Stress caused by the bending moment.
        - **Deflection:** Vertical movement of the beam.
        - **Utilization Ratio:** Actual stress divided by allowable stress.
        """)

    with help_tab3:
        with st.expander("What does PASS mean?"):
            st.write("The calculated stress is less than or equal to the allowable stress.")

        with st.expander("What does FAIL mean?"):
            st.write("The calculated stress is greater than the allowable stress.")

        with st.expander("Why do the diagrams change when a load moves?"):
            st.write(
                "Changing the load position changes the reactions, shear force, "
                "bending moment, stress, and deflection."
            )

        with st.expander("Can this app replace professional design?"):
            st.write(
                "No. This app is for education and simplified beam analysis."
            )

        st.markdown("**Contact:** Replace this text with your email or class contact information.")

st.caption(
    "Educational beam-analysis model with interactive diagrams and safety checks."
)

# SIDEBAR INPUTS (IMPERIAL) 

with st.sidebar:
    st.header("⚙️ Beam & Load Parameters (Imperial)")

    len_unit = st.radio(
        "Length Unit for Beam",
        ["Inches (in)", "Feet (ft)"],
        index=(
            0
            if st.session_state.display_length_unit == "Inches (in)"
            else 1
        ),
        horizontal=True
    )

    st.session_state.display_length_unit = len_unit
    if "Feet" in len_unit:
        L_ft = st.number_input("Beam Length L (ft)", min_value=0.1, value=16.0, step=1.0)
        L = L_ft * 12.0
    else:
        L = st.number_input("Beam Length L (in)", min_value=1.0, value=192.0, step=12.0)

    st.subheader("Force Unit Selection")
    force_unit = st.selectbox(
        "Select Force Unit",
        ["kips (1 kip = 1,000 lbs)", "Pounds (lbs)"],
        index=(
            1
            if st.session_state.display_force_unit == "Pounds (lbs)"
            else 0
        )
    )

    st.session_state.display_force_unit = force_unit

    st.subheader("Support Configurations (Boundary Conditions)")
    support_options = ["Pinned (Hinged)", "Roller", "Fixed (Ngàm)", "Free (Tự do)"]

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        support_A = st.selectbox("Support A (Left)", support_options, index=0)
    with col_s2:
        support_B = st.selectbox("Support B (Right)", support_options, index=1)

    st.subheader("1. Point Loads")
    n_loads = st.number_input("Number of Point Loads", min_value=0, max_value=5, value=1)

    P, x_load = [], []
    for i in range(int(n_loads)):
        with st.expander(f"Load P{i+1}", expanded=True):
            if "Pounds" in force_unit:
                p_val_lb = st.number_input(f"Magnitude P{i+1} (lbs)", min_value=10.0, value=5000.0, step=100.0, key=f"p_{i}")
                p_val = p_val_lb / 1000.0
            else:
                p_val = st.number_input(f"Magnitude P{i+1} (kips)", min_value=0.01, value=5.0, step=0.5, key=f"p_{i}")

            if "Feet" in len_unit:
                x_val_ft = st.number_input(f"Position x{i+1} from A (ft)", min_value=0.0, max_value=float(L/12.0), value=4.0, key=f"x_{i}")
                x_val = x_val_ft * 12.0
            else:
                x_val = st.number_input(f"Position x{i+1} from A (in)", min_value=0.0, max_value=float(L), value=48.0, key=f"x_{i}")
            P.append(p_val)
            x_load.append(x_val)

    # Demo
    st.subheader("🚗 Moving Load Simulation")
    enable_walker = st.toggle("Enable Moving Load Simulation", value=True)

    if enable_walker:
        load_type = st.selectbox("Select Moving Load Type", [
            "🚶‍♂️ Walker / Pedestrian (~180 lbs)", 
            "🛒 Cart / Hand Truck (~500 lbs)", 
            "🚜 Forklift / Heavy Cart (~3,000 lbs)",
            "⚙️ Custom Moving Load"
        ])
        
        if "Walker" in load_type:
            default_wt_lb = 180.0
            icon_str = "🚶‍♂️"
        elif "Cart" in load_type and "Hand" in load_type:
            default_wt_lb = 500.0
            icon_str = "🛒"
        elif "Forklift" in load_type:
            default_wt_lb = 3000.0
            icon_str = "🚜"
        else:
            default_wt_lb = 1000.0
            icon_str = "⚙️"

        if "Pounds" in force_unit:
            walker_wt_lb = st.number_input("Moving Load Weight (lbs)", min_value=10.0, value=default_wt_lb, step=50.0)
            walker_load = walker_wt_lb / 1000.0
        else:
            walker_load = st.number_input("Moving Load Weight (kips)", min_value=0.01, value=default_wt_lb/1000.0, step=0.1)
            
        if "Feet" in len_unit:
            walker_pos_ft = st.slider("Position x_moving (ft)", min_value=0.0, max_value=float(L/12.0), value=float(L/24.0), step=0.5)
            walker_pos = walker_pos_ft * 12.0
        else:
            walker_pos = st.slider("Position x_moving (in)", min_value=0.0, max_value=float(L), value=float(L/2.0), step=1.0)
    else:
        walker_load = 0.0
        walker_pos = 0.0
        icon_str = "🚗"

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
    enable_udl = st.toggle("Enable Distributed Load (UDL)", value=False)

    if enable_udl:
        if "Pounds" in force_unit:
            w_mag_lb = st.number_input("Intensity w (lbs/in)", min_value=1.0, value=500.0, step=50.0)
            w_magnitude = w_mag_lb / 1000.0
        else:
            w_magnitude = st.number_input("Intensity w (kips/in)", min_value=0.001, value=0.5, step=0.1)

        col_u1, col_u2 = st.columns(2)
        with col_u1:
            x_start = st.number_input("Start x1 (in)", min_value=0.0, max_value=float(L), value=0.0)
        with col_u2:
            x_end = st.number_input("End x2 (in)", min_value=0.0, max_value=float(L), value=float(L))
    else:
        w_magnitude = 0.0
        x_start, x_end = 0.0, 0.0

    st.subheader("4. Cross-Section & Dimensions (Inches)")

    if st.button(
        "📐 Launch Section Builder",
        use_container_width=True,
        key="old_interface_section_builder"
    ):
        open_section_builder()

    st.caption(
        f"Builder selection: {st.session_state.selected_section_name}"
    )
    section_shape = st.selectbox("Cross-Section Shape", ["Rectangular (Solid)", "Hollow Box / Tube", "I-Shape / Wide Flange"])

    if section_shape == "Rectangular (Solid)":
        b = st.slider("Width b (in)", min_value=1.0, max_value=24.0, value=8.0, step=0.5)
        h = st.slider("Total Height h (in)", min_value=1.0, max_value=36.0, value=16.0, step=0.5)
        I = b * (h**3) / 12.0
        S = I / (h / 2.0)
        A_web = b * h
        
    elif section_shape == "Hollow Box / Tube":
        b = st.slider("Outer Width b (in)", min_value=2.0, max_value=24.0, value=8.0, step=0.5)
        h = st.slider("Outer Height h (in)", min_value=2.0, max_value=36.0, value=16.0, step=0.5)
        t_wall = st.slider("Wall Thickness t (in)", min_value=0.1, max_value=3.0, value=0.5, step=0.1)
        b_in = max(0.1, b - 2 * t_wall)
        h_in = max(0.1, h - 2 * t_wall)
        I = (b * (h**3) - b_in * (h_in**3)) / 12.0
        S = I / (h / 2.0)
        A_web = 2 * t_wall * h
        
    else: # I-Shape
        b = st.slider("Flange Width b (in)", min_value=2.0, max_value=24.0, value=8.0, step=0.5)
        h = st.slider("Total Height h (in)", min_value=2.0, max_value=36.0, value=16.0, step=0.5)
        t_web = st.slider("Web Thickness t_web (in)", min_value=0.1, max_value=2.0, value=0.4, step=0.1)
        t_flange = st.slider("Flange Thickness t_flange (in)", min_value=0.1, max_value=2.0, value=0.6, step=0.1)
        h_web = max(0.1, h - 2 * t_flange)
        I = (t_web * (h_web**3) / 12.0) + 2 * (b * (t_flange**3) / 12.0 + b * t_flange * ((h - t_flange)/2.0)**2)
        S = I / (h / 2.0)
        A_web = t_web * h_web

    # ================= 2D CROSS-SECTION PROFILE VIEW =================
    st.markdown("---")
    st.subheader("📐 2D Cross-Section Preview")

    fig_2d = go.Figure()
    if section_shape == "Rectangular (Solid)":
        x_rect = [-b/2, b/2, b/2, -b/2, -b/2]
        y_rect = [-h/2, -h/2, h/2, h/2, -h/2]
        fig_2d.add_trace(go.Scatter(x=x_rect, y=y_rect, fill="toself", fillcolor="#37474F", line=dict(color="black", width=2)))
    elif section_shape == "Hollow Box / Tube":
        fig_2d.add_trace(go.Scatter(x=[-b/2, b/2, b/2, -b/2, -b/2], y=[-h/2, -h/2, h/2, h/2, -h/2], fill="toself", fillcolor="#37474F", line=dict(color="black", width=2), name="Outer"))
        fig_2d.add_trace(go.Scatter(x=[-b_in/2, b_in/2, b_in/2, -b_in/2, -b_in/2], y=[-h_in/2, -h_in/2, h_in/2, h_in/2, -h_in/2], fill="toself", fillcolor="white", line=dict(color="gray", width=2), name="Inner"))
    else: # I-Shape
        x_pts = [-b/2, b/2, b/2, t_web/2, t_web/2, b/2, b/2, -b/2, -b/2, -t_web/2, -t_web/2, -b/2, -b/2]
        y_pts = [-h/2, -h/2, -h/2 + t_flange, -h/2 + t_flange, h/2 - t_flange, h/2 - t_flange, h/2, h/2, h/2 - t_flange, h/2 - t_flange, -h/2 + t_flange, -h/2 + t_flange, -h/2]
        fig_2d.add_trace(go.Scatter(x=x_pts, y=y_pts, fill="toself", fillcolor="#37474F", line=dict(color="black", width=2)))

    fig_2d.update_layout(
        xaxis=dict(title="Width b (in)", range=[-max(b, 4)*0.7, max(b, 4)*0.7]),
        yaxis=dict(title="Height h (in)", range=[-max(h, 4)*0.7, max(h, 4)*0.7], scaleanchor="x", scaleratio=1),
        margin=dict(l=0, r=0, b=0, t=10),
        height=220,
        showlegend=False
    )
    st.plotly_chart(fig_2d, use_container_width=True)

    st.subheader("5. Material Properties (ksi)")
    material_category = st.selectbox("Material Category", ["Steel & Metals", "Wood & Timber", "Custom"])

    if material_category == "Steel & Metals":
        material_choice = st.selectbox("Select Steel Grade", ["A36 Steel (Fy = 36 ksi)", "A992 Steel (Fy = 50 ksi)", "Aluminum 6061-T6 (Fy = 35 ksi)"])
        if "A36" in material_choice:
            mat_name, yield_strength, E_modulus = "A36 Steel", 36.0, 29000.0
        elif "A992" in material_choice:
            mat_name, yield_strength, E_modulus = "A992 Steel", 50.0, 29000.0
        else:
            mat_name, yield_strength, E_modulus = "Aluminum 6061-T6", 35.0, 10000.0
            
    elif material_category == "Wood & Timber":
        material_choice = st.selectbox("Select Wood Grade", [
            "Douglas Fir-Larch No.1 (Fb = 1.5 ksi)",
            "Southern Pine No.1 (Fb = 1.7 ksi)",
            "Hem-Fir No.1/No.2 (Fb = 1.2 ksi)"
        ])
        if "Douglas Fir" in material_choice:
            mat_name, yield_strength, E_modulus = "Douglas Fir-Larch No.1", 1.5, 1600.0
        elif "Southern Pine" in material_choice:
            mat_name, yield_strength, E_modulus = "Southern Pine No.1", 1.7, 1800.0
        else:
            mat_name, yield_strength, E_modulus = "Hem-Fir No.1/No.2", 1.2, 1400.0
    else:
        mat_name = st.text_input("Custom Material Name", value="Custom")
        yield_strength = st.number_input("Allowable Stress (ksi)", value=20.0)
        E_modulus = st.number_input("E Modulus (ksi)", value=29000.0)
        
    factor_of_safety = st.number_input("Factor of Safety (FOS)", min_value=0.1, value=1.5, step=0.1)


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
    input_errors.append("The moving load must be located on the beam.")

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


# ================= MATERIAL THEME =================

if material_category == "Steel & Metals":
    beam_color = "#37474F"
    theme_name = "Steel Structure"
elif material_category == "Wood & Timber":
    beam_color = "#8D6E63"
    theme_name = "Timber Structure"
else:
    beam_color = "#7E57C2"
    theme_name = "Custom Material"

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

dx = L / 999.0
EI = E_modulus * I
if EI > 0:
    curvature = M / EI
    theta = np.cumsum(curvature) * dx
    if is_cantilever and "Fixed" in support_A:
        v_deflection = np.cumsum(theta) * dx
    elif is_cantilever and "Fixed" in support_B:
        theta_rev = theta - theta[-1]
        v_deflection = np.cumsum(theta_rev) * dx
        v_deflection -= v_deflection[-1]
    else:
        theta -= theta[-1] * (x / L)
        v_deflection = np.cumsum(theta) * dx
        v_deflection -= v_deflection[0] * (1 - x/L) + v_deflection[-1] * (x/L)
    max_deflection = np.max(np.abs(v_deflection))
else:
    v_deflection = np.zeros_like(x)
    max_deflection = 0.0

sigma_max = max_m / S if S > 0 else 0.0
tau_max = max_v / A_web if A_web > 0 else 0.0
sigma_allow = yield_strength / factor_of_safety if factor_of_safety > 0 else 1.0
tau_allow = (0.577 * yield_strength) / factor_of_safety
utilization_ratio = sigma_max / sigma_allow

# Summary Metrics Display

if "Pounds" in force_unit:
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
for i, (p_val, x_val) in enumerate(zip(P, x_load)):
    p_label = (f"P{i+1} = {p_val*1000:.0f} lbs" if "Pounds" in force_unit else f"P{i+1} = {p_val:.2f} kips")
    fig_problem.add_annotation(
        x=x_val, y=0,
        ax=x_val, ay=0.95,
        xref="x", yref="y",
        axref="x", ayref="y",
        text=p_label,
        showarrow=True,
        arrowhead=2,
        arrowsize=1.2,
        arrowwidth=2.5,
        arrowcolor="#D32F2F",
        font=dict(color="#D32F2F", size=11, family="Arial Black")
    )

# Moving load
if enable_walker:
    moving_label = (f"{icon_str} {walker_load*1000:.0f} lbs" if "Pounds" in force_unit else f"{icon_str} {walker_load:.2f} kips")
    fig_problem.add_annotation(
        x=walker_pos, y=0,
        ax=walker_pos, ay=1.15,
        xref="x", yref="y",
        axref="x", ayref="y",
        text=moving_label,
        showarrow=True,
        arrowhead=2,
        arrowsize=1.2,
        arrowwidth=2.5,
        arrowcolor="#2E7D32",
        font=dict(color="#2E7D32", size=11, family="Arial Black")
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
    w_label = (f"w = {w_magnitude*1000:.1f} lbs/in" if "Pounds" in force_unit else f"w = {w_magnitude:.3f} kips/in")
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
for i, (p_val, x_val) in enumerate(zip(P, x_load)):
    p_label_text = (f"P{i+1} = {p_val*1000:.0f} lbs" if "Pounds" in force_unit else f"P{i+1} = {p_val:.2f} kips")
    fig_fbd.add_annotation(
        x=x_val, y=0,
        ax=x_val, ay=0.75,
        xref="x", yref="y",
        axref="x", ayref="y",
        text=p_label_text,
        showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor="#1565C0",
        font=dict(color="#1565C0", size=11, family="Arial Black")
    )

# Moving load
if enable_walker:
    moving_text = (f"{icon_str} {walker_load*1000:.0f} lbs" if "Pounds" in force_unit else f"{icon_str} {walker_load:.2f} kips")
    fig_fbd.add_annotation(
        x=walker_pos, y=0,
        ax=walker_pos, ay=1.0,
        xref="x", yref="y",
        axref="x", ayref="y",
        text=moving_text,
        showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor="#2E7D32",
        font=dict(color="#2E7D32", size=11, family="Arial Black")
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
    w_label_text = (f"w = {w_magnitude*1000:.1f} lbs/in" if "Pounds" in force_unit else f"w = {w_magnitude:.3f} kips/in")
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

    for i, (load, location) in enumerate(zip(all_P, all_x)):
        st.write(
            f"Load P{i + 1} = {load:.2f} kips "
            f"at x{i + 1} = {location / 12.0:.2f} ft from A"
        )

    if enable_udl and udl_length > 0:
        st.write(
            f"Distributed Load, w = {w_magnitude:.3f} kips/in "
            f"from {x_start:.2f} in to {x_end:.2f} in"
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
            f"{w_magnitude:.3f} × {udl_length:.2f} "
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
        st.write(f"Moment of Inertia, I = {I:,.2f} in⁴")
        st.write(f"Section Modulus, S = {S:,.2f} in³")

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
        f"- Builder Iz: "
        f"{st.session_state.custom_Iz:,.1f} in⁴"
    )
    st.write(
        f"- Builder E: "
        f"{st.session_state.custom_E:,.1f} ksi"
    )
    st.write(f"- Section Shape: {section_shape}")
    st.write(f"- Moment of Inertia I: {I:,.1f} in^4")

with col_st3:
    st.write(f"- Max Bending Stress ($\\sigma_{{max}}$): {sigma_max:.2f} ksi (Allowable: {sigma_allow:.2f} ksi)")
    st.write(f"- Max Shear Stress ($\\tau_{{max}}$): {tau_max:.3f} ksi (Allowable: {tau_allow:.2f} ksi)")
    st.write(f"- Max Deflection: {max_deflection:.4f} in (Limit L/360: {L/360:.2f} in)")
