"""
Margarine (Table Spread) Batch Production Dashboard
-----------------------------------------------------
Run locally with:
    pip install streamlit pandas plotly numpy
    streamlit run batch_dashboard.py

All data is embedded in this file (from the July 2026 batch manufacturing
record) so no external CSV/Excel is required. Edit the DATA section below
to plug in new batches.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =====================================================================
# PAGE CONFIG
# =====================================================================
st.set_page_config(
    page_title="Margarine Batch Production Dashboard",
    page_icon="🧈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================
# 1. DATA
# =====================================================================

# ---- Batch-level metadata (one row per batch) --------------------------------
batches_meta = pd.DataFrame([
    dict(job="E2667373", batch="P4 B1 042826", date="2026-07-09", operators="Daniel",                       total_kg=2501.2),
    dict(job="E2667373", batch="P4 B2 042826", date="2026-07-09", operators="Daniel",                       total_kg=2501.2),
    dict(job="E2667590", batch="P4 B3 062826", date="2026-07-11", operators="Daniel",                       total_kg=2501.2),
    dict(job="E2667590", batch="P4 B2 062826", date="2026-07-11", operators="Daniel",                       total_kg=2501.2),
    dict(job="E2667590", batch="P4 B1 062826", date="2026-07-11", operators="Daniel",                       total_kg=2576.2),
    dict(job="E2669297", batch="P4 B1 052926", date="2026-07-17", operators="Abubakar, Alex and Daniel",    total_kg=2501.2),
    dict(job="E2671282", batch="P4 B1 053026", date="2026-07-24", operators="Dennis and Brian",             total_kg=2502.2),
    dict(job="E2671282", batch="P4 B2 053026", date="2026-07-24", operators="Daniel and Alex",              total_kg=2501.2),
    dict(job="E2671282", batch="P4 B3 053026", date="2026-07-24", operators="Daniel and Alex",              total_kg=2501.2),
    dict(job="E2671458", batch="P4 B1 013126", date="2026-07-27", operators="Abubakar and Godfrey",         total_kg=2503.2),
    dict(job="E2671458", batch="P4 B2 013126", date="2026-07-27", operators="Abubakar and Celevesta",       total_kg=2501.2),
    dict(job="E2671458", batch="P4 B3 013126", date="2026-07-27", operators="Abubakar and Celevesta",       total_kg=2502.2),
    dict(job="E2671458", batch="P4 B4 013126", date="2026-07-27", operators="Daniel and Celevesta",         total_kg=2501.2),
])
batches_meta["date"] = pd.to_datetime(batches_meta["date"])
batches_meta.insert(0, "batch_id", batches_meta["job"] + " | " + batches_meta["batch"])

BATCH_IDS = batches_meta["batch_id"].tolist()

# ---- Job-level output / process-loss (recorded once per job, not per batch) --
job_summary = pd.DataFrame([
    dict(job="E2667373", output_cartons=735,  process_loss_kg=592.4),
    dict(job="E2667590", output_cartons=1188, process_loss_kg=450.6),
    dict(job="E2669297", output_cartons=351,  process_loss_kg=395.5),
    dict(job="E2671282", output_cartons=1199, process_loss_kg=310.6),
    dict(job="E2671458", output_cartons=810,  process_loss_kg=287.8),
])
job_kg = batches_meta.groupby("job", as_index=False)["total_kg"].sum().rename(columns={"total_kg": "job_total_kg"})
job_summary = job_summary.merge(job_kg, on="job")
job_summary["loss_pct"] = (job_summary["process_loss_kg"] / job_summary["job_total_kg"] * 100).round(2)
job_summary["cartons_per_100kg"] = (job_summary["output_cartons"] / job_summary["job_total_kg"] * 100).round(2)

# ---- Component (formula/recipe) matrix: 20 components x 13 batches -----------
components = [
    ("OTMCA0001264", "Citric Acid Anhydrous 25kg",              [0.5]*13),
    ("PUAAB0012843", "Butter Flavour - Table Margarine",        [0.5]*13),
    ("PUAAC0012844", "Creamy Flavour - Table Margarine",        [3.25]*13),
    ("PUAAD0013685", "Dimodan HP Distilled Monoglyceride",      [5]*13),
    ("PUAAE0005964", "Soya Lecithin",                           [7.5]*13),
    ("PUAAG0013683", "Grindsted Crystal Clean 20",              [50]*13),
    ("PUOAE0000233", "GMS (Normal Emulsifier)",                 [5]*13),
    ("PUAAH0011544", "Hydrogenated Palm Kernel Oil",            [200]*13),
    ("PUAAM0005966", "Milk Powder",                             [50]*13),
    ("PUAAM0012845", "Milk Flavour - Table Margarine",          [0.125]*13),
    ("PUAAS0011649", "Sodium Benzoate BP 98 (Food Grade)",      [2.5]*13),
    ("PUAOS0006011", "Baker's (Fine) Salt",                     [62.5]*13),
    ("PUOAB0000219", "Betacarotine",                            [0.075]*13),
    ("PUOAP0000243", "Potassium Sorbate",                       [2.5]*13),
    ("PUOAV0000253", "Vitamin A&D",                             [0.25]*13),
    ("PUOGB0000286", "BHT",                                     [0.5]*13),
    ("PUOOS0005963", "Sunflower Oil",                           [25]*13),
    ("PUROD0012133", "Demineralized Water",                     [400,400,400,400,475,400,400,400,400,401,400,400,400]),
    ("SFOOH0000706", "Olein High Cloud",                        [337,338,338,338,338,338,339,338,338,338,338,337,338]),
    ("SFOOR0000702", "RBD",                                     [1349,1348,1348,1348,1348,1348,1348,1348,1348,1349,1348,1350,1348]),
]

comp_df = pd.DataFrame(
    {name: qty for _, name, qty in components},
    index=BATCH_IDS,
).T
comp_df.insert(0, "component_code", [c[0] for c in components])
comp_df.index.name = "component"

# Long/tidy format for plotting
comp_long = comp_df.reset_index().melt(
    id_vars=["component", "component_code"], var_name="batch_id", value_name="qty_kg"
)
comp_long = comp_long.merge(batches_meta, on="batch_id")

# Standard ("reference") recipe amount per component = the mode across batches
ref_qty = comp_df.drop(columns="component_code").mode(axis=1)[0]
STANDARD_TOTAL_KG = ref_qty.sum()  # theoretical standard batch weight

# Flag anomaly note
ANOMALY_BATCH = "E2667590 | P4 B1 062826"
ANOMALY_NOTE = "Dm water off quantity due to tank weight inconsistency"

# =====================================================================
# 2. SIDEBAR FILTERS
# =====================================================================
st.sidebar.title("🧈 Filters")
st.sidebar.caption("Table Margarine — Product P4 — July 2026 batches")

job_options = ["All"] + sorted(batches_meta["job"].unique().tolist())
sel_job = st.sidebar.selectbox("Job Number", job_options)

date_options = ["All"] + sorted(batches_meta["date"].dt.strftime("%d/%m/%Y").unique().tolist())
sel_date = st.sidebar.selectbox("Production Date", date_options)

all_operators = sorted(set(
    op.strip() for ops in batches_meta["operators"] for op in ops.replace(" and ", ",").split(",")
))
sel_operators = st.sidebar.multiselect("Operator(s) involved", all_operators, default=[])

filtered = batches_meta.copy()
if sel_job != "All":
    filtered = filtered[filtered["job"] == sel_job]
if sel_date != "All":
    filtered = filtered[filtered["date"].dt.strftime("%d/%m/%Y") == sel_date]
if sel_operators:
    mask = filtered["operators"].apply(
        lambda ops: any(o in ops for o in sel_operators)
    )
    filtered = filtered[mask]

if filtered.empty:
    st.sidebar.warning("No batches match the selected filters — showing all batches instead.")
    filtered = batches_meta.copy()

st.sidebar.markdown("---")
st.sidebar.metric("Batches in view", len(filtered))
st.sidebar.metric("Jobs in view", filtered["job"].nunique())

with st.sidebar.expander("⬇️ Download raw data"):
    st.download_button(
        "Batch metadata (CSV)",
        batches_meta.drop(columns="batch_id").to_csv(index=False),
        file_name="batch_metadata.csv",
    )
    st.download_button(
        "Component matrix (CSV)",
        comp_df.to_csv(),
        file_name="component_matrix.csv",
    )
    st.download_button(
        "Job summary (CSV)",
        job_summary.to_csv(index=False),
        file_name="job_summary.csv",
    )

# =====================================================================
# 3. HEADER + KPI ROW
# =====================================================================
st.title("🧈 Table Margarine — Batch Production Dashboard")
st.caption(
    f"Product P4 formula • {batches_meta['job'].nunique()} jobs • "
    f"{len(batches_meta)} batches • "
    f"{batches_meta['date'].min():%d %b} – {batches_meta['date'].max():%d %b %Y}"
)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total batches (filtered)", len(filtered))
k2.metric("Total batch weight", f"{filtered['total_kg'].sum():,.1f} kg")
k3.metric("Avg batch weight", f"{filtered['total_kg'].mean():,.1f} kg")

jobs_in_view = job_summary[job_summary["job"].isin(filtered["job"].unique())]
k4.metric("Total output (cartons)", f"{jobs_in_view['output_cartons'].sum():,.0f}")
k5.metric("Total process loss", f"{jobs_in_view['process_loss_kg'].sum():,.1f} kg")

st.info(f"⚠️ **Batch note** — *{ANOMALY_BATCH}*: {ANOMALY_NOTE}", icon="⚠️")

st.markdown("---")

# =====================================================================
# 4. TABS
# =====================================================================
tab_overview, tab_batches, tab_recipe, tab_operators, tab_data = st.tabs(
    ["📊 Overview", "🧪 Batch Weights", "🧾 Recipe / Formula", "👷 Operators", "📋 Full Data"]
)

# ---------------------------------------------------------------------
# TAB 1 — OVERVIEW (job-level)
# ---------------------------------------------------------------------
with tab_overview:
    c1, c2 = st.columns(2)

    with c1:
        fig = px.bar(
            job_summary, x="job", y="output_cartons",
            title="Output (Cartons) by Job",
            text="output_cartons", color="output_cartons",
            color_continuous_scale="Greens",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(coloraxis_showscale=False, yaxis_title="Cartons", xaxis_title="Job Number")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.bar(
            job_summary, x="job", y="process_loss_kg",
            title="Process Loss (kg) by Job",
            text="process_loss_kg", color="process_loss_kg",
            color_continuous_scale="Reds",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(coloraxis_showscale=False, yaxis_title="Loss (kg)", xaxis_title="Job Number")
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        fig = px.bar(
            job_summary, x="job", y="loss_pct",
            title="Process Loss as % of Total Input Weight",
            text=job_summary["loss_pct"].astype(str) + "%",
            color="loss_pct", color_continuous_scale="OrRd",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(coloraxis_showscale=False, yaxis_title="Loss %", xaxis_title="Job Number")
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        fig = px.bar(
            job_summary, x="job", y="cartons_per_100kg",
            title="Yield — Cartons per 100 kg Input",
            text="cartons_per_100kg", color="cartons_per_100kg",
            color_continuous_scale="Blues",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(coloraxis_showscale=False, yaxis_title="Cartons / 100kg", xaxis_title="Job Number")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Job Summary Table")
    st.dataframe(
        job_summary.rename(columns={
            "job": "Job Number", "output_cartons": "Output (Cartons)",
            "process_loss_kg": "Process Loss (kg)", "job_total_kg": "Total Input (kg)",
            "loss_pct": "Loss %", "cartons_per_100kg": "Cartons / 100kg",
        }),
        use_container_width=True, hide_index=True,
    )

    st.subheader("Production Timeline")
    timeline = batches_meta.groupby("date").agg(batches=("batch", "count"), total_kg=("total_kg", "sum")).reset_index()
    fig = go.Figure()
    fig.add_bar(x=timeline["date"], y=timeline["batches"], name="Batches produced", marker_color="#2E86AB")
    fig.add_trace(go.Scatter(x=timeline["date"], y=timeline["total_kg"] / 500, name="Total kg (÷500, scaled)",
                              mode="lines+markers", yaxis="y2", line=dict(color="#F26419", width=3)))
    fig.update_layout(
        title="Batches Produced & Weight Processed per Day",
        xaxis_title="Date", yaxis=dict(title="Batches produced"),
        yaxis2=dict(title="Total kg (scaled)", overlaying="y", side="right"),
        legend=dict(orientation="h", y=1.15),
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------
# TAB 2 — BATCH WEIGHTS
# ---------------------------------------------------------------------
with tab_batches:
    st.subheader("Total Batch Weight vs. Standard")
    fig = px.bar(
        filtered.sort_values("date"), x="batch", y="total_kg", color="job",
        title="Total Batch Weight (kg) — colored by Job",
        hover_data=["date", "operators"],
    )
    fig.add_hline(y=STANDARD_TOTAL_KG, line_dash="dash", line_color="gray",
                  annotation_text=f"Standard formula ≈ {STANDARD_TOTAL_KG:,.1f} kg", annotation_position="top left")
    fig.update_layout(xaxis_title="Batch", yaxis_title="Total weight (kg)", xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Batch Deviation from Standard Formula Weight")
    dev = filtered.copy()
    dev["deviation_kg"] = dev["total_kg"] - STANDARD_TOTAL_KG
    fig = px.bar(
        dev.sort_values("date"), x="batch", y="deviation_kg", color="deviation_kg",
        color_continuous_scale="RdYlGn_r", title="Deviation from Standard (kg)",
    )
    fig.update_layout(coloraxis_showscale=False, xaxis_title="Batch", yaxis_title="Deviation (kg)", xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        f"Standard formula total = **{STANDARD_TOTAL_KG:,.1f} kg** (most common batch weight). "
        f"Batch **{ANOMALY_BATCH.split(' | ')[1]}** deviates by "
        f"**+{2576.2 - STANDARD_TOTAL_KG:,.1f} kg** — consistent with the logged water tank issue."
    )

    st.subheader("Variable Raw Materials Across Batches")
    variable_components = ["Demineralized Water", "Olein High Cloud", "RBD"]
    sel_var = st.selectbox("Select a variable component to inspect", variable_components)
    vc = comp_long[comp_long["component"] == sel_var].merge(
        filtered[["batch_id"]], on="batch_id"
    ).sort_values("date")
    ref_val = ref_qty[sel_var]
    fig = px.line(
        vc, x="batch", y="qty_kg", markers=True, color="job",
        title=f"{sel_var} — Quantity per Batch (kg)",
        hover_data=["date", "operators"],
    )
    fig.add_hline(y=ref_val, line_dash="dot", line_color="gray",
                  annotation_text=f"Standard = {ref_val:g} kg", annotation_position="bottom right")
    fig.update_layout(xaxis_title="Batch", yaxis_title="kg", xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------
# TAB 3 — RECIPE / FORMULA
# ---------------------------------------------------------------------
with tab_recipe:
    st.subheader("Inspect a Single Batch's Full Formula")
    sel_batch = st.selectbox("Choose a batch", filtered["batch_id"].tolist())
    row = batches_meta[batches_meta["batch_id"] == sel_batch].iloc[0]

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Job Number", row["job"])
    b2.metric("Batch Number", row["batch"])
    b3.metric("Date", row["date"].strftime("%d/%m/%Y"))
    b4.metric("Total Weight", f"{row['total_kg']:,.1f} kg")
    st.caption(f"Operator(s): **{row['operators']}**")
    if sel_batch == ANOMALY_BATCH:
        st.warning(f"⚠️ {ANOMALY_NOTE}")

    batch_recipe = comp_long[comp_long["batch_id"] == sel_batch].sort_values("qty_kg", ascending=False)

    c1, c2 = st.columns([1.2, 1])
    with c1:
        fig = px.bar(
            batch_recipe, x="qty_kg", y="component", orientation="h",
            title="Component Quantities (kg)", text="qty_kg",
            color="qty_kg", color_continuous_scale="Teal",
        )
        fig.update_traces(texttemplate="%{text:.3g}", textposition="outside")
        fig.update_layout(coloraxis_showscale=False, yaxis=dict(categoryorder="total ascending"), height=600)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.treemap(
            batch_recipe, path=["component"], values="qty_kg",
            title="Formula Composition (share of batch weight)",
        )
        fig.update_traces(textinfo="label+percent root")
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("View full formula table"):
        st.dataframe(
            batch_recipe[["component_code", "component", "qty_kg"]].rename(
                columns={"component_code": "Component Code", "component": "Component", "qty_kg": "Quantity (kg)"}
            ),
            use_container_width=True, hide_index=True,
        )

    st.markdown("---")
    st.subheader("Compare Recipe Consistency Across All Batches (Heatmap)")
    heat = comp_df.drop(columns="component_code")
    fig = px.imshow(
        heat, aspect="auto", color_continuous_scale="Viridis",
        labels=dict(x="Batch", y="Component", color="kg"),
        title="Component Quantity (kg) — All Batches",
    )
    fig.update_layout(height=650, xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Almost all components are constant across batches — the heatmap makes the rare "
               "variations (water, Olein High Cloud, RBD) easy to spot as faint banding.")

# ---------------------------------------------------------------------
# TAB 4 — OPERATORS
# ---------------------------------------------------------------------
with tab_operators:
    st.subheader("Batches per Operator")
    op_rows = []
    for _, r in batches_meta.iterrows():
        for op in r["operators"].replace(" and ", ",").split(","):
            op_rows.append(dict(operator=op.strip(), batch=r["batch"], job=r["job"], date=r["date"], total_kg=r["total_kg"]))
    op_df = pd.DataFrame(op_rows)

    op_counts = op_df.groupby("operator", as_index=False).agg(
        batches=("batch", "count"), total_kg=("total_kg", "sum")
    ).sort_values("batches", ascending=False)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(op_counts, x="operator", y="batches", title="Number of Batches Worked, by Operator",
                     text="batches", color="batches", color_continuous_scale="Purples")
        fig.update_traces(textposition="outside")
        fig.update_layout(coloraxis_showscale=False, xaxis_title="Operator", yaxis_title="Batches")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.pie(op_counts, names="operator", values="total_kg",
                     title="Share of Total Batch Weight Handled, by Operator", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Operator Pairings (co-working)")
    pair_counts = batches_meta["operators"].value_counts().reset_index()
    pair_counts.columns = ["Operator team", "Batches"]
    st.dataframe(pair_counts, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------
# TAB 5 — FULL DATA
# ---------------------------------------------------------------------
with tab_data:
    st.subheader("Batch Metadata")
    st.dataframe(
        filtered.drop(columns="batch_id").rename(columns={
            "job": "Job Number", "batch": "Batch Number", "date": "Date",
            "operators": "Operator(s)", "total_kg": "Total (kg)",
        }),
        use_container_width=True, hide_index=True,
    )

    st.subheader("Full Component Matrix (all batches)")
    st.dataframe(comp_df, use_container_width=True)

    st.subheader("Job-Level Summary")
    st.dataframe(job_summary, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Dashboard built with Streamlit + Plotly · Edit the DATA section at the top of this file to add new batches.")
