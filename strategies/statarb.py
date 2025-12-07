import pandas as pd
import numpy as np
from itertools import combinations
import logging
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

from data.loader import DataManager
from analytics.statistics import check_cointegration, calculate_zscore, calculate_spread, calculate_half_life

logger = logging.getLogger(__name__)

@dataclass
class TradeSignal:
    pair: Tuple[str, str]
    signal: str # "LONG_SPREAD", "SHORT_SPREAD", "EXIT", "NO_SIGNAL"
    z_score: float
    hedge_ratio: float
    timestamp: pd.Timestamp

class StatArbStrategy:
    def __init__(self, tickers: List[str], start_date: str, end_date: Optional[str] = None):
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.dm = DataManager(provider="alpaca")
        self.data: pd.DataFrame = pd.DataFrame()
        self.cointegrated_pairs: List[Dict] = []
        
        # Parameters
        self.z_entry_threshold = 2.0
        self.z_exit_threshold = 0.5
        self.rolling_window = 30 # Days for Rolling Z-Score
        self.min_half_life = 1
        self.max_half_life = 42 # If half life is too long, it's not useful

    def load_data(self):
        self.data = self.dm.fetch_data(self.tickers, self.start_date, self.end_date)
        if self.data.empty:
            logger.error("No data loaded. Cannot proceed.")

    def find_cointegrated_pairs(self) -> List[Dict]:
        """
        Scans all combinations of tickers to find cointegrated pairs.
        This is computationally expensive if N is large. O(N^2).
        """
        if self.data.empty:
            self.load_data()
            
        n = self.data.shape[1]
        keys = self.data.columns
        pairs = []
        
        logger.info(f"Scanning {n} assets for cointegration ({n*(n-1)//2} combinations)...")
        
        for i in range(n):
            for j in range(i + 1, n):
                s1 = self.data[keys[i]]
                s2 = self.data[keys[j]]
                
                # Check cointegration
                is_coint, p_val, hedge_ratio = check_cointegration(s1, s2)
                
                if is_coint:
                    # Check half-life to ensure mean reversion is fast enough
                    spread = calculate_spread(s2, s1, hedge_ratio)
                    half_life = calculate_half_life(spread)
                    
                    if self.min_half_life <= half_life <= self.max_half_life:
                        pair_info = {
                            "y": keys[j],
                            "x": keys[i],
                            "p_value": p_val,
                            "hedge_ratio": hedge_ratio,
                            "half_life": half_life
                        }
                        pairs.append(pair_info)
                        logger.info(f"Found Pair: {keys[j]}/{keys[i]} | p={p_val:.4f} | HL={half_life:.1f}")
        
        self.cointegrated_pairs = pairs
        logger.info(f"Total cointegrated pairs found: {len(pairs)}")
        return pairs

    def generate_signals(self, pair_info: Dict) -> pd.DataFrame:
        """
        Generates historical signals for a specific pair.
        Returns a DataFrame with Spread, ZScore, and Signal columns.
        """
        y_sym = pair_info['y']
        x_sym = pair_info['x']
        beta = pair_info['hedge_ratio']
        
        y = self.data[y_sym]
        x = self.data[x_sym]
        
        spread = calculate_spread(y, x, beta)
        zscore = calculate_zscore(spread, window=self.rolling_window)
        
        df = pd.DataFrame(index=spread.index)
        df['spread'] = spread
        df['zscore'] = zscore
        df['signal'] = 0 # 0: None, 1: Long Spread, -1: Short Spread, 9: Exit
        
        # Vectorized Logic? Or Iterative for state management?
        # True trading requires state (are we currently in a position?)
        # For signal generation dataframe, we can mark "Entry" conditions.
        
        long_entry = df['zscore'] < -self.z_entry_threshold
        short_entry = df['zscore'] > self.z_entry_threshold
        
        exit_cond = abs(df['zscore']) < self.z_exit_threshold
        
        df.loc[long_entry, 'signal_raw'] = 1
        df.loc[short_entry, 'signal_raw'] = -1
        df.loc[exit_cond, 'signal_raw'] = 0
        
        return df

    def analyze_pair(self, pair_info: Dict):
        """
        Detailed analysis of a pair.
        """
        df = self.generate_signals(pair_info)
        # TODO: Add simple backtest logic here or return for backtester
        return df
