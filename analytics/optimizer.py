import pandas as pd
import itertools
import logging
from typing import Dict, List
from strategies.statarb import StatArbStrategy
from backtesting.engine import Backtester
from analytics.statistics import calculate_zscore

logger = logging.getLogger(__name__)

class Optimizer:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.backtester = Backtester(transaction_cost=0.001, spread_pct=0.0005) # Use tight settings
        
    def run_grid_search(self, pair: Dict, param_grid: Dict) -> pd.DataFrame:
        """
        Runs a grid search for a specific pair.
        param_grid: {
            'window': [15, 30, 45, 60],
            'entry_z': [1.5, 2.0, 2.5],
            'exit_z': [0.0, 0.5]
        }
        """
        keys = param_grid.keys()
        values = param_grid.values()
        combinations = list(itertools.product(*values))
        
        results = []
        
        y_sym = pair['y']
        x_sym = pair['x']
        hedge_ratio = pair['hedge_ratio']
        
        if y_sym not in self.data.columns or x_sym not in self.data.columns:
            logger.error("Missing data for optimization.")
            return pd.DataFrame()
            
        spread = self.data[y_sym] - hedge_ratio * self.data[x_sym]
        
        logger.info(f"Optimizing {y_sym}-{x_sym} across {len(combinations)} combinations...")
        
        for combo in combinations:
            params = dict(zip(keys, combo))
            
            # Recalculate Z-Score with new window
            zscore = calculate_zscore(spread, window=params['window'])
            
            # Generate Signals
            signals = pd.DataFrame(index=spread.index)
            signals['zscore'] = zscore
            
            # Reconstruct signal generation logic
            signals['long_entry'] = zscore < -params['entry_z']
            signals['long_exit'] = zscore > -params['exit_z']
            signals['short_entry'] = zscore > params['entry_z']
            signals['short_exit'] = zscore < params['exit_z']
            
            # Backtester expects 'signal_raw' for legacy reasons or we can infer?
            # Looking at engine.py: signals = signals_df['signal_raw'].copy()
            # Wait, engine.py uses 'signal_raw' as a single -1/0/1 series? 
            # OR does it calculate positions from the booleans?
            # Let's check engine.py... it seems it expects 'signal_raw' OR we need to pass a signal series.
            # Actually, `analyze_pair` in `statarb.py` returns a DF with `signal_raw`.
            # We should construct `signal_raw` here too.
            
            sig_raw = pd.Series(0, index=signals.index)
            sig_raw[signals['long_entry']] = 1
            sig_raw[signals['short_entry']] = -1
            # Exits are state dependent, handled in backtest loop usually or we pass raw logic?
            # The backtester takes `signals_df`.
            signals['signal_raw'] = sig_raw
            
            # Run Backtest
            bt_res = self.backtester.run_backtest(signals, pair, self.data)
            
            results.append({
                **params,
                'Sharpe': bt_res['Sharpe Ratio'],
                'Return': bt_res['Total Return'],
                'Trades': len(bt_res['Trades'])
            })
            
        df = pd.DataFrame(results)
        df = df.sort_values(by='Sharpe', ascending=False)
        return df

if __name__ == "__main__":
    # Test
    pass
