import io
import math
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title='Interactive Beam Analysis', page_icon='📐', layout='wide', initial_sidebar_state='expanded')

st.markdown('''
<style>
.block-container {padding-top:1.2rem; padding-bottom:3rem;}
[data-testid="stSidebar"] {min-width:350px; max-width:350px;}
.small-note {color:#697586; font-size:.9rem;}
</style>
''', unsafe_allow_html=True)

@dataclass
class PointLoad:
    magnitude: float
    location: float

@dataclass
class DistributedLoad:
    start: float
    end: float
    w_start: float
    w_end: float

    @property
    def length(self):
        return self.end - self.start

    @property
    def resultant(self):
        return 0.5 * (self.w_start + self.w_end) * self.length

    @property
    def centroid(self):
        L = self.length
        if L <= 0 or abs(self.resultant) < 1e-12:
            return self.start
        rect = min(self.w_start, self.w_end) * L
        tri = abs(self.w_end - self.w_start) * L / 2
        xr = self.start + L / 2
        xt = self.start + (2 * L / 3 if self.w_end >= self.w_start else L / 3)
        return (rect * xr + tri * xt) / self.resultant

@dataclass
class AppliedMoment:
    magnitude: float
    location: float


def cumtrapz(y, x):
    out = np.zeros_like(y, dtype=float)
    if len(y) > 1:
        out[1:] = np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(x))
    return out


def load_intensity(load, x):
    w = np.zeros_like(x)
    active = (x >= load.start) & (x <= load.end)
    if load.length > 0:
        w[active] = load.w_start + (load.w_end - load.w_start) * (x[active] - load.start) / load.length
    return w


def analyze(L, point_loads, distributed_loads, moments):
    total_force = sum(p.magnitude for p in point_loads) + sum(d.resultant for d in distributed_loads)
    load_moment_a = sum(p.magnitude * p.location for p in point_loads) + sum(d.resultant * d.centroid for d in distributed_loads)
    applied_moment = sum(m.magnitude for m in moments)  # positive = CCW
    RB = (load_moment_a - applied_moment) / L
    RA = total_force - RB

    x = np.linspace(0, L, 4001)
    w = np.zeros_like(x)
    for d in distributed_loads:
        w += load_intensity(d, x)

    V = RA - cumtrapz(w, x)
    for p in point_loads:
        V[x >= p.location] -= p.magnitude

    M = cumtrapz(V, x)
    for m in moments:
        M[x >= m.location] -= m.magnitude

    V[np.abs(V) < 1e-10] = 0
    M[np.abs(M) < 1e-10] = 0

    iv = int(np.argmax(np.abs(V)))
    im = int(np.argmax(np.abs(M)))
    force_error = abs(RA + RB - total_force)
    moment_error = abs(RB * L + applied_moment - load_moment_a)

    return {
        'RA': RA, 'RB': RB, 'x': x, 'w': w, 'V': V, 'M': M,
        'total_load': total_force,
        'max_shear': abs(V[iv]), 'max_shear_x': x[iv],
        'max_moment': abs(M[im]), 'max_moment_signed': M[im], 'max_moment_x': x[im],
        'force_error': force_error, 'moment_error': moment_error,
        'moment_at_a': M[0], 'moment_at_b': M[-1]
    }


def section_props(shape, dims):
    if shape == 'Rectangular':
        b, h = dims['b'], dims['h']
        A = b * h
        I = b * h**3 / 12
        c = h / 2
        desc = f'{b:.1f} × {h:.1f} mm rectangular section'
    elif shape == 'Circular':
        d = dims['d']
        A = math.pi * d**2 / 4
        I = math.pi * d**4 / 64
        c = d / 2
        desc = f'{d:.1f} mm diameter circular section'
    else:
        bo, ho, bi, hi = dims['bo'], dims['ho'], dims['bi'], dims['hi']
        A = bo * ho - bi * hi
        I = (bo * ho**3 - bi * hi**3) / 12
        c = ho / 2
        desc = f'{bo:.1f} × {ho:.1f} mm hollow rectangular section'
    return {'A': A, 'I': I, 'c': c, 'S': I / c, 'description': desc}


