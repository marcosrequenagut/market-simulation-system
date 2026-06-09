import streamlit as st
import plotly.graph_objects as go
import requests
from datetime import datetime

API_URL = "http://backend:8000"
DEFAULT_TICKER = "^GSPC"

st.set_page_config(
    page_title="Market Analyzer",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Market Analyzer")

# Select ticker
col_ticker, col_empty = st.columns([1, 3])
with col_ticker:
    ticker = st.selectbox(
        "Select Index",
        options=["^GSPC", "^DJI", "^IXIC", "^FTSE", "^DAX", "^FCHI", "^N225", "^HSI", "GC=F", "BTC-USD"],
        format_func=lambda x: {
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
        }.get(x, x)
    )

# Calculate the metrics
latest = requests.get(f"{API_URL}/market/{ticker}/latest").json()
prices_2d = requests.get(f"{API_URL}/market/{ticker}/prices", params={"limit": 2}).json()
prices_2d = list(reversed(prices_2d))

today_price = prices_2d[-1]["close"]
yesterday_price = prices_2d[-2]["close"] if len(prices_2d) >= 2 else today_price
change = today_price - yesterday_price
change_pct = (change / yesterday_price) * 100
color = "normal" if change >= 0 else "inverse"

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    st.metric(
        label="Today",
        value=f"${today_price:,.2f}",
        delta=f"{change_pct:+.2f}%",
        delta_color=color
    )
with col2:
    st.metric(
        label="Previous close",
        value=f"${yesterday_price:,.2f}"
    )

st.divider()

# Select time range
st.subheader("S&P 500 Price History")

range_options = {
    "5 Days": {"days": 7}, # 7 days to cover all the week, not counting weekends
    "1 Month": {"days": 30},
    "6 Months": {"days": 180},
    "1 Year": {"years": 1},
    "5 Years": {"years": 5},
    "20 Years": {"years": 20},
    "Max": {"years": 100}
}

selected_range = st.radio(
    "Select range",
    options=list(range_options.keys()),
    index=5,
    horizontal=True
)

params = range_options[selected_range]
data = requests.get(f"{API_URL}/market/{ticker}/history", params=params).json()

dates = [row["date"] for row in data]
closes = [row["close"] for row in data]

# Make the chart
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=dates,
    y=closes,
    mode="lines",
    name=ticker,
    line=dict(color="#00C805", width=1.5),
    fill="tozeroy",
    fillcolor="rgba(0, 200, 5, 0.05)"
))

y_min = min(closes) * 0.98
y_max = max(closes) * 1.02

fig.update_layout(
    height=500,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(
        showgrid=False,
        showline=False,
        color="#888"
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.1)",
        color="#888",
        tickprefix="$",
        range=[y_min, y_max]
    ),
    hovermode="x unified",
    margin=dict(l=0, r=0, t=20, b=0)
)

st.plotly_chart(fig, use_container_width=True)