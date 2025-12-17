import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller

def resample_data(df, timeframe='1min'):
    """
    Resample tick data to OHLCV.
    df must have datetime index and price/qty columns.
    """
    if df.empty:
        return pd.DataFrame()
        
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    ohlc = df['price'].resample(timeframe).ohlc()
    volume = df['qty'].resample(timeframe).sum()
    
    result = pd.concat([ohlc, volume], axis=1)
    result.rename(columns={'qty': 'volume'}, inplace=True)
    
    # Fill gaps (forward fill close, zero volume) - basic handling
    result['close'] = result['close'].ffill()
    result['open'] = result['open'].fillna(result['close'])
    result['high'] = result['high'].fillna(result['close'])
    result['low'] = result['low'].fillna(result['close'])
    result['volume'] = result['volume'].fillna(0)
    
    return result

def calculate_spread(series_a, series_b, hedge_ratio=None):
    """
    Calculate spread between two price series.
    Spread = Price_A - (Hedge_Ratio * Price_B)
    If hedge_ratio is None, it is calculated via OLS.
    """
    # Align series
    df = pd.concat([series_a, series_b], axis=1).dropna()
    df.columns = ['y', 'x']
    
    if df.empty:
        return pd.Series(), None

    if hedge_ratio is None:
        hedge_ratio = calculate_hedge_ratio(df['y'], df['x'])
        
    spread = df['y'] - (hedge_ratio * df['x'])
    return spread, hedge_ratio

def calculate_hedge_ratio(y, x):
    """Calculate hedge ratio using OLS: y = beta * x + alpha."""
    try:
        model = sm.OLS(y, x)
        results = model.fit()
        return results.params.iloc[0] # Return beta
    except:
        return 1.0

def calculate_zscore(series, window=20):
    """Calculate Rolling Z-Score."""
    if series.empty:
        return pd.Series()
        
    mean = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    zscore = (series - mean) / std
    return zscore

def adf_test(series):
    """
    Perform Augmented Dickey-Fuller test for stationarity.
    Returns p-value and boolean (True if stationary p < 0.05).
    """
    if len(series) < 20: # Function requires some data
        return 1.0, False
        
    try:
        # Check if series is constant
        if series.nunique() <= 1:
            return 1.0, False
            
        result = adfuller(series.values)
        p_value = result[1]
        return p_value, p_value < 0.05
    except Exception as e:
        print(f"ADF Error: {e}")
        return 1.0, False
