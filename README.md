# portfolio-backtester

A command-line script I made to help me with making decisions with regards to choosing stocks in the stock market.

In short, it's a portfolio backtester; i.e. given a portfolio, it'll tell you how that portfolio would've done in the past.

Main features:
- download stock data
- display data on graph
- calculate indicators: sma, ema, macd
- generate new data for one stock based on existing data of other stock (intended for observing ETFs based on an index prior to an ETF's inception, e.g. UPRO is based on S&P, but UPRO didn't exist before 2009, so you can use the S&P data to generate UPRO to see its predicted behaviour before 2009)
- create basic portfolios of assets, specify rebalancing, withdrawals and simulate its past performance on a per-day basis

# Current work in progress

o separate into different files
o create Trader class to handle trading logic (placing orders, commissions, etc.)
o compare information against known/real data to verify accuracy
o weird behaviour: withdrawals can lead to negative cash values
o bug: withdrawals can lead to negative portfolio values
o bug: occasionally generating data leads to divide by 0
o bug: occasionally generating data leads to infinite recursion

# Version features/change

Current version: 2.3
WIP: 2.4

Version 1

v1.0, basic data
- download stock data given ticker
- download stock(s) data from list of stocks in file
- read CSV file with stock data and convert to arrays
- graph stock data using pyplot

v1.1, basic indicators
- implement some indicators (sma, ema, macd) with custom date ranges
- display indicators using pyplot

v1.2, playing around with data
- calculate growth of all stocks in a file
- specify time period for analysis
- implement some utils to make analysis consistent (e.g. date math, nearest date before/after given date)

v1.3, ETF data generation
- given two tickers, create relationship between the two and extrapolate data for one based on data in other (e.g. UPRO is 3x the S&P500, read S&P before UPRO's inception to calculate what UPRO would have been had it existed before its inception)
- tweak data generation to improve accuracy
- test generation by generating existing data and comparing

v1.4, cleanup
- move repeated code into functions
- rewrite some functions to be more legible and have clearer logic flow


Version 2

v2.0, basic portfolio
- create portfolio class, which has cash, holdings, and assets
- create portfolio behaviour (buy, sell, short, cover)

v2.1, basic market
- create market class, which has a date and stocks
- create market behaviour (query stocks on date, advance date, add stocks, inject data)

v2.2, basic simulation
- create simulator class, which has portfolio, market, and start/end date(s)
- create simulator simulation behaviour

v2.3, simulation features
- add contributions and rebalancing of portfolio holdings to simulator
- add optional commission costs
- add portfolio statistics for graphing purposes (portfolio value, asset allocation, annual return, contribution vs growth)

v2.4, validation and cleanup