def material_props(name, custom_E, custom_strength):
    data = {
        'A36 Steel': (200000.0, 250.0, 'Yield strength'),
        'Aluminum 6061-T6': (68900.0, 276.0, 'Yield strength'),
        'Douglas Fir-Larch': (11000.0, 12.0, 'Reference bending strength'),
        'Normal-Weight Concrete': (25000.0, 20.0, 'Simplified flexural strength'),
        'Custom': (custom_E, custom_strength, 'Specified strength')
    }
    E, strength, label = data[name]
    return {'E': E, 'strength': strength, 'label': label}


def deflection_curve(x_m, M_knm, E_mpa, I_mm4):
    x_mm = x_m * 1000
    curvature = M_knm * 1e6 / (E_mpa * I_mm4)
    slope0 = cumtrapz(curvature, x_mm)
    defl0 = cumtrapz(slope0, x_mm)
    c1 = -defl0[-1] / x_mm[-1]
    slope = slope0 + c1
    defl = defl0 + c1 * x_mm
    return slope, defl


def plot_fbd(L, points, distributed, moments, RA, RB):
    fig, ax = plt.subplots(figsize=(12, 4.2))
    ax.plot([0, L], [0, 0], linewidth=6)
    ax.plot(0, 0, '^', markersize=15)
    ax.plot(L, 0, '^', markersize=15, markerfacecolor='white')

    scale = max([p.magnitude for p in points] + [d.w_start for d in distributed] + [d.w_end for d in distributed] + [1])
    H = max(1.0, 0.16 * scale)

    for x0, r, label, ha in [(0, RA, 'RA', 'left'), (L, RB, 'RB', 'right')]:
        ax.annotate('', xy=(x0, 0.03), xytext=(x0, -1.15 * H), arrowprops={'arrowstyle':'->', 'linewidth':2.1})
        ax.text(x0, -1.38 * H, f'{label} = {r:.2f} kN', ha=ha, va='top')

    for p in points:
        ax.annotate('', xy=(p.location, 0.05), xytext=(p.location, 1.55 * H), arrowprops={'arrowstyle':'->', 'linewidth':2.1})
        ax.text(p.location, 1.68 * H, f'{p.magnitude:.2f} kN', ha='center')

    for i, d in enumerate(distributed):
        xs = np.linspace(d.start, d.end, max(5, int(12 * d.length / L)))
        for xv in xs:
            wv = d.w_start + (d.w_end - d.w_start) * (xv - d.start) / d.length
            top = 0.6 * H + H * wv / max(scale, 1e-9)
            ax.annotate('', xy=(xv, 0.05), xytext=(xv, top), arrowprops={'arrowstyle':'->', 'linewidth':1.15})
        ax.text((d.start+d.end)/2, 2.0*H, f'Distributed {i+1}: {d.w_start:.2f} → {d.w_end:.2f} kN/m', ha='center', fontsize=9)

    for m in moments:
        symbol = '↺' if m.magnitude >= 0 else '↻'
        ax.text(m.location, 0.55*H, f'{symbol} {abs(m.magnitude):.2f} kN·m', ha='center', fontsize=12)

    ax.text(0, -0.28*H, 'A', ha='center', fontweight='bold')
    ax.text(L, -0.28*H, 'B', ha='center', fontweight='bold')
    ax.set_xlim(-0.06*L, 1.06*L)
    ax.set_ylim(-1.8*H, 2.45*H)
    ax.set_xlabel('Position along beam (m)')
    ax.set_title('Free-Body Diagram')
    ax.set_yticks([])
    ax.grid(axis='x', alpha=.25)
    fig.tight_layout()
    return fig


