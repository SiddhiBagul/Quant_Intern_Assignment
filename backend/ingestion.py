import asyncio
import json
import websockets
import logging
from datetime import datetime
import sys
import os

# Add parent directory to path to import database
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backend.database import init_db, save_trades_batch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ingestion.log"),
        logging.StreamHandler()
    ]
)

SYMBOLS = ['btcusdt', 'ethusdt']
WS_URL = f"wss://fstream.binance.com/stream?streams={'/'.join([s.lower()+'@trade' for s in SYMBOLS])}"

class BinanceIngestor:
    def __init__(self):
        self.running = False
        self.buffer = []
        self.batch_size = 50  # Write to DB every 50 trades or on timeout
        self.last_flush = datetime.now()

    async def flush_buffer(self):
        if self.buffer:
            save_trades_batch(self.buffer)
            logging.debug(f"Flushed {len(self.buffer)} trades to DB")
            self.buffer = []
            self.last_flush = datetime.now()

    async def connect(self):
        self.running = True
        init_db()
        logging.info(f"Connecting to Binance WebSocket: {WS_URL}")
        
        while self.running:
            try:
                async with websockets.connect(WS_URL) as ws:
                    logging.info("Connected to Binance")
                    
                    while self.running:
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                            data = json.loads(msg)
                            
                            if 'data' in data:
                                trade = data['data']
                                # Normalize if needed, but Binance format returns:
                                # {e:trade, E:event_time, s:symbol, p:price, q:qty, ...}
                                # We explicitly need s, p, q, T, m
                                
                                # Add symbol to the trade dict if it's missing (stream payload usually has it)
                                if 's' not in trade:
                                    trade['s'] = data['stream'].split('@')[0].upper()
                                
                                # Map 's' to 'symbol' for database compatibility
                                trade['symbol'] = trade['s']
                                    
                                self.buffer.append(trade)
                                
                                # Batch write logic
                                if len(self.buffer) >= self.batch_size or (datetime.now() - self.last_flush).total_seconds() > 1.0:
                                    await self.flush_buffer()
                                    
                        except asyncio.TimeoutError:
                            # Flush on timeout to keep data fresh if low volume
                            await self.flush_buffer()
                            continue
                        except websockets.exceptions.ConnectionClosed:
                            logging.warning("WebSocket connection closed, reconnecting...")
                            break
                            
            except Exception as e:
                logging.error(f"Connection error: {e}")
                await asyncio.sleep(5)  # Backoff before reconnect

    def start(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.connect())
        except KeyboardInterrupt:
            logging.info("Stopping ingestion...")
        finally:
            loop.run_until_complete(self.flush_buffer())

if __name__ == "__main__":
    ingestor = BinanceIngestor()
    ingestor.start()
