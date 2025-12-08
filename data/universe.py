import pandas as pd
import ssl

def get_sp500_tickers() -> list:
    """
    Scrapes the S&P 500 list from Wikipedia.
    Returns a list of tickers.
    """
    try:
        # Wikipedia table
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        
        # SSL context fix for some environments
        ssl._create_default_https_context = ssl._create_unverified_context
        
        tables = pd.read_html(url)
        df = tables[0]
        
        tickers = df['Symbol'].tolist()
        
        # Clean tickers (e.g. BRK.B -> BRK-B) mostly for Yahoo, but Alpaca usually accepts whatever or needs specific.
        # Wikipedia: BRK.B
        # Alpaca: BRK.B or BRK/B? 
        # Actually standard for web is dot, but file systems/some providers prefer dash.
        # Let's keep as is, but handle map if needed.
        # Alpaca usually takes BRK.B
        
        return tickers
    except Exception as e:
        print(f"Failed to scrape S&P 500: {e}")
        # Fallback to hardcoded list if scraping fails
        # Expanded to ~100 major S&P 500 tickers across sectors
        return [
            "AAPL", "MSFT", "GOOG", "AMZN", "NVDA", "TSLA", "META", "BRK.B", "UNH", "JNJ", 
            "XOM", "JPM", "V", "PG", "LLY", "MA", "HD", "CVX", "MRK", "ABBV", 
            "PEP", "KO", "ORCL", "BAC", "COST", "MCD", "CSCO", "CRM", "ACN", "ADBE",
            "LIN", "TMO", "AMD", "NFLX", "WMT", "DHR", "DIS", "TXN", "WFC", "PM", 
            "CAT", "INTU", "COP", "QCOM", "IBM", "BA", "GE", "AMGN", "HON", "UNP",
            "LOW", "SPGI", "RTX", "INTC", "GS", "EL", "PLD", "SBUX", "DE", "MS",
            "BLK", "T", "CVS", "LMT", "GILD", "AXP", "SYK", "BKNG", "MDLZ", "TJX",
            "ISRG", "ADI", "C", "MMC", "VRTX", "MDT", "ADP", "LRCX", "TMUS", "TGT",
            "MO", "GM", "F", "SLB", "EOG", "Oxy", "PFE", "BDX", "BSX", "USB"
        ]
        # Forced Update v2