def plot_xy(x, y, title, ylabel, marker=None, step=False):
    fig, ax = plt.subplots(figsize=(11.5, 4.2))
    if step:
        ax.step(x, y, where='post', linewidth=2)
    else:
        ax.plot(x, y, linewidth=2)
    ax.fill_between(x, y, 0, alpha=.12)
    ax.axhline(0, linewidth=1)
    ax.set_xlim(x[0], x[-1])
    ax.set_xlabel('Position along beam (m)')
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=.28)
    if marker:
        mx, my = marker
        ax.plot(mx, my, 'o')
        ax.annotate(f'{abs(my):.3f}', (mx, my), xytext=(9,10), textcoords='offset points')
    fig.tight_layout()
    return fig


if 'uploaded_points' not in st.session_state:
    st.session_state.uploaded_points = []
    st.session_state.uploaded_distributed = []
    st.session_state.uploaded_moments = []
    st.session_state.results = None

# ---------------- SIDEBAR ----------------
st.sidebar.title('Beam Setup')
L = st.sidebar.number_input('Beam length, L (m)', min_value=0.10, value=6.00, step=0.10)
source = st.sidebar.radio('Load source', ['Manual entry', 'Uploaded CSV'], horizontal=True)

points, distributed, moments = [], [], []
if source == 'Manual entry':
    families = st.sidebar.multiselect('Load types', ['Point loads','Uniformly distributed loads','Linearly varying loads','Applied moments'], default=['Point loads'])

    if 'Point loads' in families:
        n = st.sidebar.number_input('Number of point loads', 0, 12, 2, 1)
        for i in range(int(n)):
            with st.sidebar.expander(f'Point load {i+1}', expanded=i<2):
                mag = st.number_input('Magnitude (kN)', min_value=0.0, value=10.0 if i==0 else 15.0, step=0.5, key=f'pmag{i}')
                loc = st.number_input('Location from A (m)', min_value=0.0, max_value=float(L), value=float(L*(i+1)/(int(n)+1)), step=0.1, key=f'ploc{i}')
                points.append(PointLoad(mag, loc))

    if 'Uniformly distributed loads' in families:
        n = st.sidebar.number_input('Number of uniform loads', 0, 6, 1, 1)
        for i in range(int(n)):
            with st.sidebar.expander(f'Uniform load {i+1}'):
                a = st.number_input('Start (m)', 0.0, float(L), 0.0, 0.1, key=f'ua{i}')
                b = st.number_input('End (m)', 0.0, float(L), float(L), 0.1, key=f'ub{i}')
                w = st.number_input('Intensity (kN/m)', min_value=0.0, value=5.0, step=0.5, key=f'uw{i}')
                distributed.append(DistributedLoad(a,b,w,w))

    if 'Linearly varying loads' in families:
        n = st.sidebar.number_input('Number of varying loads', 0, 6, 1, 1)
        for i in range(int(n)):
            with st.sidebar.expander(f'Varying load {i+1}'):
                a = st.number_input('Start (m)', 0.0, float(L), 0.0, 0.1, key=f'va{i}')
                b = st.number_input('End (m)', 0.0, float(L), float(L), 0.1, key=f'vb{i}')
                w1 = st.number_input('Start intensity (kN/m)', min_value=0.0, value=0.0, step=0.5, key=f'vw1{i}')
                w2 = st.number_input('End intensity (kN/m)', min_value=0.0, value=8.0, step=0.5, key=f'vw2{i}')
                distributed.append(DistributedLoad(a,b,w1,w2))

    if 'Applied moments' in families:
        n = st.sidebar.number_input('Number of applied moments', 0, 6, 1, 1)
        for i in range(int(n)):
            with st.sidebar.expander(f'Applied moment {i+1}'):
                mag = st.number_input('Moment (kN·m)', value=5.0, step=0.5, key=f'mmag{i}', help='Positive = counterclockwise')
                loc = st.number_input('Location from A (m)', 0.0, float(L), float(L/2), 0.1, key=f'mloc{i}')
                moments.append(AppliedMoment(mag,loc))

