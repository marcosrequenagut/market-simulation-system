import streamlit as st
import plotly.graph_objects as go
import requests
from datetime import datetime

API_URL = "http://backend:8000"

st.set_page_config(
    page_title="S&P 500 Analyzer",
    page_icon="📈",
    layout="wide"
)

st.title("📈 S&P 500 Analyzer")

# Calculate the metrics
# A 7-day window is used to account for weekends and market holidays.
# In practice, we retrieve the latest available trading days rather than seven actual trading days,
# ensuring that at least two market days are available for calculations.
latest = requests.get(f"{API_URL}/sp500/latest").json()
prices_2d = requests.get(f"{API_URL}/sp500/prices/history", params={"days": 7}).json() # 7 days to cover all the week, not counting weekends

today_price = latest["close"]
yesterday_price = prices_2d[-2]["close"] if len(prices_2d) >= 7 else today_price # 7 days to cover all the week, not counting weekends
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
        label="Yesterday",
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
data = requests.get(f"{API_URL}/sp500/prices/history", params=params).json()

dates = [row["date"] for row in data]
closes = [row["close"] for row in data]

# Make the chart
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=dates,
    y=closes,
    mode="lines",
    name="S&P 500",
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