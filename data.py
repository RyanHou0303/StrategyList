import yfinance as yf
import pandas as pd
tickers = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","AVGO","UNH","XOM",
    "LLY","JPM","JNJ","V","PG","HD","MA","COST","ABBV","MRK",
    "PEP","KO","NFLX","WMT","BAC","PFE","CVX","CRM","LIN","ADBE",
    "TMO","CSCO","MCD","ABT","ACN","WFC","DHR","DIS","TXN","INTC",
    "VZ","AMD","IBM","QCOM","HON","UNP","PM","GE","CAT","MS",
    "GS","BLK","RTX","NOW","AMAT","ADP","BKNG","LMT","LOW","AXP"
]
rows=[]
for tk in tickers:
    tkr = yf.Ticker(tk)
    hist = tkr.history(period="1y",interval="1d")
    shares_out = tkr.info.get("sharesOutstanding", None)
    if hist.empty:
        continue

    for _,r in hist.iterrows():
        rows.append({
            "date":_,
            "ticker":tk,
            "close":float(r["Close"]),
            "volume":float(r["Volume"]),
            "shares_outstanding": shares_out
        })
df = pd.DataFrame(rows)
print(df.head())
df["market_cap"]=df["close"]*df["shares_outstanding"]
df["is_common_share"]=True
df["is_adr"] = False
df = df.sort_values(["ticker","date"]).reset_index(drop=True)
df["days_since_listing"]=df.groupby("ticker").cumcount()
df["date"]=pd.to_datetime(df["date"])
print(df.head())
df.to_parquet("daily_panel.parquet",index=False)


