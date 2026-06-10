import streamlit as st
import plotly.graph_objects as go
import requests

API_URL = "http://backend:8000"

TICKERS = {
    "^GSPC": "S&P 500",
    "^DJI": "Dow Jones",
    "^IXIC": "NASDAQ",
    "^FTSE": "FTSE 100",
    "^DAX": "DAX",
    "^FCHI": "CAC 40",
    "^N225": "Nikkei 225",
    "^HSI": "Hang Seng",
    "GC=F": "Gold",
    "BTC-USD": "Bitcoin"
}

COLORS = [
    "#00C805", "#2196F3", "#FF6B35", "#9C27B0",
    "#FF1744", "#00BCD4", "#FFD600", "#FF4081"
]

st.set_page_config(
    page_title="Index Comparator",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Index Comparator")
st.markdown("Compare the performance of multiple indices normalized to base 100")

st.divider()

# Controls
col1, col2 = st.columns([2, 1])

with col1:
    selected_tickers = st.multiselect(
        "Select indices to compare (2-4)",
        options=list(TICKERS.keys()),
        default=["^GSPC", "^IXIC"],
        format_func=lambda x: TICKERS.get(x, x),
        max_selections=4
    )

with col2:
    range_options = {
        "1 Month": {"days": 30},
        "6 Months": {"days": 180},
        "1 Year": {"years": 1},
        "5 Years": {"years": 5},
        "20 Years": {"years": 20},
        "Max": {"years": 100}
    }
    selected_range = st.selectbox(
        "Time range",
        options=list(range_options.keys()),
        index=2
    )

st.divider()

if len(selected_tickers) < 2:
    st.warning("Please select at least 2 indices to compare")
    st.stop()

# Fetch data
params = range_options[selected_range]
response = requests.post(f"{API_URL}/market/compare", json={
    "tickers": selected_tickers,
    **params
})

if response.status_code != 200:
    st.error("Failed to fetch data")
    st.stop()

data = response.json()

# Chart
fig = go.Figure()

for i, ticker in enumerate(selected_tickers):
    if ticker not in data:
        continue
    dates = [row["date"] for row in data[ticker]]
    values =  [row["value"] for row in data[ticker]]
    color = COLORS[i % len(COLORS)]

    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode="lines",
        name=TICKERS.get(ticker, ticker),
        line=dict(color=color, width=2)
    ))

fig.add_hline(
    y=100,
    line_dash="dash",
    line_color="rgba(255,255,255,0.3)",
    annotation_text="Base 100"
)

fig.update_layout(
    height=500,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False, color="#888"),
    yaxis=dict(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.1)",
        color="#888"
    ),
    hovermode="x unified",
    margin=dict(l=0, r=0, t=20, b=0),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# Stats table
st.subheader("Performance Summary")
st.caption("Based on a $100 investment at the start of the selected period")

stats_cols = st.columns(len(selected_tickers))

for i, ticker in enumerate(selected_tickers):
    if ticker not in data or not data[ticker]:
        continue
    values = [row["value"] for row in data[ticker]]
    total_return = values[-1] - 100
    max_drawup = max(values) - 100
    max_drawdown = min(values) - 100

    with stats_cols[i]:
        st.metric(
            label=TICKERS.get(ticker, ticker),
            value=f"${values[-1]:.1f}",
            delta=f"{total_return:+.1f}% total return"
        )
        st.caption(f"📈 Best: +{max_drawup:.1f}% | 📉 Worst: {max_drawdown:.1f}%")
