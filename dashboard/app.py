import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Quant Strategies Dashboard", layout="wide")

st.title("Advanced Quant Stats & Signals")

# Paths (adjust as needed if running from root or dashboard dir)
# Assuming running from root: streamlit run dashboard/app.py
RESULTS_PATH = "backtest_results.csv"
TRADES_PATH = "detailed_trades.csv"

# Load Data
if os.path.exists(RESULTS_PATH):
    df_results = pd.read_csv(RESULTS_PATH, index_col=0)
    
    st.header("Strategy Performance (Backtest)")
    
    col1, col2, col3 = st.columns(3)
    
    # KPIs
    best_pair = df_results.iloc[0]
    
    with col1:
        st.metric("Top Pair", best_pair['Pair'])
    with col2:
        st.metric("Top Sharpe", f"{best_pair['Sharpe']:.2f}")
    with col3:
        st.metric("Top Return", f"{best_pair['return']:.2%}")
        
    st.subheader("Leaderboard")
    st.dataframe(df_results.style.format({
        'Sharpe': '{:.2f}',
        'return': '{:.2%}',
        'HalfLife': '{:.1f}',
        'P-Value': '{:.4f}'
    }))
    
    # Visualization
    st.subheader("Sharpe vs. Returns Distribution")
    fig = px.scatter(df_results, x="HalfLife", y="Sharpe", size="return", color="Pair", hover_data=['return'])
    st.plotly_chart(fig)
    
else:
    st.warning(f"No results found at {RESULTS_PATH}. Run main.py first.")

# Detailed Trades
if os.path.exists(TRADES_PATH):
    st.header("Trade Analysis")
    df_trades = pd.read_csv(TRADES_PATH, index_col=0)
    
    # Filters
    pairs = df_trades['Pair'].unique()
    selected_pair = st.selectbox("Select Pair to Analyze", pairs)
    
    subset = df_trades[df_trades['Pair'] == selected_pair]
    
    st.dataframe(subset)
    
    # PnL Chart (Cumulative)
    # We need to sort by Exit Date for cumulative pnl
    if not subset.empty:
        subset['Exit'] = pd.to_datetime(subset['Exit'])
        subset = subset.sort_values('Exit')
        subset['CumPnL'] = subset['PnL'].cumsum()
        
        fig2 = px.line(subset, x="Exit", y="CumPnL", title=f"Cumulative PnL: {selected_pair}", markers=True)
        st.plotly_chart(fig2)
        
        # Win Rate
        wins = subset[subset['PnL'] > 0]
        win_rate = len(wins) / len(subset)
        st.metric("Win Rate", f"{win_rate:.2%}")
else:
    st.info("No detailed trades found yet.")
