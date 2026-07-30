import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Interactive Beam Analysis",
    layout="wide"
)

st.title("Interactive Beam Analysis and Material Check")

st.write(
    "This application analyzes a simply supported beam "
    "with multiple downward point loads."
)

# --------------------------------------------------
# 1. BEAM INFORMATION
# --------------------------------------------------

st.header("1. Beam Information")

L = st.number_input(
    "Beam length L (m)",
    min_value=0.10,
    value=6.00,
    step=0.10
)

num_loads = st.number_input(
    "Number of point loads",
    min_value=1,
    max_value=10,
    value=2,
    step=1
)

loads = []

for i in range(int(num_loads)):
    st.subheader(f"Load {i + 1}")

    col1, col2 = st.columns(2)

    with col1:
        magnitude = st.number_input(
            f"Load {i + 1} magnitude (kN)",
            min_value=0.01,
            value=10.00,
            step=0.50,
            key=f"magnitude_{i}"
        )

    with col2:
        default_location = min(
            L * (i + 1) / (int(num_loads) + 1),
            L
        )

        location = st.number_input(
            f"Load {i + 1} location from A (m)",
            min_value=0.00,
            max_value=float(L),
            value=float(default_location),
            step=0.10,
            key=f"location_{i}"
        )

    loads.append((magnitude, location))

# --------------------------------------------------
# 2. CROSS SECTION AND MATERIAL
# --------------------------------------------------

st.header("2. Cross Section and Material")

b = st.number_input(
    "Beam width b (mm)",
    min_value=1.00,
    value=200.00,
    step=10.00
)

h = st.number_input(
    "Beam height h (mm)",
    min_value=1.00,
    value=400.00,
    step=10.00
)

material = st.selectbox(
    "Select material",
    [
        "A36 Steel",
        "Aluminum 6061-T6",
        "Custom"
    ]
)

if material == "A36 Steel":
    youngs_modulus = 200000.0
    yield_strength = 250.0

elif material == "Aluminum 6061-T6":
    youngs_modulus = 68900.0
    yield_strength = 276.0

else:
    youngs_modulus = st.number_input(
        "Custom Young's modulus E (MPa)",
        min_value=1.00,
        value=100000.00
    )

    yield_strength = st.number_input(
        "Custom yield strength (MPa)",
        min_value=1.00,
        value=200.00
    )

fos = st.number_input(
    "Factor of safety",
    min_value=0.10,
    value=1.50,
    step=0.10
)

# --------------------------------------------------
# 3. ANALYSIS
# --------------------------------------------------

