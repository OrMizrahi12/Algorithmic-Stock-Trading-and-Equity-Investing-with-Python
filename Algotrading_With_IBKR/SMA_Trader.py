#Please run the following code only with your Paper Trading Account!!!
#Check the Regular Trading Hours!!! (trade right before 16:30 US Eastern time)


import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
from ib_insync import *
#util.startLoop()

symbol = "MSFT"
shares = 10
sma_s = 50
sma_l = 200
today = pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))

cprice =  yf.Ticker(symbol).get_info()["regularMarketPrice"]
close = yf.download(symbol, end = today).Close.to_frame()

close.loc[today] = cprice
close = close.iloc[-sma_l:].copy()
close["sma_s"] = close.Close.rolling(sma_s).mean()
close["sma_l"] = close.Close.rolling(sma_l).mean()

close["position"] = np.where(close["sma_s"] > close["sma_l"], 1, -1 )
position = close.position.iloc[-1]

target = position * shares

print("", end='\n')
print("Target Position {}: {} Shares".format(symbol, target)) 

ib = IB()
ib.connect()

pos = ib.positions()

df = util.df(pos)
if df is not None:
    df["symbol"] = df.contract.apply(lambda x: x.symbol)
    df["conID"] = df.contract.apply(lambda x: x.conId)
else: 
    df = pd.DataFrame(columns = ["symbol", "position", "conID"])

contract = Stock(symbol, "SMART", "USD")
cds = ib.reqContractDetails(contract)
conID = cds[0].contract.conId

current_pos = df[df.conID == conID]

if len(current_pos) == 0:
    actual = 0
else: 
    actual = current_pos.position.iloc[0]

print("", end='\n')
print("Current Position {}: {} Shares".format(symbol, actual))
      
trades = target - actual
      
print("", end='\n')
print("Required Trades {}: {} Shares".format(symbol, trades))
print("", end='\n')

if trades > 0:
    side = "BUY"
    order = MarketOrder(side, abs(trades))
    trade = ib.placeOrder(contract, order)
    while not trade.isDone():
        ib.waitOnUpdate()
    if trade.orderStatus.status == "Filled":
        print("{} {} {} @ {}".format(side, trade.orderStatus.filled, symbol, trade.orderStatus.avgFillPrice))
    else:
        print("{} {} failed.".format(side, symbol))
elif trades < 0:
    side = "SELL"
    order = MarketOrder(side, abs(trades))
    trade = ib.placeOrder(contract, order)
    while not trade.isDone():
        ib.waitOnUpdate()
    if trade.orderStatus.status == "Filled":
        print("{} {} {} @ {}".format(side, trade.orderStatus.filled, symbol, trade.orderStatus.avgFillPrice))
    else:
        
        print("{} {} failed.".format(side, symbol))
else:
    print("No Trades required.")

ib.disconnect()
