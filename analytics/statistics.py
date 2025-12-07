import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, coint
from typing import Tuple, Dict

def check_cointegration(series_x: pd.Series, series_y: pd.Series) -> Tuple[bool, float, float]:
    """
    Perform the Engle-Granger two-step cointegration test.
    
    Returns:
        is_coint (bool): True if p-value < 0.05
        p_value (float): The p-value from the cointegration test
        hedge_ratio (float): The slope of the regression (beta)
    """
    # Align data
    x = series_x.values
    y = series_y.values
    
    # 1. Calculate Hedge Ratio (Beta) via OLS
    # Y = alpha + beta * X
    x_const = sm.add_constant(x)
    model = sm.OLS(y, x_const)
    results = model.fit()
    hedge_ratio = results.params[1]
    
    # 2. Check stationarity of residuals
    # statsmodels.tsa.stattools.coint does this in one go, but returns p-value of unit root test on residuals.
    # We use 'coint' for the test, but beta comes from OLS.
    score, p_value, _ = coint(x, y)
    
    is_coint = p_value < 0.05
    
    return is_coint, p_value, hedge_ratio

def calculate_zscore(series: pd.Series, window: int = 30) -> pd.Series:
    """
    Calculate rolling Z-Score of a series.
    Z = (Value - Mean) / StdDev
    """
    r = series.rolling(window=window)
    m = r.mean()
    s = r.std()
    z = (series - m) / s
    return z

def calculate_spread(series_y: pd.Series, series_x: pd.Series, hedge_ratio: float) -> pd.Series:
    """
    Calculate the spread: Y - beta * X
    """
    return series_y - hedge_ratio * series_x

def calculate_half_life(spread: pd.Series) -> float:
    """
    Calculate the half-life of mean reversion using Ornstein-Uhlenbeck process.
    dX_t = theta * (mu - X_t) * dt + sigma * dW_t
    
    Discrete version: X_t - X_{t-1} = alpha + beta * X_{t-1} + epsilon
    theta = -ln(1 + beta)
    half_life = -ln(2) / ln(1 + beta)
    """
    spread_lag = spread.shift(1)
    spread_ret = spread - spread_lag
    spread_lag = spread_lag.dropna()
    spread_ret = spread_ret.dropna()
    
    spread_lag_const = sm.add_constant(spread_lag)
    results = sm.OLS(spread_ret, spread_lag_const).fit()
    beta = results.params.iloc[1]
    
    if beta >= 0:
        return np.inf # Not mean reverting
        
    half_life = -np.log(2) / np.log(1 + beta) 
    # Note: Traditional formula is -ln(2)/theta where theta = -ln(1+beta) roughly approx -beta for small beta.
    # Detailed derivation often leads to half_life = -log(2) / lambda. 
    # Using simple lambda = beta for discrete approximation:
    return half_life
