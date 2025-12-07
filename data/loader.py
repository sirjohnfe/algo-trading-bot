import yfinance as yf
import pandas as pd
from typing import List, Optional, Union
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

load_dotenv()

class DataManager:
    def __init__(self, provider: str = "alpaca"):
        self.provider = provider
        if self.provider == "alpaca":
            api_key = os.getenv("APCA_API_KEY_ID")
            secret_key = os.getenv("APCA_API_SECRET_KEY")
            if not api_key or not secret_key:
                raise ValueError("Alpaca credentials missing for DataManager.")
            self.client = StockHistoricalDataClient(api_key, secret_key)

    def fetch_data(self, tickers: List[str], start_date: str, end_date: Optional[str] = None, interval: str = "1d") -> pd.DataFrame:
        """
        Fetches historical data for a list of tickers using Alpaca.
        Returns a DataFrame with Close prices, columns = tickers.
        """
        logger.info(f"Fetching data for {len(tickers)} tickers from {start_date} via Alpaca...")
        
        try:
            if self.provider == "alpaca":
                # specific handling for Alpaca
                req = StockBarsRequest(
                    symbol_or_symbols=tickers,
                    timeframe=TimeFrame.Day,
                    start=pd.Timestamp(start_date),
                    end=pd.Timestamp(end_date) if end_date else None,
                    adjustment='all' # corporate action adjustments
                )
                
                bars = self.client.get_stock_bars(req)
                
                # Convert to DataFrame
                df = bars.df
                
                # The dataframe has a MultiIndex (symbol, timestamp).
                # We want a Pivot Table: Index=timestamp, Columns=symbol, Values=close
                
                # Check columns
                # Typically: open, high, low, close, volume, trade_count, vwap
                
                pivot_df = df.reset_index().pivot(index='timestamp', columns='symbol', values='close')
                
                # Cleanup
                pivot_df.dropna(axis=1, how='all', inplace=True)
                pivot_df.fillna(method='ffill', inplace=True)
                pivot_df.dropna(inplace=True)
                
                logger.info(f"Successfully loaded data. Shape: {pivot_df.shape}")
                return pivot_df
                
            elif self.provider == "yfinance":
                # Legacy support removed or kept as fallback? 
                # User specifically asked to replace it.
                logger.warning("yfinance provider is deprecated/unreliable. Please switch to alpaca.")
                return pd.DataFrame()
            else:
                raise NotImplementedError(f"Provider {self.provider} not implemented.")
                
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return pd.DataFrame()

if __name__ == "__main__":
    # Smoke test
    logging.basicConfig(level=logging.INFO)
    dm = DataManager(provider="alpaca")
    data = dm.fetch_data(["AAPL", "MSFT"], "2023-01-01")
    print(data.head())
