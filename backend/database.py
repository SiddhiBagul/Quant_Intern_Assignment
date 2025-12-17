import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'market_data.db')

def init_db():
    """Initialize the SQLite database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create trades table
    # Storing timestamp as integer (milliseconds) for faster indexing/querying
    c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            qty REAL NOT NULL,
            timestamp INTEGER NOT NULL,
            is_buyer_maker BOOLEAN
        )
    ''')
    
    # Create index on timestamp and symbol for faster retrieval
    c.execute('CREATE INDEX IF NOT EXISTS idx_trades_ts_sym ON trades (timestamp, symbol)')
    
    conn.commit()
    conn.close()

def save_trade(trade_data):
    """
    Save a single trade dictionary to the database.
    trade_data expected format:
    {
        'symbol': str,
        'p': float (price),
        'q': float (quantity),
        'T': int (timestamp ms),
        'm': bool (is_buyer_maker)
    }
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO trades (symbol, price, qty, timestamp, is_buyer_maker)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            trade_data['symbol'],
            float(trade_data['p']),
            float(trade_data['q']),
            int(trade_data['T']),
            bool(trade_data['m'])
        ))
        conn.commit()
    except Exception as e:
        print(f"Error saving trade: {e}")
    finally:
        conn.close()

def save_trades_batch(trades_list):
    """Save a list of trades in a single transaction."""
    if not trades_list:
        return
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        data = [(
            t['symbol'], 
            float(t['p']), 
            float(t['q']), 
            int(t['T']), 
            bool(t['m'])
        ) for t in trades_list]
        
        c.executemany('''
            INSERT INTO trades (symbol, price, qty, timestamp, is_buyer_maker)
            VALUES (?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
    except Exception as e:
        print(f"Error saving batch: {e}")
    finally:
        conn.close()

def get_recent_trades(symbol, limit=1000):
    """Get the most recent N trades for a symbol."""
    conn = sqlite3.connect(DB_PATH)
    query = f'''
        SELECT timestamp, price, qty 
        FROM trades 
        WHERE symbol = ? 
        ORDER BY timestamp DESC 
        LIMIT {limit}
    '''
    df = pd.read_sql_query(query, conn, params=(symbol,))
    conn.close()
    
    if not df.empty:
        # Convert ms timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.sort_values('timestamp')
    return df

def get_trades_window(symbol, window_minutes=60):
    """Get trades for the last N minutes."""
    conn = sqlite3.connect(DB_PATH)
    cutoff_ts = int((datetime.now().timestamp() - window_minutes * 60) * 1000)
    
    query = '''
        SELECT timestamp, price, qty
        FROM trades
        WHERE symbol = ? AND timestamp >= ?
        ORDER BY timestamp ASC
    '''
    df = pd.read_sql_query(query, conn, params=(symbol, cutoff_ts))
    conn.close()
    
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
    return df
