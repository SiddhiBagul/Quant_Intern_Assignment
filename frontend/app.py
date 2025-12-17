import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backend.database import get_recent_trades, get_trades_window
from backend.analytics import resample_data, calculate_spread, calculate_zscore, adf_test

st.set_page_config(
    page_title="Gemscap Analyzer",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark mode aesthetics
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .metric-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #464b5c;
    }
</style>
""", unsafe_allow_html=True)

st.title("💎 Gemscap Quant Analytics")

# Sidebar Controls
with st.sidebar:
    st.header("Configuration")
    
    # Refresh rate
    refresh_rate = st.slider("Refresh Rate (s)", 1, 60, 2)
    
    st.subheader("Data Parameters")
    # Timeframe selection
    timeframe = st.selectbox("Resample Timeframe", ["1s", "1min", "5min", "15min"], index=1)
    
    # Window for analytics
    window_minutes = st.number_input("Lookback Window (Minutes)", min_value=1, value=60)
    
    st.subheader("Analytics Parameters")
    # Z-Score Window
    z_window = st.number_input("Z-Score Window", min_value=5, value=20)
    
    # Alert Thresholds
    z_threshold = st.slider("Z-Score Alert Threshold", 1.0, 4.0, 2.0)
    
    st.info("Ensure the ingestion backend is running!")

# Main Loop placeholder for auto-refresh
placeholder = st.empty()

while True:
    with placeholder.container():
        # Fetch Data
        run_id = time.time()
        try:
            df_btc = get_recent_trades('BTCUSDT', limit=5000)
            df_eth = get_recent_trades('ETHUSDT', limit=5000)
            
            if df_btc.empty or df_eth.empty:
                st.warning("Waiting for data... (Is the ingestion script running?)")
                time.sleep(refresh_rate)
                continue
                
            # Filter by window (though get_recent_trades limits by count, get_trades_window is better for time)
            # For performance in this demo loop, we used get_recent_trades, but let's filter just in case
            # or better yet, use Resampling directly on the frames
            
            # Resample
            # Convert timeframe string for pandas: 1min -> 1T, 5min -> 5T
            tf_map = {"1s": "1S", "1min": "1min", "5min": "5min", "15min": "15min"}
            tf = tf_map.get(timeframe, "1min")
            
            ohlc_btc = resample_data(df_btc.set_index('timestamp'), tf)
            ohlc_eth = resample_data(df_eth.set_index('timestamp'), tf)
            
            if ohlc_btc.empty or ohlc_eth.empty:
                st.warning("Not enough data for resampling.")
                time.sleep(refresh_rate)
                continue

            # Analytics
            # Ensure alignment
            common_idx = ohlc_btc.index.intersection(ohlc_eth.index)
            btc_aligned = ohlc_btc.loc[common_idx]['close']
            eth_aligned = ohlc_eth.loc[common_idx]['close']
            
            spread, hedge_ratio = calculate_spread(btc_aligned, eth_aligned)
            zscore = calculate_zscore(spread, window=int(z_window))
            
            # ADF Test on recent spread
            adf_p, is_stationary = adf_test(spread.dropna())
            
            # --- DASHBOARD LAYOUT ---
            
            # Top Metrics Row
            col1, col2, col3, col4 = st.columns(4)
            current_z = zscore.iloc[-1] if not zscore.empty else 0
            current_spread = spread.iloc[-1] if not spread.empty else 0
            
            with col1:
                st.metric("BTC Price", f"${btc_aligned.iloc[-1]:,.2f}", 
                         delta=f"{btc_aligned.iloc[-1] - btc_aligned.iloc[-2]:.2f}" if len(btc_aligned)>1 else None)
            with col2:
                st.metric("ETH Price", f"${eth_aligned.iloc[-1]:,.2f}",
                         delta=f"{eth_aligned.iloc[-1] - eth_aligned.iloc[-2]:.2f}" if len(eth_aligned)>1 else None)
            with col3:
                # Custom Alert logic
                is_alert = abs(current_z) > z_threshold
                label = "✅ Normal"
                if is_alert:
                    label = "🚨 ALERT: Z-Score Breach"
                
                st.metric("Z-Score", f"{current_z:.2f}", delta=label, delta_color="inverse" if is_alert else "normal")
            with col4:
                st.metric("Hedge Ratio", f"{hedge_ratio:.4f}")
            
            # Charts
            tab1, tab2, tab3 = st.tabs(["Price Action", "Spread & Z-Score", "Data & Stats"])
            
            with tab1:
                # Dual Axis Price Chart
                fig_price = make_subplots(specs=[[{"secondary_y": True}]])
                fig_price.add_trace(go.Scatter(x=btc_aligned.index, y=btc_aligned, name="BTC", line=dict(color='#F7931A')), secondary_y=False)
                fig_price.add_trace(go.Scatter(x=eth_aligned.index, y=eth_aligned, name="ETH", line=dict(color='#627EEA')), secondary_y=True)
                fig_price.update_layout(title="BTC vs ETH Prices", height=400, template="plotly_dark")
                st.plotly_chart(fig_price, use_container_width=True, key=f"price_{run_id}")
            
            with tab2:
                # Spread and Z-Score
                col_z1, col_z2 = st.columns(2)
                
                # Z-Score Plot
                fig_z = go.Figure()
                fig_z.add_trace(go.Scatter(x=zscore.index, y=zscore, name="Z-Score", line=dict(color='#00ff00' if not is_alert else '#ff0000')))
                # Add threshold lines
                fig_z.add_hline(y=z_threshold, line_dash="dash", line_color="red")
                fig_z.add_hline(y=-z_threshold, line_dash="dash", line_color="red")
                fig_z.update_layout(title=f"Rolling Z-Score (Window={z_window})", height=350, template="plotly_dark")
                
                # Spread Plot
                fig_spread = go.Figure()
                fig_spread.add_trace(go.Scatter(x=spread.index, y=spread, name="Spread", line=dict(color='#3498db')))
                fig_spread.update_layout(title="Spread (BTC - beta*ETH)", height=350, template="plotly_dark")
                
                col_z1.plotly_chart(fig_z, use_container_width=True, key=f"z_{run_id}")
                col_z2.plotly_chart(fig_spread, use_container_width=True, key=f"spread_{run_id}")
                
            with tab3:
                st.markdown("### Statistical Summary")
                stats_df = pd.DataFrame({
                    "Metric": ["ADF P-Value", "Stationary?", "Mean Spread", "Std Spread"],
                    "Value": [f"{adf_p:.4f}", str(is_stationary), f"{spread.mean():.4f}", f"{spread.std():.4f}"]
                })
                st.table(stats_df)
                
                st.markdown("### Recent Data (Resampled)")
                st.dataframe(ohlc_btc.tail(10))
                
                # Download
                csv = ohlc_btc.to_csv().encode('utf-8')
                st.download_button(
                    label="Download BTC OHLC CSV",
                    data=csv,
                    file_name='btc_ohlc.csv',
                    mime='text/csv',
                    key=f"dl_{run_id}"
                )

        except Exception as e:
            st.error(f"An error occurred: {e}")
            
        # Re-run logic handled by the while True + sleep loop inside placeholder
        # However, Streamlit native way is st.rerun() or sleep and loop.
        # Since we are inside a placeholder container loop, we need to respect the sleep.
        time.sleep(refresh_rate)
