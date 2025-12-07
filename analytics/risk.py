import pandas as pd
import numpy as np

def calculate_volatility(series: pd.Series, window: int = 60) -> pd.Series:
    """
    Calculate annualized volatility.
    """
    returns = series.pct_change()
    rol_vol = returns.rolling(window=window).std() * np.sqrt(252)
    return rol_vol

def calculate_target_position_size(volatility: float, target_vol: float = 0.15, max_leverage: float = 2.0) -> float:
    """
    Calculate position size based on Volatility Targeting.
    Weight = Target Vol / Current Vol
    
    If Current Vol is low (e.g. 5%), we leverage up (Weight = 15%/5% = 3.0).
    If Current Vol is high (e.g. 60%), we reduce size (Weight = 15%/60% = 0.25).
    """
    if volatility <= 0 or pd.isna(volatility):
        return 0.0
        
    weight = target_vol / volatility
    
    # Cap leverage to safety limits
    return min(weight, max_leverage)

def calculate_kelly_fraction(win_rate: float, win_loss_ratio: float) -> float:
    """
    Calculate Kelly Criterion fraction.
    f* = p - (q / b)
    p = win_rate
    q = 1 - p
    b = win_loss_ratio (Avg Win / Avg Loss)
    
    Returns standard Kelly fraction. 
    (Practitioners usually use 0.5 * Kelly to be safe).
    """
    if win_loss_ratio <= 0:
        return 0.0
        
    p = win_rate
    q = 1 - p
    b = win_loss_ratio
    
    kelly = p - (q / b)
    return max(kelly, 0.0) # No negative sizing (shorting is handled by sign)
