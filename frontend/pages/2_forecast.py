import streamlit as st
import plotly.graph_objects as go
import requests

API_URL = "http://backend:8000"

TICKERS = {
    "^GSPC": "S&P 500",
    "^DJI": "Dow Jones",
    "^IXIC": "NASDAQ",
    "^FTSE": "FTSE 100",
    "^GDAXI": "DAX",
    "^FCHI": "CAC 40",
    "^N225": "Nikkei 225",
    "^HSI": "Hang Seng",
    "GC=F": "Gold",
    "BTC-USD": "Bitcoin"
}

st.set_page_config(
    page_title="Price Forecast",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Price Forecast")
st.markdown("XGBoost model forecast based on technical indicators (returns, moving averages, RSI, Bollinger Bands, volatility).")

st.divider()

# Controls
col_ticker, col_days, col_empty = st.columns([1, 1, 2])

with col_ticker:
    ticker = st.selectbox(
        "Select Ticker",
        options=list(TICKERS.keys()),
        format_func=lambda x: TICKERS.get(x, x)
    )

with col_days:
    forecast_days = st.slider(
        "Forecast horizon (business days)",
        min_value=5,
        max_value=180,
        value=30,
        step=5
    )

st.divider()

if st.button("Generate Forecast", type="primary", use_container_width=True):
    
    with st.spinner("Running XGBoost model..."):
        response = requests.get(
            f"{API_URL}/forecast/{ticker}",
            params={"days": forecast_days}
        )

        if response.status_code == 200:
            data = response.json()
            forecast = data["forecast"]
            last_price = data["last_known_price"]
            final_price = data["forecasted_price"]
            change = final_price - last_price
            change_pct = (change / last_price) * 100

            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    label="Last known price",
                    value=f"${last_price:.2f}"
                )
            with col2:
                st.metric(
                    label=f"Forecast in {forecast_days} days",
                    value=f"${final_price:,.2f}",
                    delta=f"{change_pct:+.2f}%",
                    delta_color="normal" if change >= 0 else "inverse"
                )
            with col3:
                st.metric(
                    label="Absolute change",
                    value=f"${abs(change):,.2f}",
                    delta="gain" if change >= 0 else "loss",
                    delta_color="normal" if change >= 0 else "inverse"
                )

            st.divider()

            # Forecast chart
            st.subheader("Forecasted Price")
    
            dates = [row["date"] for row in forecast]
            prices = [row["predicted_price"] for row in forecast]
            color = "#00C805" if final_price >= last_price else "#FF4B4B"
    
            fig = go.Figure()
    
            fig.add_trace(go.Scatter(
                x=dates,
                y=prices,
                mode="lines",
                name="Forecast",
                line=dict(color=color, width=2),
                fill="tozeroy",
                fillcolor=f"rgba({'0,200,5' if final_price >= last_price else '255,75,75'}, 0.05)"
            ))
    
            # Reference line at last known price
            fig.add_hline(
                y=last_price,
                line_dash="dash",
                line_color="#888888",
                annotation_text=f"Last price: ${last_price:,.2f}",
                annotation_position="bottom right"
            )
    
            y_values = prices + [last_price]
            y_min = min(y_values) * 0.98
            y_max = max(y_values) * 1.02
    
            fig.update_layout(
                height=450,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    showgrid=False,
                    color="#888",
                    title="Date"
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.1)",
                    color="#888",
                    tickprefix="$",
                    range=[y_min, y_max]
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
    
            # Returns chart
            st.subheader("Predicted Daily Returns")
    
            returns = [row["predicted_return"] * 100 for row in forecast]
            bar_colors = ["#00C805" if r >= 0 else "#FF4B4B" for r in returns]
    
            fig2 = go.Figure()
    
            fig2.add_trace(go.Bar(
                x=dates,
                y=returns,
                marker_color=bar_colors,
                name="Daily return (%)"
            ))
    
            fig2.update_layout(
                height=250,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, color="#888"),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.1)",
                    color="#888",
                    ticksuffix="%"
                ),
                hovermode="x unified",
                margin=dict(l=0, r=0, t=10, b=0),
                showlegend=False
            )
    
            st.plotly_chart(fig2, use_container_width=True)
    
            st.divider()
    
            # Backtest section
            st.subheader("Model Backtest")
            st.markdown("How the model performed on historical data it has never seen during training.")

            with st.spinner("Loading backtest data..."):
                bt_response = requests.get(f"{API_URL}/forecast/{ticker}/backtest")
            
            if bt_response.status_code == 200:
                bt_data = bt_response.json()
                bt = bt_data["backtest"]

                bt_dates = [row["date"] for row in bt]
                bt_actual = [row["actual_price"] for row in bt]
                bt_predicted = [row["predicted_price"] for row in bt]

                fig3 = go.Figure()

                fig3.add_trace(go.Scatter(
                x=bt_dates,
                y=bt_actual,
                mode="lines",
                name="Actual price",
                line=dict(color="#00C805", width=1.5)
                ))
 
                fig3.add_trace(go.Scatter(
                    x=bt_dates,
                    y=bt_predicted,
                    mode="lines",
                    name="Predicted price",
                    line=dict(color="#888888", width=1.5, dash="dash")
                ))
    
                fig3.update_layout(
                    height=350,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False, color="#888"),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor="rgba(255,255,255,0.1)",
                        color="#888",
                        tickprefix="$"
                    ),
                    hovermode="x unified",
                    margin=dict(l=0, r=0, t=10, b=0),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
    
                st.plotly_chart(fig3, use_container_width=True)

                # Cumulative backtest
                st.subheader("Backtest - Cumulative Forecast")
                st.markdown("How the model would have performed forecasting from the first day of the test set, accumulating errors like the real forecast.")

                bt_cumulative = [row["predicted_price_cumulative"] for row in bt]

                fig4 = go.Figure()

                fig4.add_trace(go.Scatter(
                    x=bt_dates,
                    y=bt_actual,
                    mode="lines",
                    name="Actual price",
                    line=dict(color="#00C805", width=1.5)
                ))

                fig4.add_trace(go.Scatter(
                    x=bt_dates,
                    y=bt_cumulative,
                    mode="lines",
                    name="Predicted price (cumulative)",
                    line=dict(color="#FFA500", width=1.5, dash="dot")
                ))

                fig4.update_layout(
                    height=350,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False, color="#888"),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor="rgba(255,255,255,0.1)",
                        color="#888",
                        tickprefix="$"
                    ),
                    hovermode="x unified",
                    margin=dict(l=0, r=0, t=10, b=0),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )

                st.plotly_chart(fig4, use_container_width=True)

            else:
                st.warning("No backtest data available for this ticker. Train the model first.")
 
        else:
            st.error("Failed to generate forecast.")
            st.code(response.text)
