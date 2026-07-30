import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(page_title="Professional Beam Analysis (2D)", page_icon="🏗️", layout="wide")

st.title("🏗️ Interactive Beam Analysis & 2D Cross-Section Preview")
st.caption("Beam diagrams with Imperial units, unit conversion, interactive sidebar dimensions, deflection, and shear check")

# ================= SIDEBAR INPUTS (IMPERIAL) =================
with st.sidebar:
    st.header("⚙️ Beam & Load Parameters (Imperial)")
    
    len_unit = st.radio("Length Unit for Beam", ["Inches (in)", "Feet (ft)"], horizontal=True)
    if "Feet" in len_unit:
        L_ft = st.number_input("Beam Length L (ft)", min_value=0.1, value=16.0, step=1.0)
        L = L_ft * 12.0
    else:
        L = st.number_input("Beam Length L (in)", min_value=1.0, value=192.0, step=12.0)
    
    st.subheader("Force Unit Selection")
    force_unit = st.selectbox("Select Force Unit", ["kips (1 kip = 1,000 lbs)", "Pounds (lbs)"])
    
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

    st.subheader("2. Distributed Load (UDL)")
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

    st.subheader("3. Cross-Section & Dimensions (Inches)")
    section_shape = st.selectbox("Cross-Section Shape", ["Rectangular (Solid)", "Hollow Box / Tube", "I-Shape / Wide Flange"])
    
    if section_shape == "Rectangular (Solid)":
        b = st.slider("Width b (in)", min_value=1.0, max_value=24.0, value=8.0, step=0.5)
        h = st.slider("Total Height h (in)", min_value=1.0, max_value=36.0, value=16.0, step=0.5)
        I = b * (h**3) / 12.0
        S = I / (h / 2.0)
        A_web = b * h  # Dùng cho diện tích cắt xấp xỉ
        
    elif section_shape == "Hollow Box / Tube":
        b = st.slider("Outer Width b (in)", min_value=2.0, max_value=24.0, value=8.0, step=0.5)
        h = st.slider("Outer Height h (in)", min_value=2.0, max_value=36.0, value=16.0, step=0.5)
        t_wall = st.slider("Wall Thickness t (in)", min_value=0.1, max_value=3.0, value=0.5, step=0.1)
        b_in = max(0.1, b - 2 * t_wall)
        h_in = max(0.1, h - 2 * t_wall)
        I = (b * (h**3) - b_in * (h_in**3)) / 12.0
        S = I / (h / 2.0)
        A_web = 2 * t_wall * h  # Diện tích 2 bản bụng
        
    else: # I-Shape
        b = st.slider("Flange Width b (in)", min_value=2.0, max_value=24.0, value=8.0, step=0.5)
        h = st.slider("Total Height h (in)", min_value=2.0, max_value=36.0, value=16.0, step=0.5)
        t_web = st.slider("Web Thickness t_web (in)", min_value=0.1, max_value=2.0, value=0.4, step=0.1)
        t_flange = st.slider("Flange Thickness t_flange (in)", min_value=0.1, max_value=2.0, value=0.6, step=0.1)
        h_web = max(0.1, h - 2 * t_flange)
        I = (t_web * (h_web**3) / 12.0) + 2 * (b * (t_flange**3) / 12.0 + b * t_flange * ((h - t_flange)/2.0)**2)
        S = I / (h / 2.0)
        A_web = t_web * h_web  # Diện tích bản bụng chịu cắt chính

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

    st.subheader("4. Material Properties (ksi)")
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

# ================= CALCULATIONS =================
if enable_udl and x_end > x_start:
    udl_length = x_end - x_start
    udl_total_force = w_magnitude * udl_length
    udl_center = x_start + udl_length / 2.0
else:
    udl_total_force = 0.0
    udl_center = 0.0
    udl_length = 0.0

sum_moments_A = sum(p * x for p, x in zip(P, x_load)) + (udl_total_force * udl_center if enable_udl else 0.0)
RB = sum_moments_A / L if L > 0 else 0.0
total_downward = sum(P) + (udl_total_force if enable_udl else 0.0)
RA = total_downward - RB

x = np.linspace(0, L, 1000)
V = np.full_like(x, RA)
M = RA * x

for load, loc in zip(P, x_load):
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

max_v = np.max(np.abs(V)) if len(V) > 0 else 0.0
max_m = np.max(np.abs(M)) if len(M) > 0 else 0.0
max_m_kipft = max_m / 12.0
max_m_loc = x[np.argmax(np.abs(M))] if len(M) > 0 else 0.0

# Tính độ võng xấp xỉ bằng phương pháp tích phân số đơn giản cho dầm đơn giản
# (Giả lập độ cong v''(x) = M(x) / (E * I))
dx = L / 999.0
EI = E_modulus * I
if EI > 0:
    # Tích phân kép Moment để tính độ võng v(x)
    curvature = M / EI
    theta = np.cumsum(curvature) * dx
    # Điều kiện biên: độ võng bằng 0 tại x = 0 và x = L
    theta -= theta[-1] * (x / L) # Hiệu chỉnh góc xoay
    v_deflection = np.cumsum(theta) * dx
    v_deflection -= v_deflection[0] * (1 - x/L) + v_deflection[-1] * (x/L)
    max_deflection = np.max(np.abs(v_deflection))
else:
    v_deflection = np.zeros_like(x)
    max_deflection = 0.0

sigma_max = max_m / S if S > 0 else 0.0
tau_max = max_v / A_web if A_web > 0 else 0.0
sigma_allow = yield_strength / factor_of_safety if factor_of_safety > 0 else 1.0
tau_allow = (0.577 * yield_strength) / factor_of_safety # Tiêu chuẩn von Mises cho ứng suất cắt cho phép
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

