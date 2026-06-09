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

st.set_page_config(
    page_title="Investment Simulator",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Simulate Your Investment")
st.markdown("Calculate how your investment would grow over time based on historical data.")

st.divider()

# Ticker selection
col_ticker, col_empty = st.columns([1, 3])
with col_ticker:
    ticker = st.selectbox(
        "Select Ticker",
        options=list(TICKERS.keys()),
        format_func=lambda x: TICKERS.get(x, x)
    )

# Load historical stats
stats = requests.get(f"{API_URL}/market/{ticker}/stats").json()
default_rate = round(stats.get("cagr", 0.07) * 100, 2)
default_volatility = round(stats.get("annual_volatility", 0.15) * 100, 2)

st.info(f"📊 Historical CAGR for {TICKERS[ticker]}: **{default_rate}%** | Historical Volatility: **{default_volatility}%**")

st.divider()

# Inputs
col1, col2, col3, col4 = st.columns(4)

with col1:
    initial_investment = st.number_input(
        "Initial Investment ($)",
        min_value=0,
        max_value=1000000,
        value=100,
        step=100
    )

with col2:
    monthly_contribution = st.number_input(
        "Monthly Contribution  ($)",
        min_value=0,
        max_value=100000,
        value=100,
        step=50
    )

with col3:
    years = st.number_input(
        "Investment Period (years)",
        min_value=1,
        max_value=50,
        value=10,
        step=1
    )

with col4:
    annual_rate = st.number_input(
        "Expected Annual Return (%)",
        min_value=0.0,
        max_value=30.0,
        value=7.0,
        step=0.5
    ) / 100

st.divider()

# Simulate
if st.button("Simulate", type="primary", use_container_width=True):
    response = requests.post(f"{API_URL}/simulate/", json={
        "initial_investment": initial_investment,
        "monthly_contribution": monthly_contribution,
        "annual_rate": annual_rate,
        "annual_volatility": stats.get("annual_volatility", 0.15),
        "years": years,
        "simulations": 1000,
        "model": "lognormal"
    })
    if response.status_code == 200:
        data = response.json()
        compound = data["compound_interest"]
        monte_carlo = data["monte_carlo"]

        # Metrics
        st.subheader("Results")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label="Total invested",
                value=f"${compound['total_invested']:,.0f}"
            )
        with col2:
            st.metric(
                label="Final value (base case)",
                value=f"${compound['final_value']:,.0f}",
                delta=f"{compound['total_interest']:,.0f} interest"
            )
        with col3:
            roi = (compound["total_interest"] / compound["total_invested"]) * 100 if compound["total_invested"] > 0 else 0
            st.metric(
                label="Return on Investment",
                value=f"{roi:.1f}%"
            )

        st.divider()

        # Monte Carlo Simulation
        st.subheader("Monte Carlo Scenarios (1000 simulations)")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="🔴 Pessimistic (p10)",
                value=f"${monte_carlo['p10']:,.0f}"
            )
        with col2:
            st.metric(
                label="🟡 Base (p50)",
                value=f"${monte_carlo['p50']:,.0f}"
            )
        with col3:
            st.metric(
                label="🟢 Optimistic (p90)",
                value=f"${monte_carlo['p90']:,.0f}"
            )

        # Make the chart
        st.divider()
        st.subheader("Investment Growth Over Time")

        months = list(range(0, years * 12 + 1))
        monthly_rate = annual_rate / 12
        balance = initial_investment
        evolution = [balance]

        for _ in range(years * 12):
            balance = balance * (1 + monthly_rate) + monthly_contribution
            evolution.append(round(balance, 2))

        total_invested_evolution = [
            initial_investment + monthly_contribution * i
            for i in range(years * 12 + 1)
        ]

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=months,
            y=evolution,
            mode="lines",
            name="Portfolio Value",
            line=dict(color="#00C805", width=2),
            fill="tozeroy",
            fillcolor="rgba(0, 200, 5, 0.05)"
        ))

        fig.add_trace(go.Scatter(
            x=months,
            y=total_invested_evolution,
            mode="lines",
            name="Total Invested",
            line=dict(color="#888888", width=1.5, dash="dash")
        ))

        fig.update_layout(
            height=400,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                showgrid=False,
                color="#888",
                title="Months"
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.1)",
                color="#888",
                tickprefix="$"
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

    else:
        st.error("Failed to simulate investment")
        st.write(response.text)
