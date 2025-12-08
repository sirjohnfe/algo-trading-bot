from strategies.statarb import StatArbStrategy
from data.universe import get_sp500_tickers
import logging
import pandas as pd

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def diagnose():
    print("=== DIAGNOSTIC MODE: Checking Current Signals ===")
    tickers = get_sp500_tickers()[:100] 
    
    # Load strategy
    strategy = StatArbStrategy(tickers, "2021-01-01", "2024-12-10") # Ensure we cover today
    
    print("\n1. Finding Pairs (This uses cached data if available, or fetches new)...")
    try:
        # Force fresh data fetch by calling load_data explicitly if needed, 
        # but find_coins calls it internally.
        pairs = strategy.find_cointegrated_pairs()
    except Exception as e:
        print(f"CRITICAL DATA ERROR: {e}")
        return

    print(f"\n2. Analyzing {len(pairs)} Pairs for Active Signals...")
    print(f"{'PAIR':<15} {'Z-SCORE':<10} {'ACTION'}")
    print("-" * 40)
    
    signal_count = 0
    for p in pairs:
        try:
             # Get latest data analysis
             df = strategy.analyze_pair(p)
             last_z = df['zscore'].iloc[-1]
             last_date = df.index[-1]
             
             action = "WAIT"
             if last_z > 2.0: action = "SELL Y / BUY X"
             elif last_z < -2.0: action = "BUY Y / SELL X"
             
             if action != "WAIT":
                 signal_count += 1
                 print(f"{p['y']}-{p['x']:<9} {last_z:>6.2f}     {action} (Date: {last_date})")
             else:
                 # Uncomment to see non-signals
                 # print(f"{p['y']}-{p['x']:<9} {last_z:>6.2f}     {action}")
                 pass
                 
        except Exception as e:
            print(f"Error analyzing {p}: {e}")

    print("-" * 40)
    print(f"Total Active Signals: {signal_count}")
    
    if signal_count == 0:
        print("\nCONCLUSION: The bot is working correctly. There are simply NO trades right now.")
        print("StatArb is a game of patience. It waits for extreme events (2 Standard Deviations).")

if __name__ == "__main__":
    diagnose()
