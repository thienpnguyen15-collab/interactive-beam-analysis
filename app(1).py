import io
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Interactive Beam Analysis",
    page_icon="📐",
    layout="wide"
)

st.title("Interactive Beam Analysis and Material Check")
st.caption(
    "Simply supported beam analysis with point loads, distributed loads, "
    "free-body diagram, shear-force diagram, bending-moment diagram, "
    "and simplified material checking."
)

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
st.sidebar.header("Beam Settings")

L = st.sidebar.number_input(
    "Beam length L (m)",
    min_value=0.10,
    value=6.00,
    step=0.10
)

load_mode = st.sidebar.selectbox(
    "Input method",
    ["Manual Input", "Upload CSV"]
)

load_type = st.sidebar.selectbox(
    "Load type",
    ["Point Loads", "Uniform Distributed Load", "Combined Loads"]
)

st.sidebar.header("Cross Section")

section_type = st.sidebar.selectbox(
    "Section shape",
    ["Rectangular", "Circular", "Hollow Rectangular"]
)

if section_type == "Rectangular":
    b = st.sidebar.number_input(
        "Width b (mm)", min_value=1.0, value=200.0, step=10.0
    )
    h = st.sidebar.number_input(
        "Height h (mm)", min_value=1.0, value=400.0, step=10.0
    )
    I = b * h**3 / 12.0
    c = h / 2.0

elif section_type == "Circular":
    d = st.sidebar.number_input(
        "Diameter d (mm)", min_value=1.0, value=300.0, step=10.0
    )
    I = np.pi * d**4 / 64.0
    c = d / 2.0

else:
    bo = st.sidebar.number_input(
        "Outer width bo (mm)", min_value=2.0, value=300.0, step=10.0
    )
    ho = st.sidebar.number_input(
        "Outer height ho (mm)", min_value=2.0, value=500.0, step=10.0
    )
    bi = st.sidebar.number_input(
        "Inner width bi (mm)", min_value=1.0, value=200.0, step=10.0
    )
    hi = st.sidebar.number_input(
        "Inner height hi (mm)", min_value=1.0, value=400.0, step=10.0
    )

    if bi >= bo or hi >= ho:
        st.sidebar.error("Inner dimensions must be smaller than outer dimensions.")
        I = np.nan
        c = ho / 2.0
    else:
        I = (bo * ho**3 - bi * hi**3) / 12.0
        c = ho / 2.0

S = I / c if np.isfinite(I) and c > 0 else np.nan

st.sidebar.header("Material")

material = st.sidebar.selectbox(
    "Material",
    ["A36 Steel", "Aluminum 6061-T6", "Douglas Fir", "Custom"]
)

if material == "A36 Steel":
    E = 200000.0
    strength = 250.0
elif material == "Aluminum 6061-T6":
    E = 68900.0
    strength = 276.0
elif material == "Douglas Fir":
    E = 12000.0
    strength = 40.0
else:
    E = st.sidebar.number_input(
        "Young's modulus E (MPa)", min_value=1.0, value=100000.0
    )
    strength = st.sidebar.number_input(
        "Reference strength (MPa)", min_value=1.0, value=200.0
    )

fos = st.sidebar.number_input(
    "Factor of safety", min_value=0.10, value=1.50, step=0.10
)

# ---------------------------------------------------------
# INPUT TABS
# ---------------------------------------------------------
tab_input, tab_results, tab_theory, tab_guide = st.tabs(
    ["Input", "Results", "Theory", "User Guide"]
)

point_loads = []
udls = []

