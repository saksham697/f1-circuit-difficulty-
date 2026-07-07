"""
F1 Circuit Difficulty Profile — Streamlit app
=============================================
Interactive map of every circuit with its real track outline. Click a circuit
(on the map or in the selector) to see its difficulty profile — chaos score,
DNF rate, pole-to-win conversion, and how it ranks processional vs chaotic.

Data: pre-computed from the MySQL analytics pipeline (v_circuit_profile) and
merged with track-outline geometry (bacinger/f1-circuits, GeoJSON). Bundled as
app_data.json so the deployed app needs no database and no network.

Run locally:   streamlit run app.py
Deploy:        push to GitHub -> share.streamlit.io -> pick repo -> app.py
"""
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium
import folium

# ----------------------------------------------------------------------------
# Page + theme
# ----------------------------------------------------------------------------
st.set_page_config(page_title="F1 Circuit Difficulty Profile",
                   page_icon="🏁", layout="wide")

RED, TEAL, INK, MUT = "#E10600", "#00D2BE", "#E6EDF3", "#8A94A6"
PANEL, BG = "#121722", "#0B0E14"
LABEL_COLOR = {"Chaotic": RED, "Mixed": "#FF8700", "Processional": TEAL}

st.markdown(f"""
<style>
    .stApp {{ background:{BG}; }}
    .block-container {{ padding-top:1.4rem; }}
    h1,h2,h3 {{ color:{INK}; font-weight:700; letter-spacing:.3px; }}
    .metric-card {{
        background:{PANEL}; border:1px solid #1e2636; border-radius:14px;
        padding:16px 18px; margin-bottom:10px;
    }}
    .metric-card .label {{ color:{MUT}; font-size:.72rem; text-transform:uppercase;
        letter-spacing:1px; margin-bottom:4px; }}
    .metric-card .value {{ color:{INK}; font-size:1.7rem; font-weight:700; }}
    .pill {{ display:inline-block; padding:3px 12px; border-radius:999px;
        font-weight:700; font-size:.8rem; }}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------
@st.cache_data
def load_data():
    with open("app_data.json", encoding="utf-8") as f:
        raw = json.load(f)
    df = pd.DataFrame(raw["circuits"])
    return df

df = load_data()

st.title("🏁 F1 Circuit Difficulty Profile")
st.markdown(
    f"<span style='color:{MUT}'>Which circuits are processional processions — and "
    f"which are chaos? Built from 25 years of race data (grid→finish moves, DNF "
    f"rates, pole conversion) scored into a single chaos index. "
    f"<b>Click any circuit</b> to explore.</span>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Sidebar filters
# ----------------------------------------------------------------------------
with st.sidebar:
    st.header("Filters")
    labels = st.multiselect("Profile", ["Chaotic", "Mixed", "Processional"],
                            default=["Chaotic", "Mixed", "Processional"])
    min_races = st.slider("Minimum races held", 8, int(df.n_races.max()), 8)
    countries = st.multiselect("Country", sorted(df.country.unique()))
    st.caption("Data: MySQL analytics pipeline + bacinger/f1-circuits outlines")

view = df[df.profile_label.isin(labels) & (df.n_races >= min_races)]
if countries:
    view = view[view.country.isin(countries)]

# selector (kept in sync with the map)
names = view.sort_values("chaos_score", ascending=False)["circuit_name"].tolist()
if "selected" not in st.session_state or st.session_state.selected not in names:
    st.session_state.selected = names[0] if names else None

# ----------------------------------------------------------------------------
# Layout: map (left) + detail panel (right)
# ----------------------------------------------------------------------------
left, right = st.columns([1.5, 1], gap="large")

with left:
    st.subheader("Circuit map")
    m = folium.Map(location=[25, 10], zoom_start=2, tiles="CartoDB dark_matter",
                   world_copy_jump=True)
    for _, r in view.iterrows():
        color = LABEL_COLOR.get(r.profile_label, MUT)
        # track outline
        if r.track_coords:
            folium.PolyLine(r.track_coords, color=color, weight=3, opacity=0.9).add_to(m)
        # clickable marker at circuit centroid
        folium.CircleMarker(
            location=[r.map_lat, r.map_lng], radius=6,
            color=color, fill=True, fill_color=color, fill_opacity=0.9,
            tooltip=f"{r.circuit_name} — {r.profile_label} ({r.chaos_score:.2f})",
            popup=r.circuit_name,
        ).add_to(m)
    out = st_folium(m, height=460, width='stretch',
                    returned_objects=["last_object_clicked_popup"])
    if out and out.get("last_object_clicked_popup"):
        st.session_state.selected = out["last_object_clicked_popup"]

    # fallback / explicit selector
    sel_name = st.selectbox("…or pick a circuit", names,
                            index=names.index(st.session_state.selected)
                            if st.session_state.selected in names else 0)
    st.session_state.selected = sel_name

# ----------------------------------------------------------------------------
# Detail panel for the selected circuit
# ----------------------------------------------------------------------------
sel = view[view.circuit_name == st.session_state.selected]
with right:
    if sel.empty:
        st.info("No circuit selected — adjust filters.")
    else:
        c = sel.iloc[0]
        color = LABEL_COLOR.get(c.profile_label, MUT)
        st.subheader(c.circuit_name)
        st.markdown(
            f"<span class='pill' style='background:{color}22;color:{color};"
            f"border:1px solid {color}'>{c.profile_label}</span> "
            f"<span style='color:{MUT}'>&nbsp;{c.country} · "
            f"{int(c.n_races)} races</span>", unsafe_allow_html=True)

        # mini track-shape plot
        if c.track_coords:
            lats = [p[0] for p in c.track_coords]
            lngs = [p[1] for p in c.track_coords]
            tfig = go.Figure(go.Scatter(x=lngs, y=lats, mode="lines",
                             line=dict(color=color, width=3)))
            tfig.update_layout(
                height=190, margin=dict(l=0, r=0, t=6, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
                yaxis=dict(visible=False))
            if c.track_length_m:
                tfig.add_annotation(text=f"{c.track_length_m/1000:.2f} km",
                    xref="paper", yref="paper", x=0.02, y=0.98,
                    showarrow=False, font=dict(color=MUT, size=12))
            st.plotly_chart(tfig, width='stretch',
                            config={"displayModeBar": False})

        def card(label, value):
            st.markdown(f"<div class='metric-card'><div class='label'>{label}</div>"
                        f"<div class='value'>{value}</div></div>",
                        unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            card("Chaos score", f"{c.chaos_score:.2f}")
            card("DNF rate", f"{c.dnf_rate:.0%}")
            card("Avg positions gained", f"{c.avg_positions_gained:+.2f}")
        with g2:
            card("Pole → win", f"{c.pole_to_win_rate:.0%}")
            card("Grid→finish corr", f"{c.grid_finish_corr:.2f}")
            card("Unique winners", f"{int(c.unique_winners)}")

# ----------------------------------------------------------------------------
# Dashboard charts (full width, below)
# ----------------------------------------------------------------------------
st.markdown("---")
st.subheader("How the field compares")

tab1, tab2, tab3 = st.tabs(["Chaos ranking", "Processional ↔ Chaotic map", "Data table"])

with tab1:
    d = view.sort_values("chaos_score")
    bar = go.Figure(go.Bar(
        x=d.chaos_score, y=d.circuit_name, orientation="h",
        marker=dict(color=d.chaos_score, colorscale=[[0, TEAL], [0.5, "#FFF200"], [1, RED]],
                    line=dict(color="#0B0E14", width=0.5)),
        hovertemplate="%{y}<br>chaos %{x:.2f}<extra></extra>"))
    bar.update_layout(height=max(420, 22*len(d)), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font_color=INK,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(title="chaos score", gridcolor="#1e2636"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"))
    st.plotly_chart(bar, width='stretch')

with tab2:
    sc = go.Figure()
    for lab in ["Chaotic", "Mixed", "Processional"]:
        dd = view[view.profile_label == lab]
        if dd.empty:
            continue
        sc.add_trace(go.Scatter(
            x=dd.grid_finish_corr, y=dd.dnf_rate, mode="markers+text",
            text=dd.circuit_name, textposition="top center",
            textfont=dict(size=8, color=MUT), name=lab,
            marker=dict(size=8 + dd.n_races, color=LABEL_COLOR[lab],
                        line=dict(color="#0B0E14", width=1)),
            hovertemplate="%{text}<br>corr %{x:.2f} · DNF %{y:.0%}<extra></extra>"))
    sc.add_vline(x=view.grid_finish_corr.median(), line_dash="dash", line_color=MUT)
    sc.add_hline(y=view.dnf_rate.median(), line_dash="dash", line_color=MUT)
    sc.update_layout(height=560, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font_color=INK,
        xaxis=dict(title="Grid→Finish correlation  (→ processional)", gridcolor="#1e2636"),
        yaxis=dict(title="DNF rate  (↑ chaotic)", gridcolor="#1e2636"),
        legend=dict(bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(sc, width='stretch')

with tab3:
    show = view.sort_values("chaos_score", ascending=False)[[
        "circuit_name", "country", "profile_label", "n_races", "chaos_score",
        "dnf_rate", "pole_to_win_rate", "grid_finish_corr", "avg_positions_gained"]]
    st.dataframe(show, width='stretch', hide_index=True,
                 column_config={
                    "chaos_score": st.column_config.ProgressColumn(
                        "Chaos", min_value=0, max_value=1, format="%.2f"),
                    "dnf_rate": st.column_config.NumberColumn("DNF", format="%.0f%%"),
                    "pole_to_win_rate": st.column_config.NumberColumn("Pole→Win", format="%.0f%%"),
                 })

st.caption("Chaos score is a weighted blend of DNF rate, position volatility, "
           "grid→finish correlation and pole-to-win conversion, min–max normalized "
           "across circuits. Weights are a design choice — see project README.")