if st.button("Analyze Beam", type="primary"):

    load_magnitudes = np.array(
        [load[0] for load in loads],
        dtype=float
    )

    load_locations = np.array(
        [load[1] for load in loads],
        dtype=float
    )

    # Sort loads from left to right
    sort_index = np.argsort(load_locations)

    load_locations = load_locations[sort_index]
    load_magnitudes = load_magnitudes[sort_index]

    # --------------------------------------------------
    # SUPPORT REACTIONS
    # --------------------------------------------------

    total_load = np.sum(load_magnitudes)

    R_B = np.sum(
        load_magnitudes * load_locations
    ) / L

    R_A = total_load - R_B

    # --------------------------------------------------
    # EQUILIBRIUM CHECK
    # --------------------------------------------------

    force_error = abs(
        R_A + R_B - total_load
    )

    moment_error = abs(
        R_B * L
        - np.sum(load_magnitudes * load_locations)
    )

    tolerance = 1e-8

    equilibrium_pass = (
        force_error < tolerance
        and moment_error < tolerance
    )

    # --------------------------------------------------
    # SHEAR AND MOMENT
    # --------------------------------------------------

    x = np.linspace(0, L, 2001)

    V = np.full_like(x, R_A)
    M = R_A * x

    for magnitude, location in zip(
        load_magnitudes,
        load_locations
    ):
        active = x >= location

        V[active] -= magnitude

        M[active] -= (
            magnitude
            * (x[active] - location)
        )

    V[np.abs(V) < 1e-10] = 0
    M[np.abs(M) < 1e-10] = 0

    # Exact critical points:
    # supports and point-load locations
    critical_x = np.unique(
        np.concatenate(
            ([0], load_locations, [L])
        )
    )

    critical_M = R_A * critical_x

    for magnitude, location in zip(
        load_magnitudes,
        load_locations
    ):
        active = critical_x >= location

        critical_M[active] -= (
            magnitude
            * (critical_x[active] - location)
        )

    max_moment_index = np.argmax(
        np.abs(critical_M)
    )

    max_moment_signed = critical_M[
        max_moment_index
    ]

    max_moment = abs(max_moment_signed)

    max_moment_location = critical_x[
        max_moment_index
    ]

    max_shear = max(
        abs(R_A),
        abs(R_B),
        np.max(np.abs(V))
    )

    # --------------------------------------------------
    # CROSS-SECTION PROPERTIES
    # --------------------------------------------------

    I = b * h**3 / 12
    c = h / 2
    S = I / c

    # 1 kN·m = 1,000,000 N·mm
    max_moment_Nmm = max_moment * 1e6

    sigma_max = max_moment_Nmm / S

    allowable_stress = (
        yield_strength / fos
    )

    utilization_ratio = (
        sigma_max / allowable_stress
    )

    material_pass = utilization_ratio <= 1

    # --------------------------------------------------
    # RESULTS
    # --------------------------------------------------

    st.header("3. Analysis Results")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Reaction at A",
        f"{R_A:.3f} kN"
    )

    col2.metric(
        "Reaction at B",
        f"{R_B:.3f} kN"
    )

    col3.metric(
        "Total Load",
        f"{total_load:.3f} kN"
    )

    st.subheader("Internal Force Results")

    result_col1, result_col2, result_col3 = st.columns(3)

    result_col1.metric(
        "Maximum Shear",
        f"{max_shear:.3f} kN"
    )

    result_col2.metric(
        "Maximum Moment",
        f"{max_moment:.3f} kN·m"
    )

    result_col3.metric(
        "Maximum Moment Location",
        f"{max_moment_location:.3f} m"
    )

    st.subheader("Equilibrium Verification")

    st.write(
        f"Vertical-force error: "
        f"{force_error:.3e} kN"
    )

    st.write(
        f"Moment error about A: "
        f"{moment_error:.3e} kN·m"
    )

    if equilibrium_pass:
        st.success("Equilibrium check: PASS")
    else:
        st.error("Equilibrium check: FAIL")

    st.subheader("Material Check")

    st.write(f"Material: {material}")
    st.write(
        f"Young's modulus: "
        f"{youngs_modulus:.0f} MPa"
    )
    st.write(
        f"Yield strength: "
        f"{yield_strength:.3f} MPa"
    )
    st.write(
        f"Moment of inertia, I: "
        f"{I:.3e} mm⁴"
    )
    st.write(
        f"Section modulus, S: "
        f"{S:.3e} mm³"
    )
    st.write(
        f"Maximum bending stress: "
        f"{sigma_max:.3f} MPa"
    )
    st.write(
        f"Allowable stress: "
        f"{allowable_stress:.3f} MPa"
    )
    st.write(
        f"Utilization ratio: "
        f"{utilization_ratio:.3f}"
    )

    if material_pass:
        st.success("Material check: PASS")
    else:
        st.error("Material check: DOES NOT PASS")

    # --------------------------------------------------
    # BEAM LOADING DIAGRAM
    # --------------------------------------------------

    st.header("4. Diagrams")

    fig_beam, ax_beam = plt.subplots(
        figsize=(10, 3)
    )

    ax_beam.plot(
        [0, L],
        [0, 0],
        linewidth=5
    )

    ax_beam.plot(
        0,
        0,
        marker="^",
        markersize=12
    )

    ax_beam.plot(
        L,
        0,
        marker="^",
        markersize=12,
        markerfacecolor="white"
    )

    arrow_height = max(
        np.max(load_magnitudes) * 0.15,
        1
    )

    for magnitude, location in zip(
        load_magnitudes,
        load_locations
    ):
        ax_beam.annotate(
            "",
            xy=(location, 0),
            xytext=(location, arrow_height),
            arrowprops={
                "arrowstyle": "->",
                "linewidth": 2
            }
        )

        ax_beam.text(
            location,
            arrow_height * 1.1,
            f"{magnitude:.1f} kN",
            ha="center"
        )

    ax_beam.text(
        0,
        -arrow_height * 0.4,
        f"A: {R_A:.2f} kN",
        ha="left"
    )

    ax_beam.text(
        L,
        -arrow_height * 0.4,
        f"B: {R_B:.2f} kN",
        ha="right"
    )

    ax_beam.set_xlim(
        -0.05 * L,
        1.05 * L
    )

    ax_beam.set_ylim(
        -arrow_height,
        arrow_height * 1.6
    )

    ax_beam.set_xlabel(
        "Position Along Beam (m)"
    )

    ax_beam.set_title(
        "Beam Loading Diagram"
    )

    ax_beam.grid(True)
    ax_beam.set_yticks([])

    st.pyplot(fig_beam)
    plt.close(fig_beam)

    # --------------------------------------------------
    # SHEAR FORCE DIAGRAM
    # --------------------------------------------------

    fig_shear, ax_shear = plt.subplots(
        figsize=(10, 4)
    )

    ax_shear.step(
        x,
        V,
        where="post",
        linewidth=2
    )

    ax_shear.axhline(
        0,
        linewidth=1
    )

    ax_shear.set_xlim(0, L)

    ax_shear.set_xlabel(
        "Position Along Beam (m)"
    )

    ax_shear.set_ylabel(
        "Shear Force (kN)"
    )

    ax_shear.set_title(
        "Shear Force Diagram"
    )

    ax_shear.grid(True)

    st.pyplot(fig_shear)
    plt.close(fig_shear)

    # --------------------------------------------------
    # BENDING MOMENT DIAGRAM
    # --------------------------------------------------

    fig_moment, ax_moment = plt.subplots(
        figsize=(10, 4)
    )

    ax_moment.plot(
        x,
        M,
        linewidth=2
    )

    ax_moment.axhline(
        0,
        linewidth=1
    )

    ax_moment.plot(
        max_moment_location,
        max_moment_signed,
        marker="o"
    )

    ax_moment.annotate(
        f"Mmax = {max_moment:.2f} kN·m",
        xy=(
            max_moment_location,
            max_moment_signed
        ),
        xytext=(10, 10),
        textcoords="offset points"
    )

    ax_moment.set_xlim(0, L)

    ax_moment.set_xlabel(
        "Position Along Beam (m)"
    )

    ax_moment.set_ylabel(
        "Bending Moment (kN·m)"
    )

    ax_moment.set_title(
        "Bending Moment Diagram"
    )

    ax_moment.grid(True)

    st.pyplot(fig_moment)
    plt.close(fig_moment)

    # --------------------------------------------------
    # EDUCATIONAL SUMMARY
    # --------------------------------------------------

    st.header("5. Educational Summary")

    st.write(
        "- Support reactions are calculated using "
        "vertical-force and moment equilibrium."
    )

    st.write(
        "- The shear force changes suddenly at each "
        "point-load location."
    )

    st.write(
        "- The bending moment changes linearly between "
        "point loads."
    )

    st.write(
        "- Bending stress depends on the maximum moment "
        "and cross-section geometry."
    )

    st.write(
        "- Material selection changes the yield strength, "
        "allowable stress, and safety result."
    )

    st.info(
        "This is a simplified bending-stress check only. "
        "It does not check deflection, buckling, fatigue, "
        "connections, or detailed shear capacity."
    )