st.sidebar.divider()
st.sidebar.subheader('Cross Section')
shape = st.sidebar.selectbox('Section shape', ['Rectangular','Circular','Hollow rectangular'])
dims = {}
if shape == 'Rectangular':
    dims['b'] = st.sidebar.number_input('Width, b (mm)', min_value=1.0, value=200.0, step=10.0)
    dims['h'] = st.sidebar.number_input('Height, h (mm)', min_value=1.0, value=400.0, step=10.0)
elif shape == 'Circular':
    dims['d'] = st.sidebar.number_input('Diameter, d (mm)', min_value=1.0, value=300.0, step=10.0)
else:
    dims['bo'] = st.sidebar.number_input('Outer width (mm)', min_value=1.0, value=250.0, step=10.0)
    dims['ho'] = st.sidebar.number_input('Outer height (mm)', min_value=1.0, value=400.0, step=10.0)
    dims['bi'] = st.sidebar.number_input('Inner width (mm)', min_value=0.0, value=180.0, step=10.0)
    dims['hi'] = st.sidebar.number_input('Inner height (mm)', min_value=0.0, value=330.0, step=10.0)

st.sidebar.divider()
st.sidebar.subheader('Material and Safety')
material_name = st.sidebar.selectbox('Material', ['A36 Steel','Aluminum 6061-T6','Douglas Fir-Larch','Normal-Weight Concrete','Custom'])
custom_E, custom_strength = 100000.0, 200.0
if material_name == 'Custom':
    custom_E = st.sidebar.number_input("Young's modulus, E (MPa)", min_value=1.0, value=100000.0, step=1000.0)
    custom_strength = st.sidebar.number_input('Strength value (MPa)', min_value=0.1, value=200.0, step=5.0)
fos = st.sidebar.number_input('Factor of safety', min_value=0.1, value=1.5, step=0.1)
include_deflection = st.sidebar.checkbox('Calculate elastic deflection', value=True)
run = st.sidebar.button('Analyze Beam', type='primary', use_container_width=True)

st.title('Interactive Beam Analysis')
st.caption('Explore how loads, geometry, and material selection affect a simply supported beam.')

analysis_tab, upload_tab, theory_tab, guide_tab = st.tabs(['Analysis','Upload','Theory','User Guide'])

with upload_tab:
    st.subheader('Upload Beam Loads')
    st.write('Upload a CSV file, then choose **Uploaded CSV** in the sidebar and click **Analyze Beam**.')
    template = pd.DataFrame([
        {'type':'point','magnitude':10,'location':2,'start':'','end':'','w_start':'','w_end':''},
        {'type':'udl','magnitude':'','location':'','start':3,'end':5,'w_start':4,'w_end':4},
        {'type':'varying','magnitude':'','location':'','start':0,'end':2,'w_start':0,'w_end':6},
        {'type':'moment','magnitude':5,'location':4.5,'start':'','end':'','w_start':'','w_end':''}
    ])
    st.download_button('Download CSV Template', template.to_csv(index=False).encode(), 'beam_load_template.csv', 'text/csv')
    file = st.file_uploader('Choose CSV file', type=['csv'])
    if file:
        try:
            df = pd.read_csv(file)
            st.dataframe(df, use_container_width=True)
            up_p, up_d, up_m = [], [], []
            if 'type' not in df.columns:
                st.error("CSV must include a 'type' column.")
            else:
                for idx, row in df.iterrows():
                    typ = str(row.get('type','')).strip().lower()
                    if typ == 'point':
                        up_p.append(PointLoad(float(row['magnitude']), float(row['location'])))
                    elif typ in {'udl','uniform'}:
                        w = float(row['w_start'])
                        up_d.append(DistributedLoad(float(row['start']), float(row['end']), w, w))
                    elif typ in {'varying','triangular','trapezoidal'}:
                        up_d.append(DistributedLoad(float(row['start']), float(row['end']), float(row['w_start']), float(row['w_end'])))
                    elif typ == 'moment':
                        up_m.append(AppliedMoment(float(row['magnitude']), float(row['location'])))
                    else:
                        st.warning(f'Row {idx+2}: unsupported type {typ!r} skipped.')
                st.session_state.uploaded_points = up_p
                st.session_state.uploaded_distributed = up_d
                st.session_state.uploaded_moments = up_m
                st.success('Upload processed successfully.')
        except Exception as e:
            st.error(f'Could not read CSV: {e}')
    st.dataframe(pd.DataFrame([
        ['point','magnitude, location','Downward concentrated force'],
        ['udl','start, end, w_start','Uniform load'],
        ['varying','start, end, w_start, w_end','Triangular/trapezoidal load'],
        ['moment','magnitude, location','Positive = counterclockwise']
    ], columns=['Type','Required columns','Meaning']), use_container_width=True, hide_index=True)

