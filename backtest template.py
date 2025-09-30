import yfinance as yf
import pandas as pd
import numpy as np

tickers = ["IBM","GE","GM","BA","T","DD","C","KO","XOM","MRK"]
start_date = "2025-08-04"
due_date = "2025-09-23"
oneside_notional = 1_000_000


weekly_data = yf.download(tickers, start=start_date, end=due_date, interval="1wk")["Close"]
weekly_return = weekly_data.pct_change()   # 保留第一周 NaN，不要 dropna
daily_data = yf.download(tickers, start=start_date, end=due_date)["Close"]
daily_return = daily_data.pct_change().dropna()
# ========= portfolio constuction=========
weekly_signal = weekly_return.shift(1).dropna()

portfolios = []
for date, r in weekly_signal.iterrows():
    signal = r - r.median()   # de median
    signals = signal.sort_values(ascending=False)
    top = signals.head(2)
    bottom = signals.tail(2)

    long = top / top.sum()
    short = bottom / bottom.sum()

    longs = (long * oneside_notional).rename("Position")
    shorts = (short * -oneside_notional).rename("Position")

    position = pd.concat([longs, shorts], axis=0).reset_index()
    position.columns = ["Ticker", "Position"]
    position["startDate"] = date
    portfolios.append(position)

weekly_portfolios = pd.concat(portfolios)

# ========= backtesting =========
daily_results = []

for i in range(len(weekly_signal.index) - 1):
    start_week = weekly_signal.index[i]
    end_week = weekly_signal.index[i + 1]

    weights = weekly_portfolios[weekly_portfolios["startDate"] == start_week].set_index("Ticker")["Position"]

    # daily return）
    this_week_returns = daily_return.loc[start_week:end_week].iloc[:-1]

    for date, r in this_week_returns.iterrows():
        pnl = (weights.reindex(r.index).fillna(0) * r).sum()
        ret = pnl / (2 * oneside_notional)  # total notional 2m
        daily_results.append({
            "Date": date,
            "PnL": pnl,
            "Return": ret
        })

daily_df = pd.DataFrame(daily_results).set_index("Date")
print("Daily results:\n", daily_df)
# ================= SPY  =================
spy = yf.download("SPY", start=start_date, end=due_date)["Close"]
spy_return = spy.pct_change().dropna()
spy_return.name = "SPY"

combined = pd.concat([daily_df["Return"], spy_return], axis=1, join="inner").dropna()
excess = combined["Return"] - combined["SPY"]

IR = excess.mean() / excess.std(ddof=1) * np.sqrt(252)
print("Information Ratio vs SPY:", IR)
correlation = combined["Return"].corr(combined["SPY"])
print("Correlation coefficient:", correlation)

# ================= VaR & ETL =================
daily_return_strat = daily_df["Return"].dropna()
daily_pnl = daily_df["PnL"].dropna()
sorted_returns = np.sort(daily_return_strat.values)

VaR75 = np.percentile(sorted_returns, 25)
ETL75 = sorted_returns[sorted_returns <= VaR75].mean()
print("75% VaR:", VaR75)
print("75% ETL:", ETL75)

# ================= max drawdown =================
cum_pnl = daily_pnl.cumsum()
running_max = cum_pnl.cummax()
drawdown = cum_pnl - running_max
max_drawdown = drawdown.min()
print("Max Drawdown:", max_drawdown)