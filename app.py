import pandas as pd
import streamlit as st

st.set_page_config(page_title="Building Risk Profiling", layout="wide")

st.title("Building Risk Profiling MVP")
st.write("Prototype risk scoring tool for UK residential blocks")


@st.cache_data
def load_data():
    try:
        df = pd.read_csv("sample_buildings.csv")

        if df.empty:
            st.error("sample_buildings.csv is empty.")
            st.stop()

        required_columns = [
            "building_name",
            "region",
            "building_type",
            "storeys",
            "units",
            "fire_risk",
            "damp_mould_risk",
            "compliance_risk",
            "repairs_risk",
            "complaints_risk",
            "cost_risk",
        ]

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(
                "sample_buildings.csv is missing required columns: "
                + ", ".join(missing_columns)
            )
            st.stop()

        return df

    except FileNotFoundError:
        st.error("sample_buildings.csv was not found in the repo root.")
        st.stop()

    except pd.errors.EmptyDataError:
        st.error("sample_buildings.csv exists but contains no readable CSV data.")
        st.stop()

    except Exception as e:
        st.error(f"Unexpected error while loading data: {e}")
        st.stop()


df = load_data()

st.sidebar.header("Filters")

selected_type = st.sidebar.multiselect(
    "Building type",
    options=sorted(df["building_type"].dropna().unique()),
    default=sorted(df["building_type"].dropna().unique()),
)

selected_region = st.sidebar.multiselect(
    "Region",
    options=sorted(df["region"].dropna().unique()),
    default=sorted(df["region"].dropna().unique()),
)

filtered = df[
    (df["building_type"].isin(selected_type)) &
    (df["region"].isin(selected_region))
].copy()

risk_columns = [
    "fire_risk",
    "damp_mould_risk",
    "compliance_risk",
    "repairs_risk",
    "complaints_risk",
    "cost_risk",
]

if filtered.empty:
    st.warning("No buildings match the current filters.")
    st.stop()

filtered["total_risk_score"] = filtered[risk_columns].sum(axis=1)
filtered["portfolio_rank"] = (
    filtered["total_risk_score"].rank(ascending=False, method="dense").astype(int)
)

st.subheader("Portfolio risk table")
st.dataframe(
    filtered[
        [
            "building_name",
            "region",
            "building_type",
            "storeys",
            "units",
            "total_risk_score",
            "portfolio_rank",
        ]
    ].sort_values("total_risk_score", ascending=False),
    use_container_width=True,
)

st.subheader("Building detail")

building = st.selectbox(
    "Select a building",
    sorted(filtered["building_name"].dropna().unique()),
)

record = filtered[filtered["building_name"] == building].iloc[0]

col1, col2, col3 = st.columns(3)
col1.metric("Total Risk Score", int(record["total_risk_score"]))
col2.metric("Portfolio Rank", int(record["portfolio_rank"]))
col3.metric("Storeys", int(record["storeys"]))

st.write("### Risk breakdown")

breakdown = pd.DataFrame(
    {
        "Risk Area": [
            "Fire",
            "Damp and Mould",
            "Compliance",
            "Repairs",
            "Complaints",
            "Cost",
        ],
        "Score": [
            record["fire_risk"],
            record["damp_mould_risk"],
            record["compliance_risk"],
            record["repairs_risk"],
            record["complaints_risk"],
            record["cost_risk"],
        ],
    }
)

st.bar_chart(breakdown.set_index("Risk Area"))

st.write("### Suggested next actions")

actions = []

if record["fire_risk"] >= 15:
    actions.append("Review FRA actions and compartmentation evidence.")
if record["damp_mould_risk"] >= 15:
    actions.append("Investigate root cause of damp and mould and ventilation failure.")
if record["compliance_risk"] >= 15:
    actions.append("Check overdue compliance actions and missing certifications.")
if record["repairs_risk"] >= 15:
    actions.append("Review repeat repairs and backlog on this block.")
if record["complaints_risk"] >= 15:
    actions.append("Review complaint themes and escalation history.")
if record["cost_risk"] >= 15:
    actions.append("Assess reactive spend and forecast capital needs.")

if actions:
    for action in actions:
        st.write(f"- {action}")
else:
    st.write("- No immediate high-risk trigger identified in this prototype.")
