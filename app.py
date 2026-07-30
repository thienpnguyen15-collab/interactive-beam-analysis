
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.title("Interactive Beam Analysis and Material Check")

st.write(
    "This application analyzes a simply supported beam "
    "with multiple downward point loads."
)

L = st.number_input(
    "Beam length L (m)",
    min_value=0.1,
    value=6.0,
    step=0.1
)

n_loads = st.number_input(
    "Number of point loads",
    min_value=1,
    max_value=10,
    value=2,
    step=1
)

P = []
x_load = []

for i in range(int(n_loads)):
    st.subheader(f"Load {i + 1}")

    load = st.number_input(
        f"Load {i + 1} magnitude (kN)",
        min_value=0.01,
        value=10.0,
        key=f"load_{i}"
    )

    location = st.number_input(
        f"Load {i + 1} location from A (m)",
        min_value=0.0,
        max_value=float(L),
        value=min(float(L) / 2, float(L)),
        key=f"location_{i}"
    )

    P.append(load)
    x_load.append(location)

st.subheader("Rectangular Cross Section")

b = st.number_input(
    "Beam width b (mm)",
    min_value=1.0,
    value=200.0
)

h = st.number_input(
    "Beam height h (mm)",
    min_value=1.0,
    value=400.0
)

material_choice = st.selectbox(
    "Select material",
    ["A36 Steel", "Aluminum 6061-T6"]
)

factor_of_safety = st.number_input(
    "Factor of safety",
    min_value=0.1,
    value=1.5,
    step=0.1
)

if st.button("Analyze Beam"):

    RB = sum(
        load * location
        for load, location in zip(P, x_load)
    ) / L

    RA = sum(P) - RB

    x = np.linspace(0, L, 2001)

    V = np.full_like(x, RA)
    M = RA * x

    for load, location in zip(P, x_load):
        active = x >= location
        V[active] -= load
        M[active] -= load * (x[active] - location)

    max_shear = np.max(np.abs(V))
    max_moment = np.max(np.abs(M))
    max_index = np.argmax(np.abs(M))
    max_location = x[max_index]

    I = b * h**3 / 12
    S = I / (h / 2)

    if material_choice == "A36 Steel":
        E = 200000
        yield_strength = 250
    else:
        E = 68900
        yield_strength = 276

    sigma_max = max_moment * 1e6 / S
    allowable_stress = yield_strength / factor_of_safety
    utilization_ratio = sigma_max / allowable_stress

    st.subheader("Support Reactions")

    col1, col2 = st.columns(2)
    col1.metric("Reaction at A", f"{RA:.3f} kN")
    col2.metric("Reaction at B", f"{RB:.3f} kN")

    st.subheader("Internal Force Results")

    st.write(f"Maximum shear: {max_shear:.3f} kN")
    st.write(f"Maximum moment: {max_moment:.3f} kN·m")
    st.write(
        f"Maximum moment location: "
        f"{max_location:.3f} m from support A"
    )

    st.subheader("Material Check")

    st.write(f"Material: {material_choice}")
    st.write(f"Young's modulus: {E:.0f} MPa")
    st.write(f"Yield strength: {yield_strength:.3f} MPa")
    st.write(f"Moment of inertia: {I:.3e} mm⁴")
    st.write(f"Section modulus: {S:.3e} mm³")
    st.write(f"Maximum bending stress: {sigma_max:.3f} MPa")
    st.write(f"Allowable stress: {allowable_stress:.3f} MPa")
    st.write(f"Utilization ratio: {utilization_ratio:.3f}")

    if utilization_ratio <= 1:
        st.success("Material check: PASS")
    else:
        st.error("Material check: DOES NOT PASS")

    fig1, ax1 = plt.subplots()
    ax1.step(x, V, where="post")
    ax1.axhline(0)
    ax1.grid(True)
    ax1.set_xlabel("Position Along Beam (m)")
    ax1.set_ylabel("Shear Force (kN)")
    ax1.set_title("Shear Force Diagram")
    st.pyplot(fig1)

    fig2, ax2 = plt.subplots()
    ax2.plot(x, M)
    ax2.axhline(0)
    ax2.grid(True)
    ax2.set_xlabel("Position Along Beam (m)")
    ax2.set_ylabel("Bending Moment (kN·m)")
    ax2.set_title("Bending Moment Diagram")
    st.pyplot(fig2)