with tab_input:
    st.subheader("Load Input")

    if load_mode == "Upload CSV":
        st.write(
            "Upload a CSV with columns: `type`, `magnitude`, `start`, `end`."
        )
        st.write(
            "For a point load, use type `point`, magnitude in kN, "
            "and put the location in `start`. The `end` value may be blank."
        )
        st.write(
            "For a UDL, use type `udl`, magnitude in kN/m, "
            "with start and end positions in meters."
        )

        sample = pd.DataFrame(
            {
                "type": ["point", "point", "udl"],
                "magnitude": [10.0, 15.0, 5.0],
                "start": [2.0, 4.0, 1.0],
                "end": [np.nan, np.nan, 3.0],
            }
        )

        st.download_button(
            "Download sample CSV",
            data=sample.to_csv(index=False).encode("utf-8"),
            file_name="beam_loads_sample.csv",
            mime="text/csv",
        )

        uploaded = st.file_uploader("Upload load CSV", type=["csv"])

        if uploaded is not None:
            try:
                df = pd.read_csv(uploaded)
                required = {"type", "magnitude", "start", "end"}

                if not required.issubset(set(df.columns)):
                    st.error(
                        "CSV must include columns: type, magnitude, start, end."
                    )
                else:
                    st.dataframe(df, use_container_width=True)

                    for _, row in df.iterrows():
                        kind = str(row["type"]).strip().lower()
                        magnitude = float(row["magnitude"])
                        start = float(row["start"])

                        if kind == "point":
                            point_loads.append((magnitude, start))

                        elif kind == "udl":
                            end = float(row["end"])
                            udls.append((magnitude, start, end))

            except Exception as exc:
                st.error(f"Could not read CSV: {exc}")

    else:
        if load_type in ["Point Loads", "Combined Loads"]:
            st.markdown("### Point Loads")

            n_point = st.number_input(
                "Number of point loads",
                min_value=0,
                max_value=10,
                value=2,
                step=1
            )

            for i in range(int(n_point)):
                col1, col2 = st.columns(2)

                with col1:
                    p = st.number_input(
                        f"Point load {i + 1} magnitude (kN)",
                        min_value=0.0,
                        value=10.0 if i == 0 else 15.0,
                        step=0.5,
                        key=f"point_mag_{i}"
                    )

                with col2:
                    default_x = 2.0 if i == 0 else min(4.0, float(L))
                    xp = st.number_input(
                        f"Point load {i + 1} location (m)",
                        min_value=0.0,
                        max_value=float(L),
                        value=min(default_x, float(L)),
                        step=0.1,
                        key=f"point_x_{i}"
                    )

                point_loads.append((p, xp))

        if load_type in ["Uniform Distributed Load", "Combined Loads"]:
            st.markdown("### Uniform Distributed Loads")

            n_udl = st.number_input(
                "Number of distributed loads",
                min_value=0,
                max_value=5,
                value=1,
                step=1
            )

            for i in range(int(n_udl)):
                col1, col2, col3 = st.columns(3)

                with col1:
                    w = st.number_input(
                        f"UDL {i + 1} intensity (kN/m)",
                        min_value=0.0,
                        value=5.0,
                        step=0.5,
                        key=f"udl_w_{i}"
                    )

                with col2:
                    a = st.number_input(
                        f"UDL {i + 1} start (m)",
                        min_value=0.0,
                        max_value=float(L),
                        value=1.0 if L >= 1 else 0.0,
                        step=0.1,
                        key=f"udl_a_{i}"
                    )

                with col3:
                    default_end = min(float(L), 3.0)
                    b_end = st.number_input(
                        f"UDL {i + 1} end (m)",
                        min_value=0.0,
                        max_value=float(L),
                        value=default_end,
                        step=0.1,
                        key=f"udl_b_{i}"
                    )

                udls.append((w, a, b_end))

    st.info(
        "After entering the loads, open the Results tab and click Analyze Beam."
    )

# ---------------------------------------------------------
# ANALYSIS FUNCTION
# ---------------------------------------------------------
def analyze_beam(length, points, distributed):
    errors = []

    if length <= 0:
        errors.append("Beam length must be positive.")

    clean_points = []
    for p, xp in points:
        if p < 0:
            errors.append("Point-load magnitudes cannot be negative.")
        elif xp < 0 or xp > length:
            errors.append("Point-load locations must be on the beam.")
        else:
            clean_points.append((float(p), float(xp)))

    clean_udls = []
    for w, a, b_end in distributed:
        if w < 0:
            errors.append("UDL intensities cannot be negative.")
        elif a < 0 or b_end > length or b_end <= a:
            errors.append("Each UDL must satisfy 0 ≤ start < end ≤ L.")
        else:
            clean_udls.append((float(w), float(a), float(b_end)))

    if errors:
        return None, errors

    total_load = sum(p for p, _ in clean_points)
    moment_about_a = sum(p * xp for p, xp in clean_points)

    for w, a, b_end in clean_udls:
        resultant = w * (b_end - a)
        centroid = (a + b_end) / 2.0
        total_load += resultant
        moment_about_a += resultant * centroid

    RB = moment_about_a / length
    RA = total_load - RB

    x = np.linspace(0.0, length, 3001)
    V = np.full_like(x, RA, dtype=float)
    M = RA * x

    for p, xp in clean_points:
        mask = x >= xp
        V[mask] -= p
        M[mask] -= p * (x[mask] - xp)

    for w, a, b_end in clean_udls:
        inside = (x >= a) & (x <= b_end)
        after = x > b_end

        V[inside] -= w * (x[inside] - a)
        M[inside] -= 0.5 * w * (x[inside] - a) ** 2

        resultant = w * (b_end - a)
        centroid = (a + b_end) / 2.0

        V[after] -= resultant
        M[after] -= resultant * (x[after] - centroid)

    force_error = abs(RA + RB - total_load)
    moment_error = abs(RB * length - moment_about_a)

    max_shear = float(np.max(np.abs(V)))
    max_moment_index = int(np.argmax(np.abs(M)))
    max_moment = float(abs(M[max_moment_index]))
    max_moment_x = float(x[max_moment_index])

    return {
        "RA": RA,
        "RB": RB,
        "total_load": total_load,
        "x": x,
        "V": V,
        "M": M,
        "max_shear": max_shear,
        "max_moment": max_moment,
        "max_moment_x": max_moment_x,
        "force_error": force_error,
        "moment_error": moment_error,
        "points": clean_points,
        "udls": clean_udls,
    }, []