st.divider()

# ================= 1. 2D PLOTS (BEAM SCHEMATIC, SFD, BMD & DEFLECTION) =================
fig = make_subplots(
    rows=4, cols=1, 
    shared_xaxes=True,
    vertical_spacing=0.06,
    subplot_titles=(
        f"1. Beam Schematic ({theme_name}) & Active Loads", 
        f"2. Shear Force Diagram (SFD)", 
        f"3. Bending Moment Diagram (BMD) - Max: {max_m_kipft:.2f} kip-ft",
        f"4. Deflection Curve (Elastic Line) - Max: {max_deflection:.4f} in"
    )
)

# 1. Beam Schematic
fig.add_trace(go.Scatter(
    x=[0, L], y=[0, 0], mode='lines+markers', 
    line=dict(color=beam_color, width=8), 
    marker=dict(size=10, color=beam_color),
    showlegend=False
), row=1, col=1)

fig.add_trace(go.Scatter(x=[0], y=[-0.3], mode='markers', marker=dict(symbol='triangle-up', size=18, color='#D32F2F'), showlegend=False), row=1, col=1)
fig.add_trace(go.Scatter(x=[L], y=[-0.3], mode='markers', marker=dict(symbol='triangle-up', size=18, color='#D32F2F'), showlegend=False), row=1, col=1)

for i, (p_val, x_val) in enumerate(zip(P, x_load)):
    p_label_text = f"P{i+1}={p_val*1000:.0f} lbs" if "Pounds" in force_unit else f"P{i+1}={p_val} kips"
    fig.add_annotation(
        x=x_val, y=0, ax=x_val, ay=1.0,
        xref='x1', yref='y1', axref='x1', ayref='y1',
        text=p_label_text, showarrow=True,
        arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='darkblue',
        font=dict(color='darkblue', size=11, family="Arial Black")
    )

if enable_udl and udl_length > 0:
    fig.add_trace(go.Scatter(
        x=[x_start, x_end], y=[0.3, 0.3], mode='lines',
        line=dict(color='#FF8F00', width=6),
        name='UDL', showlegend=False
    ), row=1, col=1)
    
    w_label_text = f"w = {w_magnitude*1000:.1f} lbs/in" if "Pounds" in force_unit else f"w = {w_magnitude} kips/in"
    fig.add_annotation(
        x=(x_start + x_end)/2, y=0.5,
        text=w_label_text,
        showarrow=False,
        font=dict(color='#E65100', size=12, family="Arial Black")
    )

# 2. Shear Force Diagram
V_plot = V * 1000.0 if "Pounds" in force_unit else V
v_unit_label = "Shear V (lbs)" if "Pounds" in force_unit else "Shear V (kips)"
fig.add_trace(go.Scatter(
    x=x, y=V_plot, mode='lines', fill='tozeroy', 
    line=dict(color='#1E88E5', width=2), name='Shear',
    hovertemplate='Position x: %{x:.1f} in<br>Shear V: %{y:.2f}<extra></extra>'
), row=2, col=1)

# 3. Bending Moment Diagram
fig.add_trace(go.Scatter(
    x=x, y=M/12.0, mode='lines', fill='tozeroy', 
    line=dict(color='#E53935', width=2), name='Moment',
    hovertemplate='Position x: %{x:.1f} in<br>Moment M: %{y:.2f} kip-ft<extra></extra>'
), row=3, col=1)

# 4. Deflection Curve
fig.add_trace(go.Scatter(
    x=x, y=v_deflection, mode='lines', fill='tozeroy',
    line=dict(color='#43A047', width=2), name='Deflection',
    hovertemplate='Position x: %{x:.1f} in<br>Deflection: %{y:.4f} in<extra></extra>'
), row=4, col=1)

for x_val in x_load:
    for r in [1, 2, 3, 4]:
        fig.add_vline(x=x_val, line_width=1, line_dash="dash", line_color="gray", opacity=0.7, row=r, col=1)

fig.update_layout(height=860, showlegend=False, hovermode="x unified", template="plotly_white")
fig.update_yaxes(visible=False, row=1, col=1)
fig.update_yaxes(title_text=v_unit_label, row=2, col=1)
fig.update_yaxes(title_text="Moment (kip-ft)", row=3, col=1)
fig.update_yaxes(title_text="Deflection (in)", row=4, col=1)
fig.update_xaxes(title_text="Beam Position x (in)", row=4, col=1)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ================= 2. SAFETY CHECK & PROPERTIES =================
st.subheader("🛡️ Safety Check & Properties")
col_st1, col_st2, col_st3 = st.columns(3)

with col_st1:
    if utilization_ratio <= 1.0:
        st.success(f"### PASS ✅\n**Bending Utilization:** {utilization_ratio:.1%}")
    else:
        st.error(f"### FAIL ❌\n**Bending Utilization:** {utilization_ratio:.1%}")

with col_st2:
    st.write(f"- **Selected Material:** `{mat_name}` ({theme_name})")
    st.write(f"- **Section Shape:** `{section_shape}`")
    st.write(f"- **Moment of Inertia I:** `{I:,.1f} in^4`")

with col_st3:
    st.write(
        f"- **Max Bending Stress ($\\sigma_{{max}}$):** "
        f"`{sigma_max:.2f} ksi` (Allowable: `{sigma_allow:.2f} ksi`)"
    )
    st.write(
        f"- **Max Shear Stress ($\\tau_{{max}}$):** "
        f"`{tau_max:.3f} ksi` (Allowable: `{tau_allow:.2f} ksi`)"
    )
    st.write(
        f"- **Max Deflection:** `{max_deflection:.4f} in` "
        f"(Limit L/360: `{L/360:.2f} in`)"
    )
