import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Interactive Beam Analysis",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ Interactive Beam Analysis")
st.write(
    "Analyze a simply supported beam with multiple downward point loads."
)

# =========================================================
# USER INPUTS
# =========================================================
with st.sidebar:
    st.header("Beam Inputs")

    L_ft = st.number_input(
        "Beam Length, L (ft)",
        min_value=1.0,
        value=16.0,
        step=1.0
    )
    L = L_ft * 12.0  # inches

    n_loads = st.number_input(
        "Number of Point Loads",
        min_value=1,
        max_value=5,
        value=2,
        step=1
    )

    loads = []
    locations = []

    for i in range(int(n_loads)):
        st.subheader(f"Load P{i + 1}")

        load_kips = st.number_input(
            f"Magnitude P{i + 1} (kips)",
            min_value=0.01,
            value=5.0,
            step=0.5,
            key=f"load_{i}"
        )

        location_ft = st.number_input(
            f"Location x{i + 1} from A (ft)",
            min_value=0.0,
            max_value=float(L_ft),
            value=min(4.0 + 4.0 * i, float(L_ft)),
            step=0.5,
            key=f"location_{i}"
        )

        loads.append(load_kips)
        locations.append(location_ft * 12.0)

    st.header("Cross Section")

    b = st.number_input(
        "Width, b (in)",
        min_value=0.1,
        value=8.0,
        step=0.5
    )

    h = st.number_input(
        "Height, h (in)",
        min_value=0.1,
        value=16.0,
        step=0.5
    )

    st.header("Material")

    material = st.selectbox(
        "Material",
        [
            "A36 Steel",
            "A992 Steel",
            "Aluminum 6061-T6"
        ]
    )

    if material == "A36 Steel":
        Fy = 36.0
        E = 29000.0
    elif material == "A992 Steel":
        Fy = 50.0
        E = 29000.0
    else:
        Fy = 35.0
        E = 10000.0

    FOS = st.number_input(
        "Factor of Safety",
        min_value=1.0,
        value=1.5,
        step=0.1
    )

# =========================================================
# CALCULATIONS
# =========================================================
total_load = sum(loads)
moment_about_A = sum(P * x for P, x in zip(loads, locations))

RB = moment_about_A / L
RA = total_load - RB

x = np.linspace(0.0, L, 1000)

V = np.full_like(x, RA)
M = RA * x

for P, a in zip(loads, locations):
    active = x >= a
    V[active] -= P
    M[active] -= P * (x[active] - a)

max_shear = np.max(np.abs(V))
max_moment = np.max(np.abs(M))
max_moment_index = np.argmax(np.abs(M))
max_moment_location = x[max_moment_index]

I = b * h**3 / 12.0
S = b * h**2 / 6.0

sigma_max = max_moment / S
sigma_allowable = Fy / FOS
utilization = sigma_max / sigma_allowable

# Numerical integration for deflection
EI = E * I
curvature = M / EI

theta_raw = np.zeros_like(x)
deflection_raw = np.zeros_like(x)

theta_raw[1:] = np.cumsum(
    0.5 * (curvature[1:] + curvature[:-1]) * np.diff(x)
)

deflection_raw[1:] = np.cumsum(
    0.5 * (theta_raw[1:] + theta_raw[:-1]) * np.diff(x)
)

# Boundary condition: deflection = 0 at x = 0 and x = L
correction_slope = deflection_raw[-1] / L
deflection = deflection_raw - correction_slope * x

max_deflection = np.max(np.abs(deflection))
deflection_limit = L / 360.0

# =========================================================
# SUMMARY
# =========================================================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Reaction RA", f"{RA:.2f} kips")
col2.metric("Reaction RB", f"{RB:.2f} kips")
col3.metric("Maximum Moment", f"{max_moment / 12.0:.2f} kip-ft")
col4.metric("Maximum Deflection", f"{max_deflection:.4f} in")

# =========================================================
# PROBLEM DIAGRAM
# =========================================================
st.subheader("1. Beam and Loading Diagram")

fig_beam = go.Figure()

fig_beam.add_trace(
    go.Scatter(
        x=[0, L],
        y=[0, 0],
        mode="lines",
        line=dict(color="black", width=8),
        showlegend=False
    )
)

fig_beam.add_trace(
    go.Scatter(
        x=[0],
        y=[-0.2],
        mode="markers",
        marker=dict(symbol="triangle-up", size=22),
        showlegend=False
    )
)

fig_beam.add_trace(
    go.Scatter(
        x=[L],
        y=[-0.2],
        mode="markers",
        marker=dict(symbol="circle", size=18),
        showlegend=False
    )
)

fig_beam.add_annotation(
    x=0,
    y=-0.4,
    text="Pinned Support A",
    showarrow=False
)

fig_beam.add_annotation(
    x=L,
    y=-0.4,
    text="Roller Support B",
    showarrow=False
)

for i, (P, a) in enumerate(zip(loads, locations)):
    fig_beam.add_annotation(
        x=a,
        y=0,
        ax=a,
        ay=0.9,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        text=f"P{i + 1} = {P:.2f} kips",
        showarrow=True,
        arrowhead=2,
        arrowwidth=2
    )

fig_beam.update_layout(
    height=330,
    template="plotly_white",
    showlegend=False,
    margin=dict(l=20, r=20, t=30, b=20)
)