# ---------------------------------------------------------
# RESULTS TAB
# ---------------------------------------------------------
with tab_results:
    st.subheader("Beam Analysis Results")

    if st.button("Analyze Beam", type="primary"):
        result, errors = analyze_beam(L, point_loads, udls)

        if errors:
            for error in errors:
                st.error(error)

        elif not np.isfinite(I) or not np.isfinite(S):
            st.error("Cross-section dimensions are invalid.")

        else:
            RA = result["RA"]
            RB = result["RB"]
            max_moment = result["max_moment"]

            sigma_max = max_moment * 1e6 / S
            allowable_stress = strength / fos
            utilization = sigma_max / allowable_stress
            material_pass = utilization <= 1.0

            st.markdown("### Support Reactions")
            c1, c2, c3 = st.columns(3)
            c1.metric("Reaction at A", f"{RA:.3f} kN")
            c2.metric("Reaction at B", f"{RB:.3f} kN")
            c3.metric("Total applied load", f"{result['total_load']:.3f} kN")

            st.markdown("### Internal Force Results")
            c1, c2, c3 = st.columns(3)
            c1.metric("Maximum shear", f"{result['max_shear']:.3f} kN")
            c2.metric("Maximum moment", f"{max_moment:.3f} kN·m")
            c3.metric(
                "Location of maximum moment",
                f"{result['max_moment_x']:.3f} m"
            )

            st.markdown("### Equilibrium Check")
            st.write(
                f"Vertical-force error: {result['force_error']:.3e} kN"
            )
            st.write(
                f"Moment error about A: {result['moment_error']:.3e} kN·m"
            )

            if (
                result["force_error"] < 1e-8
                and result["moment_error"] < 1e-8
            ):
                st.success("Equilibrium verification: PASS")
            else:
                st.error("Equilibrium verification: FAIL")

            st.markdown("### Material Check")
            st.write(f"Material: {material}")
            st.write(f"Young's modulus: {E:.0f} MPa")
            st.write(f"Reference strength: {strength:.3f} MPa")
            st.write(f"Moment of inertia: {I:.3e} mm⁴")
            st.write(f"Section modulus: {S:.3e} mm³")
            st.write(f"Maximum bending stress: {sigma_max:.3f} MPa")
            st.write(f"Allowable stress: {allowable_stress:.3f} MPa")
            st.write(f"Utilization ratio: {utilization:.3f}")

            if material_pass:
                st.success("Material check: PASS")
            else:
                st.error("Material check: DOES NOT PASS")

            st.markdown("### Free-Body Diagram")

            fig_fbd, ax_fbd = plt.subplots(figsize=(11, 3.5))
            ax_fbd.plot([0, L], [0, 0], linewidth=5)
            ax_fbd.plot(0, 0, marker="^", markersize=12)
            ax_fbd.plot(
                L, 0, marker="^", markersize=12, markerfacecolor="white"
            )

            vertical_scale = max(
                [p for p, _ in result["points"]]
                + [w for w, _, _ in result["udls"]]
                + [1.0]
            )

            for p, xp in result["points"]:
                ax_fbd.annotate(
                    "",
                    xy=(xp, 0.03 * vertical_scale),
                    xytext=(xp, 0.55 * vertical_scale),
                    arrowprops={"arrowstyle": "->", "linewidth": 2}
                )
                ax_fbd.text(
                    xp,
                    0.62 * vertical_scale,
                    f"{p:.1f} kN",
                    ha="center"
                )

            for w, a, b_end in result["udls"]:
                xs = np.linspace(a, b_end, 9)
                for xi in xs:
                    ax_fbd.annotate(
                        "",
                        xy=(xi, 0.03 * vertical_scale),
                        xytext=(xi, 0.35 * vertical_scale),
                        arrowprops={"arrowstyle": "->", "linewidth": 1}
                    )
                ax_fbd.plot(
                    [a, b_end],
                    [0.35 * vertical_scale, 0.35 * vertical_scale],
                    linewidth=2
                )
                ax_fbd.text(
                    (a + b_end) / 2,
                    0.43 * vertical_scale,
                    f"{w:.1f} kN/m",
                    ha="center"
                )

            ax_fbd.annotate(
                "",
                xy=(0, 0.0),
                xytext=(0, -0.45 * vertical_scale),
                arrowprops={"arrowstyle": "->", "linewidth": 2}
            )
            ax_fbd.annotate(
                "",
                xy=(L, 0.0),
                xytext=(L, -0.45 * vertical_scale),
                arrowprops={"arrowstyle": "->", "linewidth": 2}
            )

            ax_fbd.text(
                0, -0.58 * vertical_scale, f"RA = {RA:.2f} kN", ha="left"
            )
            ax_fbd.text(
                L, -0.58 * vertical_scale, f"RB = {RB:.2f} kN", ha="right"
            )

            ax_fbd.set_xlim(-0.05 * L, 1.05 * L)
            ax_fbd.set_ylim(
                -0.75 * vertical_scale,
                0.85 * vertical_scale
            )
            ax_fbd.set_xlabel("Position along beam (m)")
            ax_fbd.set_yticks([])
            ax_fbd.grid(True)
            st.pyplot(fig_fbd)
            plt.close(fig_fbd)

            st.markdown("### Shear-Force Diagram")
            fig_v, ax_v = plt.subplots(figsize=(11, 4))
            ax_v.plot(result["x"], result["V"], linewidth=2)
            ax_v.fill_between(
                result["x"], 0, result["V"], alpha=0.2
            )
            ax_v.axhline(0, linewidth=1)
            ax_v.set_xlim(0, L)
            ax_v.set_xlabel("Position along beam (m)")
            ax_v.set_ylabel("Shear force (kN)")
            ax_v.grid(True)
            st.pyplot(fig_v)
            plt.close(fig_v)

            st.markdown("### Bending-Moment Diagram")
            fig_m, ax_m = plt.subplots(figsize=(11, 4))
            ax_m.plot(result["x"], result["M"], linewidth=2)
            ax_m.fill_between(
                result["x"], 0, result["M"], alpha=0.2
            )
            ax_m.axhline(0, linewidth=1)
            ax_m.plot(
                result["max_moment_x"],
                result["M"][np.argmax(np.abs(result["M"]))],
                marker="o"
            )
            ax_m.set_xlim(0, L)
            ax_m.set_xlabel("Position along beam (m)")
            ax_m.set_ylabel("Bending moment (kN·m)")
            ax_m.grid(True)
            st.pyplot(fig_m)
            plt.close(fig_m)

            output_df = pd.DataFrame(
                {
                    "x_m": result["x"],
                    "shear_kN": result["V"],
                    "moment_kNm": result["M"],
                }
            )

            st.download_button(
                "Download analysis results CSV",
                data=output_df.to_csv(index=False).encode("utf-8"),
                file_name="beam_analysis_results.csv",
                mime="text/csv"
            )