with theory_tab:
    st.subheader('Theoretical Background')
    st.markdown(r'''
### Static equilibrium
\[\sum F_y=0\]
\[\sum M_A=0\]
\[R_B L+\sum M_k-\sum P_i x_i-\sum W_j\bar{x}_j=0\]
\[R_A+R_B-\sum P_i-\sum W_j=0\]

### Shear and bending moment
Point loads create sudden changes in shear. Distributed loads cause gradual changes.
\[\frac{dM}{dx}=V\]

### Section properties and bending stress
For a rectangular section:
\[I=\frac{bh^3}{12},\qquad S=\frac{I}{c}\]
\[\sigma_{max}=\frac{M_{max}}{S}\]
\[\sigma_{allow}=\frac{\text{material strength}}{\text{factor of safety}}\]
\[U=\frac{\sigma_{max}}{\sigma_{allow}}\]

### Elastic deflection
\[EI\frac{d^2v}{dx^2}=M(x)\]
The app numerically integrates curvature and applies \(v(0)=v(L)=0\).
''')
    st.warning('Wood and concrete checks are educational simplifications. Actual design must follow material-specific codes and load combinations.')

with guide_tab:
    st.subheader('User Guide')
    st.markdown('''
1. Enter beam length in the sidebar.
2. Choose manual input or uploaded CSV.
3. Select point loads, uniform loads, varying loads, and/or applied moments.
4. Enter section dimensions, material, and factor of safety.
5. Click **Analyze Beam**.
6. Review the FBD, reactions, verification, SFD, BMD, stress check, and optional deflection.
''')
    st.dataframe(pd.DataFrame([
        ['Support','Simply supported beam'],
        ['Loads','Point, UDL, triangular/trapezoidal, applied moment'],
        ['Sections','Rectangular, circular, hollow rectangular'],
        ['Materials','Steel, aluminum, wood, concrete, custom'],
        ['Diagrams','FBD, load intensity, SFD, BMD, deflection'],
        ['Upload','CSV template and upload'],
        ['Export','CSV analysis data and text summary']
    ], columns=['Feature','Capability']), use_container_width=True, hide_index=True)