fig_beam.update_xaxes(
    title="Beam Position (in)",
    range=[-0.05 * L, 1.05 * L],
    showgrid=False
)

fig_beam.update_yaxes(
    visible=False,
    range=[-0.6, 1.1]
)

st.plotly_chart(fig_beam, use_container_width=True)

# =========================================================
# FREE BODY DIAGRAM
# =========================================================
st.subheader("2. Free Body Diagram")

fig_fbd = go.Figure()

fig_fbd.add_trace(
    go.Scatter(
        x=[0, L],
        y=[0, 0],
        mode="lines",
        line=dict(color="black", width=3),
        showlegend=False
    )
)

fig_fbd.add_annotation(
    x=0,
    y=0,
    ax=0,
    ay=-0.7,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    text=f"RA = {RA:.2f} kips",
    showarrow=True,
    arrowhead=2,
    arrowwidth=2
)

fig_fbd.add_annotation(
    x=L,
    y=0,
    ax=L,
    ay=-0.7,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    text=f"RB = {RB:.2f} kips",
    showarrow=True,
    arrowhead=2,
    arrowwidth=2
)

for i, (P, a) in enumerate(zip(loads, locations)):
    fig_fbd.add_annotation(
        x=a,
        y=0,
        ax=a,
        ay=0.8,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        text=f"P{i + 1} = {P:.2f} kips",
        showarrow=True,
        arrowhead=2,
        arrowwidth=2
    )

fig_fbd.update_layout(
    height=340,
    template="plotly_white",
    showlegend=False,
    margin=dict(l=20, r=20, t=30, b=20)
)

fig_fbd.update_xaxes(
    title="Beam Position (in)",
    range=[-0.05 * L, 1.05 * L],
    showgrid=False
)

fig_fbd.update_yaxes(
    visible=False,
    range=[-0.9, 1.0]
)

st.plotly_chart(fig_fbd, use_container_width=True)

# =========================================================
# ENGINEERING DIAGRAMS
# =========================================================
st.subheader("3. Shear, Moment, and Deflection Diagrams")

fig_results = make_subplots(
    rows=3,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.08,
    subplot_titles=(
        "Shear Force Diagram",
        "Bending Moment Diagram",
        "Deflection Curve"
    )
)

fig_results.add_trace(
    go.Scatter(
        x=x,
        y=V,
        mode="lines",
        fill="tozeroy",
        name="Shear"
    ),
    row=1,
    col=1
)

fig_results.add_trace(
    go.Scatter(
        x=x,
        y=M / 12.0,
        mode="lines",
        fill="tozeroy",
        name="Moment"
    ),
    row=2,
    col=1
)

fig_results.add_trace(
    go.Scatter(
        x=x,
        y=deflection,
        mode="lines",
        name="Deflection"
    ),
    row=3,
    col=1
)

fig_results.update_layout(
    height=720,
    template="plotly_white",
    showlegend=False,
    hovermode="x unified"
)

fig_results.update_yaxes(
    title_text="Shear (kips)",
    row=1,
    col=1
)

fig_results.update_yaxes(
    title_text="Moment (kip-ft)",
    row=2,
    col=1
)

fig_results.update_yaxes(
    title_text="Deflection (in)",
    row=3,
    col=1
)

fig_results.update_xaxes(
    title_text="Beam Position (in)",
    row=3,
    col=1
)

st.plotly_chart(fig_results, use_container_width=True)

# =========================================================
# CALCULATIONS AND SAFETY CHECK
# =========================================================
st.subheader("4. Calculation Summary")

st.latex(r"\sum M_A = 0")
st.write(
    f"RB = Σ(Px)/L = {RB:.2f} kips"
)

st.latex(r"\sum F_y = 0")
st.write(
    f"RA = ΣP - RB = {RA:.2f} kips"
)

st.latex(r"I=\frac{bh^3}{12}")
st.write(
    f"I = {I:,.2f} in⁴"
)

st.latex(r"S=\frac{bh^2}{6}")
st.write(
    f"S = {S:,.2f} in³"
)

st.latex(r"\sigma_{max}=\frac{M_{max}}{S}")
st.write(
    f"Maximum bending stress = {sigma_max:.2f} ksi"
)

st.latex(r"\sigma_{allowable}=\frac{F_y}{FOS}")
st.write(
    f"Allowable stress = {sigma_allowable:.2f} ksi"
)

st.write(
    f"Maximum moment occurs at x = "
    f"{max_moment_location / 12.0:.2f} ft from Support A."
)

col_a, col_b = st.columns(2)

with col_a:
    if utilization <= 1.0:
        st.success(
            f"PASS ✅\n\n"
            f"Bending utilization = {utilization:.1%}"
        )
    else:
        st.error(
            f"FAIL ❌\n\n"
            f"Bending utilization = {utilization:.1%}"
        )

with col_b:
    if max_deflection <= deflection_limit:
        st.success(
            f"DEFLECTION PASS ✅\n\n"
            f"{max_deflection:.4f} in ≤ {deflection_limit:.4f} in"
        )
    else:
        st.error(
            f"DEFLECTION FAIL ❌\n\n"
            f"{max_deflection:.4f} in > {deflection_limit:.4f} in"
        )

st.caption(
    "Educational model: simply supported beam, downward point loads, "
    "rectangular cross section, and linear-elastic behavior."
)
