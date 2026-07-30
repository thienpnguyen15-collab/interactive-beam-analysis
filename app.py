import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Beam Analysis & Material Check", layout="centered")

st.title("Interactive Beam Analysis and Material Check")
st.write("This application analyzes a simply supported beam with multiple downward point loads.")

# 1. Nhập thông số hình học của dầm
st.subheader("Beam Configuration")
L = st.number_input("Beam length L (m)", min_value=0.5, max_value=50.0, value=6.00, step=0.1)
num_loads = st.number_input("Number of point loads", min_value=1, max_value=5, value=2, step=1)

loads = []
for i in range(int(num_loads)):
    st.markdown(f"### Load {i+1}")
    mag = st.number_input(f"Load {i+1} magnitude (kN)", min_value=0.0, value=10.00, step=1.0, key=f"mag_{i}")
    loc = st.number_input(f"Load {i+1} location from A (m)", min_value=0.0, max_value=L, value=3.00, step=0.1, key=f"loc_{i}")
    loads.append((mag, loc))

# 2. Thông số tiết diện và vật liệu
st.subheader("Rectangular Cross Section")
b = st.number_input("Beam width b (mm)", min_value=10.0, value=200.00, step=10.0)
h = st.number_input("Beam height h (mm)", min_value=10.0, value=400.00, step=10.0)

material_db = {
    "A36 Steel": {"E": 200000.0, "Fy": 250.0},
    "Aluminum (6061-T6)": {"E": 68900.0, "Fy": 276.0},
    "Custom Wood": {"E": 11000.0, "Fy": 30.0}
}
material = st.selectbox("Select material", list(material_db.keys()))
fos = st.number_input("Factor of safety", min_value=1.0, value=1.50, step=0.1)

if st.button("Analyze Beam"):
    # Tính toán phản lực gối (Support Reactions)
    sum_moment_A = sum(mag * loc for mag, loc in loads)
    R_B = sum_moment_A / L if L > 0 else 0
    R_A = sum(mag for mag, _ in loads) - R_B

    st.subheader("Support Reactions")
    st.markdown(f"- Reaction at A: **{R_A:.3f} kN**")
    st.markdown(f"- Reaction at B: **{R_B:.3f} kN**")

    # Tính toán nội lực tại các điểm chia lưới nhỏ trên dầm để vẽ biểu đồ
    x = np.linspace(0, L, 500)
    V = np.zeros_like(x)
    M = np.zeros_like(x)

    for idx, xi in enumerate(x):
        # Lực cắt V(x) = R_A - sum(P_i khi x >= l_i)
        v_val = R_A
        m_val = R_A * xi
        for mag, loc in loads:
            if xi >= loc:
                v_val -= mag
                m_val -= mag * (xi - loc)
        V[idx] = v_val
        M[idx] = m_val

    max_moment = np.max(np.abs(M))
    max_moment_loc = x[np.argmax(np.abs(M))]
    max_shear = np.max(np.abs(V))

    st.subheader("Internal Force Results")
    st.write(f"Maximum shear: **{max_shear:.3f} kN**")
    st.write(f"Maximum moment: **{max_moment:.3f} kN·m**")
    st.write(f"Maximum moment location: **{max_moment_loc:.3f} m** from support A")

    # Kiểm tra vật liệu (Material Check)
    mat_props = material_db[material]
    E = mat_props["E"]
    Fy = mat_props["Fy"]

    # Mô men quán tính I = b*h^3 / 12 (mm^4)
    I = (b * (h**3)) / 12.0
    c = h / 2.0
    S = I / c  # Section modulus (mm^3)

    # Ứng suất uốn lớn nhất (MPa = N/mm^2)
    max_moment_Nmm = max_moment * 1e6  # đổi từ kN·m sang N·mm
    sigma_max = max_moment_Nmm / S
    allowable_stress = Fy / fos
    utilization = sigma_max / allowable_stress

    st.subheader("Material Check")
    st.write(f"Material: **{material}**")
    st.write(f"Young's modulus: **{E:.1f} MPa**")
    st.write(f"Yield strength: **{Fy:.3f} MPa**")
    st.write(f"Moment of inertia: **{I:.3e} mm⁴**")
    st.write(f"Section modulus: **{S:.3e} mm³**")
    st.write(f"Maximum bending stress: **{sigma_max:.3f} MPa**")
    st.write(f"Allowable stress: **{allowable_stress:.3f} MPa**")
    st.write(f"Utilization ratio: **{utilization:.3f}**")

    if sigma_max <= allowable_stress:
        st.success("Material check: **PASS**")
    else:
        st.error("Material check: **FAIL**")

    # Vẽ biểu đồ momen uốn (Bending Moment Diagram)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x, M, color="tab:blue", lw=2)
    ax.fill_between(x, M, color="tab:blue", alpha=0.1)
    ax.set_title("Bending Moment Diagram (BMD)")
    ax.set_xlabel("Position Along Beam (m)")
    ax.set_ylabel("Bending Moment (kN·m)")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.axhline(0, color='black', linewidth=0.8)

    st.pyplot(fig)