with analysis_tab:
    if run:
        sel_points = points if source == 'Manual entry' else st.session_state.uploaded_points
        sel_dist = distributed if source == 'Manual entry' else st.session_state.uploaded_distributed
        sel_mom = moments if source == 'Manual entry' else st.session_state.uploaded_moments

        errors = []
        if not (sel_points or sel_dist or sel_mom):
            errors.append('Add at least one load or applied moment.')
        for i,p in enumerate(sel_points):
            if p.magnitude < 0 or not (0 <= p.location <= L): errors.append(f'Point load {i+1} is invalid.')
        for i,d in enumerate(sel_dist):
            if d.end <= d.start or d.start < 0 or d.end > L: errors.append(f'Distributed load {i+1} has invalid limits.')
            if d.w_start < 0 or d.w_end < 0: errors.append(f'Distributed load {i+1} intensity must be nonnegative.')
        for i,m in enumerate(sel_mom):
            if not (0 <= m.location <= L): errors.append(f'Applied moment {i+1} is outside the beam.')
        if shape == 'Hollow rectangular' and (dims['bi'] >= dims['bo'] or dims['hi'] >= dims['ho']):
            errors.append('Inner hollow-section dimensions must be smaller than outer dimensions.')

        if errors:
            for e in errors: st.error(e)
        else:
            a = analyze(L, sel_points, sel_dist, sel_mom)
            s = section_props(shape, dims)
            mat = material_props(material_name, custom_E, custom_strength)
            sigma = a['max_moment'] * 1e6 / s['S']
            allowable = mat['strength'] / fos
            util = sigma / allowable
            if include_deflection:
                _, defl = deflection_curve(a['x'], a['M'], mat['E'], s['I'])
                idef = int(np.argmax(np.abs(defl)))
                max_defl, max_defl_x = abs(defl[idef]), a['x'][idef]
            else:
                defl, max_defl, max_defl_x = None, None, None
            st.session_state.results = dict(a=a,s=s,mat=mat,sigma=sigma,allowable=allowable,util=util,defl=defl,max_defl=max_defl,max_defl_x=max_defl_x,points=sel_points,dist=sel_dist,mom=sel_mom)

    r = st.session_state.results
    if not r:
        st.info('Configure the beam in the sidebar and click **Analyze Beam**.')
        st.code('''Beam length: 6 m
Point load 1: 10 kN at 2 m
Point load 2: 15 kN at 4 m
Section: 200 × 400 mm rectangular
Material: A36 Steel
Factor of safety: 1.5''')
    else:
        a,s,mat = r['a'],r['s'],r['mat']
        summary_tab, diagrams_tab, steps_tab, export_tab = st.tabs(['Summary','Diagrams','Calculation Steps','Export'])

        with summary_tab:
            c = st.columns(4)
            c[0].metric('Reaction at A', f"{a['RA']:.3f} kN")
            c[1].metric('Reaction at B', f"{a['RB']:.3f} kN")
            c[2].metric('Maximum shear', f"{a['max_shear']:.3f} kN")
            c[3].metric('Maximum moment', f"{a['max_moment']:.3f} kN·m")
            c = st.columns(4)
            c[0].metric('Max moment location', f"{a['max_moment_x']:.3f} m")
            c[1].metric('Maximum stress', f"{r['sigma']:.3f} MPa")
            c[2].metric('Allowable stress', f"{r['allowable']:.3f} MPa")
            c[3].metric('Utilization ratio', f"{r['util']:.3f}")

            c = st.columns(3)
            with c[0]:
                st.success('Equilibrium check: PASS') if a['force_error']<1e-6 and a['moment_error']<1e-6 else st.error('Equilibrium check: FAIL')
            with c[1]:
                st.success('Boundary check: PASS') if abs(a['moment_at_b'])<0.05 else st.warning('Boundary check: small numerical residual')
            with c[2]:
                st.success('Material check: PASS') if r['util']<=1 else st.error('Material check: DOES NOT PASS')

            st.dataframe(pd.DataFrame([
                ['Section',s['description']],['Area',f"{s['A']:.3e} mm²"],['Moment of inertia, I',f"{s['I']:.3e} mm⁴"],['Section modulus, S',f"{s['S']:.3e} mm³"],
                ['Material',material_name],["Young's modulus, E",f"{mat['E']:.0f} MPa"],[mat['label'],f"{mat['strength']:.3f} MPa"],['Factor of safety',f'{fos:.3f}']
            ], columns=['Property','Value']), use_container_width=True, hide_index=True)
            if r['max_defl'] is not None:
                c = st.columns(2)
                c[0].metric('Maximum absolute deflection', f"{r['max_defl']:.3f} mm")
                c[1].metric('Deflection location', f"{r['max_defl_x']:.3f} m")

        with diagrams_tab:
            fig = plot_fbd(L, r['points'], r['dist'], r['mom'], a['RA'], a['RB']); st.pyplot(fig); plt.close(fig)
            if r['dist']:
                fig = plot_xy(a['x'],a['w'],'Distributed Load Intensity','Load intensity (kN/m)'); st.pyplot(fig); plt.close(fig)
            fig = plot_xy(a['x'],a['V'],'Shear-Force Diagram','Shear force (kN)', marker=(a['max_shear_x'], np.interp(a['max_shear_x'],a['x'],a['V']))); st.pyplot(fig); plt.close(fig)
            fig = plot_xy(a['x'],a['M'],'Bending-Moment Diagram','Bending moment (kN·m)', marker=(a['max_moment_x'],a['max_moment_signed'])); st.pyplot(fig); plt.close(fig)
            if r['defl'] is not None:
                fig = plot_xy(a['x'],r['defl'],'Elastic Deflection Diagram','Deflection (mm)'); st.pyplot(fig); plt.close(fig)

        with steps_tab:
            st.subheader('Step-by-Step Solution')
            st.markdown('### 1. Replace distributed loads with resultants')
            if r['dist']:
                st.dataframe(pd.DataFrame([{'Load':i+1,'Start (m)':d.start,'End (m)':d.end,'w start (kN/m)':d.w_start,'w end (kN/m)':d.w_end,'Resultant (kN)':d.resultant,'Centroid from A (m)':d.centroid} for i,d in enumerate(r['dist'])]), use_container_width=True, hide_index=True)
            else: st.write('No distributed loads entered.')
            st.markdown('### 2. Apply equilibrium')
            st.latex(rf'R_A={a["RA"]:.3f}\ \mathrm{{kN}},\qquad R_B={a["RB"]:.3f}\ \mathrm{{kN}}')
            st.markdown('### 3. Verify equilibrium')
            st.write(f"Vertical-force error = {a['force_error']:.3e} kN")
            st.write(f"Moment error about A = {a['moment_error']:.3e} kN·m")
            st.markdown('### 4. Internal forces')
            st.write(f"Maximum absolute shear = {a['max_shear']:.3f} kN at x = {a['max_shear_x']:.3f} m")
            st.write(f"Maximum absolute moment = {a['max_moment']:.3f} kN·m at x = {a['max_moment_x']:.3f} m")
            st.markdown('### 5. Section properties and bending check')
            st.latex(rf'I={s["I"]:.3e}\ \mathrm{{mm^4}},\qquad S={s["S"]:.3e}\ \mathrm{{mm^3}}')
            st.latex(rf'\sigma_{{max}}={r["sigma"]:.3f}\ \mathrm{{MPa}}')
            st.latex(rf'\sigma_{{allow}}={r["allowable"]:.3f}\ \mathrm{{MPa}}')
            st.latex(rf'U={r["util"]:.3f}')

        with export_tab:
            out = pd.DataFrame({'Position_m':a['x'],'Distributed_Load_kN_per_m':a['w'],'Shear_kN':a['V'],'Moment_kN_m':a['M'],'Deflection_mm':r['defl'] if r['defl'] is not None else np.nan})
            st.download_button('Download Analysis Data', out.to_csv(index=False).encode(), 'beam_analysis_results.csv', 'text/csv')
            summary = f'''INTERACTIVE BEAM ANALYSIS SUMMARY

Beam length: {L:.3f} m
Reaction at A: {a['RA']:.3f} kN
Reaction at B: {a['RB']:.3f} kN
Maximum shear: {a['max_shear']:.3f} kN
Maximum moment: {a['max_moment']:.3f} kN·m
Maximum moment location: {a['max_moment_x']:.3f} m
Maximum bending stress: {r['sigma']:.3f} MPa
Allowable stress: {r['allowable']:.3f} MPa
Utilization ratio: {r['util']:.3f}
Material check: {'PASS' if r['util']<=1 else 'DOES NOT PASS'}
'''
            if r['max_defl'] is not None: summary += f"Maximum deflection: {r['max_defl']:.3f} mm\n"
            st.download_button('Download Text Summary', summary.encode(), 'beam_analysis_summary.txt', 'text/plain')

st.divider()
st.caption('Educational preliminary analysis only. Not a substitute for code-compliant structural design.')
