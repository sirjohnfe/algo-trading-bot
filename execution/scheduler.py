import time
import logging
import pandas as pd
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self, interval_minutes: int = 60, strategy=None, trader=None, pairs=None):
        self.interval = interval_minutes * 60
        self.strategy = strategy
        self.trader = trader
        self.pairs = pairs
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            logger.warning("Scheduler already running.")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"Scheduler started with {self.interval/60} min interval.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Scheduler stopped.")

    def _run_loop(self):
        while self.running:
            try:
                now = datetime.now()
                # Check for Market Hours (e.g. 9:30 - 16:00 EST)
                # For crypto/paper, we run 24/7 or check logic.
                # Assuming 24/7 for now.
                
                logger.info(f"Scheduler Wake Up: {now}")
                self._job()
                
                logger.info(f"Sleeping for {self.interval} seconds...")
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"Scheduler Error: {e}")
                time.sleep(60) # Retry after 1 min on error

    def _job(self):
        """
        The trading logic to run periodically.
        """
        logger.info("Running scheduled scan...")
        
        # 1. Update Data
        self.strategy.load_data() # Logic to fetch *latest* bars
        
        # 2. Check Signals
        if not self.pairs:
             logger.warning("No pairs to scan.")
             return

        for pair in self.pairs:
            try:
                # analyze_pair re-runs Z-Score on loaded data
                df = self.strategy.analyze_pair(pair)
                last_z = df['zscore'].iloc[-1]
                
                if abs(last_z) > 2.0:
                    logger.info(f"SIGNAL DETECTED: {pair['y']}-{pair['x']} Z={last_z:.2f}")
                    # Execution Logic here
                    if self.trader:
                        # Execution Logic
                        # 1. Check if we already have a position
                        # (Simplistic check: ensure we don't spam orders. 
                        # Ideally strategies check self.trader.get_positions())
                        
                        # 2. Calculate Size (Fixed $10k per leg for Paper)
                        target_exposure = 10000 
                        
                        # Get latest prices
                        price_y = self.strategy.data[pair['y']].iloc[-1]
                        price_x = self.strategy.data[pair['x']].iloc[-1]
                        
                        qty_y = int(target_exposure / price_y)
                        qty_x = int((target_exposure * pair['hedge_ratio']) / price_x)
                        
                        logger.info(f"Executing Trade: {pair['y']} vs {pair['x']}")
                        
                        if last_z < -2.0:
                            # Long Spread: Buy Y, Sell X
                            self.trader.submit_order(pair['y'], 'buy', qty_y)
                            self.trader.submit_order(pair['x'], 'sell', qty_x)
                            
                        elif last_z > 2.0:
                            # Short Spread: Sell Y, Buy X
                            self.trader.submit_order(pair['y'], 'sell', qty_y)
                            self.trader.submit_order(pair['x'], 'buy', qty_x)
            except Exception as e:
                logger.error(f"Error scanning pair {pair}: {e}")
                
        logger.info("Scan complete.")
