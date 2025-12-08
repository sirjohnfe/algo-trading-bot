from strategies.statarb import StatArbStrategy
from data.universe import get_sp500_tickers
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def preview():
    print("Fetching data and scanning for pairs...")
    tickers = get_sp500_tickers()[:100] # Same as main.py
    
    # 3 Years of data (Same as main.py)
    strategy = StatArbStrategy(tickers, "2021-01-01", "2024-01-01")
    pairs = strategy.find_cointegrated_pairs()
    
    print(f"\n=== LIVE PORTFOLIO ({len(pairs)} Pairs) ===")
    for p in pairs:
        print(f"• {p['y']} vs {p['x']} (P-Value: {p['p_value']:.4f})")
        
if __name__ == "__main__":
    preview()