# ---------------------------------------------------------
# THEORY TAB
# ---------------------------------------------------------
with tab_theory:
    st.subheader("Theoretical Background")

    st.markdown(
        r"""
For a simply supported beam, the support reactions are found from static
equilibrium:

\[
\sum F_y = 0
\]

\[
\sum M_A = 0
\]

For a rectangular cross section:

\[
I = \frac{bh^3}{12}
\]

\[
S = \frac{I}{c}
\]

The maximum bending stress is estimated by:

\[
\sigma_{\max} = \frac{M_{\max}}{S}
\]

The allowable stress is:

\[
\sigma_{\text{allow}} =
\frac{\text{material strength}}{\text{factor of safety}}
\]

The simplified material check passes when:

\[
\sigma_{\max} \leq \sigma_{\text{allow}}
\]
"""
    )

    st.warning(
        "This educational application does not perform a complete structural "
        "design. It does not check detailed shear strength, buckling, fatigue, "
        "connections, lateral stability, code requirements, or serviceability."
    )

# ---------------------------------------------------------
# GUIDE TAB
# ---------------------------------------------------------
with tab_guide:
    st.subheader("How to Use the Application")

    st.markdown(
        """
1. Enter the beam length in the sidebar.
2. Select manual input or CSV upload.
3. Choose point loads, distributed loads, or combined loads.
4. Enter the cross-section dimensions.
5. Select a material and factor of safety.
6. Open the Results tab.
7. Click **Analyze Beam**.
8. Review reactions, equilibrium, material check, free-body diagram,
   shear-force diagram, and bending-moment diagram.
9. Download the numerical results as a CSV file when needed.
"""
    )
