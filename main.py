from strategies.statarb import StatArbStrategy
from backtesting.engine import Backtester
import matplotlib.pyplot as plt
import pandas as pd
import logging

# Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("Main")

from data.universe import get_sp500_tickers

def main():
    logger.info("Starting Advanced Quant System...")
    
    # 1. Define Universe
    # Use S&P 500 but limit to top 50 for initial speed/API limits check
    full_sp500 = get_sp500_tickers()
    logger.info(f"Loaded {len(full_sp500)} tickers from S&P 500.")
    
    tickers = full_sp500[:50] # Top 50 by alphabetical (approx random sector mix if wiki sort)
    # Note: Wiki is sorted by Symbol A-Z. 
    # Better: Top 50.
    
    
    start_date = "2023-01-01"
    end_date = "2024-01-01"
    
    # 2. Initialize Strategy
    strategy = StatArbStrategy(tickers, start_date, end_date)
    
    # 3. Find Pairs
    pairs = strategy.find_cointegrated_pairs()
    
    if not pairs:
        logger.warning("No cointegrated pairs found. Exiting.")
        return
        
    # 4. Mode Selection
    mode = "optimize" # Options: "backtest", "paper_trade", "scheduled", "optimize"
    
    if mode == "backtest":
        backtester = Backtester()
        results = []
        all_trades_log = []
    
        for pair in pairs:
            logger.info(f"Backtesting {pair['y']} vs {pair['x']}...")
            signals_df = strategy.analyze_pair(pair)
            
            bt_result = backtester.run_backtest(signals_df, pair, strategy.data)
            
            # Store Summary
            results.append({
                "Pair": f"{pair['y']}-{pair['x']}",
                "Sharpe": bt_result['Sharpe Ratio'],
                "return": bt_result['Total Return'],
                "HalfLife": pair['half_life'],
                "P-Value": pair['p_value'],
                "Num_Trades": len(bt_result['Trades'])
            })
            
            # Store Details
            for t in bt_result['Trades']:
                t['Pair'] = f"{pair['y']}-{pair['x']}"
                all_trades_log.append(t)
            
            logger.info(f"Result: Return={bt_result['Total Return']:.2%}, Sharpe={bt_result['Sharpe Ratio']:.2f}, Trades={len(bt_result['Trades'])}")
            
        # Summary
        results_df = pd.DataFrame(results)
        if not results_df.empty:
            results_df = results_df.sort_values(by="Sharpe", ascending=False)
            print("\n=== Backtest Summary ===")
            print(results_df.to_string())
            results_df.to_csv("backtest_results.csv")
            
            trades_df = pd.DataFrame(all_trades_log)
            if not trades_df.empty:
                trades_df = trades_df.sort_values(by=['Pair', 'Entry'])
                trades_df.to_csv("detailed_trades.csv")
                logger.info("Detailed trades saved to detailed_trades.csv")
            else:
                 logger.warning("No trades generated.")
    
    elif mode == "scheduled":
        from execution.trader import AlpacaExecutor
        from execution.scheduler import Scheduler
        
        try:
            trader = AlpacaExecutor()
            if trader.check_connection():
                logger.info("Initializing 24/7 Scheduler...")
                
                # We need to pass the filtering logic to the scheduler
                # For MVP, we will just scan the 'tickers' list we defined above.
                # In production, we might re-scan the universe daily.
                
                # Pre-scan for cointegration (This happens once on startup, or we could make it periodic)
                logger.info("Running initial Cointegration Scan...")
                pairs = strategy.find_cointegrated_pairs()
                
                if not pairs:
                    logger.error("No pairs found. Scheduler will not run.")
                    return

                # Create Scheduler
                # Run every 60 minutes
                scheduler = Scheduler(interval_minutes=60, strategy=strategy, trader=trader, pairs=pairs)
                scheduler.start()
                
                # Keep main thread alive
                try:
                    while True:
                        import time
                        time.sleep(1)
                except KeyboardInterrupt:
                    scheduler.stop()
                    logger.info("Bot stopped by user.")
                
        except Exception as e:
             logger.error(f"Scheduler failed: {e}")

    elif mode == "optimize":
        from analytics.optimizer import Optimizer
        
        if not pairs:
            logger.error("No pairs found to optimize.")
            return
            
        # Optimize Top Pair
        top_pair = pairs[0] # MSFT-AAPL usually
        
        optimizer = Optimizer(strategy.data)
        
        param_grid = {
            'window': [20, 30, 40, 60],
            'entry_z': [1.5, 2.0, 2.5, 3.0],
            'exit_z': [0.0, 0.5, 1.0]
        }
        
        results = optimizer.run_grid_search(top_pair, param_grid)
        
        print("\n=== Optimization Results (Top 10) ===")
        print(results.head(10).to_string())
        
        best = results.iloc[0]
        logger.info(f"Best Parameters: Window={best['window']}, Entry={best['entry_z']}, Exit={best['exit_z']} -> Sharpe={best['Sharpe']:.2f}")

    elif mode == "paper_trade":
        from execution.trader import AlpacaExecutor
        try:
            trader = AlpacaExecutor()
            if trader.check_connection():
                logger.info("Starting Paper Trading Cycle (Single Pass)...")
                
                # In a real loop, we would:
                # 1. Update Data (Live)
                # 2. Check Signals
                # 3. Send Orders
                
                # For this demo, we will just log the top Opportunity found in historical data
                # and print what trade we WOULD do.
                # To prevent accidental noise, we won't fire random orders unless confirmed.
                
                logger.info("Scanning for current opportunities directly from strategy...")
                # Note: Strategy currently uses historical static data. 
                # In live mode, 'end_date' should be Today.
                
                for pair in pairs:
                    # simplistic check: look at last Z-Score
                    df = strategy.analyze_pair(pair)
                    last_z = df['zscore'].iloc[-1]
                    
                    if abs(last_z) > 2.0:
                        logger.info(f"LIVE SIGNAL: {pair['y']}-{pair['x']} Z-Score: {last_z:.2f}")
                        # Example Order Logic
                        # trader.submit_order(pair['y'], 'buy', 10)
                        # trader.submit_order(pair['x'], 'sell', 10 * pair['hedge_ratio'])
                    else:
                        logger.debug(f"No signal for {pair['y']}-{pair['x']} (Z={last_z:.2f})")
                        
                logger.info("Paper Trading Scan Complete.")
                
        except Exception as e:
            logger.error(f"Paper Trading Initialization Failed: {e}")

if __name__ == "__main__":
    main()
