# portfolio-backtester

A command-line script I made to help me with making decisions with regards to choosing stocks in the stock market.

In short, it's a portfolio backtester; i.e. given a portfolio, it'll tell you how that portfolio would've done in the past.

Main features:
- download stock data
- calculate indicators: sma, ema, macd
- generate new data for one stock based on existing data of other stock (intended for observing ETFs based on an index prior to an ETF's inception, e.g. UPRO is based on S&P, but UPRO didn't exist before 2009, so you can use the S&P data to generate UPRO to see its predicted behaviour before 2009)
- create basic portfolios of assets, specify rebalancing, withdrawals and simulate its past performance on a per-day basis
- display data on graphs

# Sample commands

Requires python 3.5, matplotlib, argparse, urllib

Commands are a temporary way to use the program until an interface is created

```
python3.5 Downloader.py --download AAPL AMD
python3.5 folio.py --portfolio 10000 0 m q 1995-01-01 2017-08-01 AAPL 0.5 long AMD 0.5 long
```

This will download all AAPL and AMD stock data, then create a starting portfolio of $10,000 ('10000') and invest 50% of your portfolio into AAPL ('AAPL 0.5 long') and another 50% into AMD ('AMD 0.5 long'). As the days go on in the simulation, $0 will be contributed monthly ('0 m'), and the 50%/50% ratios will be rebalanced quarterly ('q')

Dates are needed as placeholders in the argument list, but don't do anything. Same goes for 'long' keywords after the stock ticker(s). I don't plan to use the command line indefinitely and it's only there to test the functionality up until an interface is made, so making the command line "pretty" is very low priority at the moment.


# Current work in progress

Short-term (v3.0, trades based on indicators):

o create shell for Brain class, a class dedicated to making decisions based on strategies  
o hardcode a basic strategy into brain (assesses market daily, provides ratios to Trader)  
o probably need to refactor Trader by moving rebalancing into Brain  
o program Brain to handle strategies based on different indicators and periods  
o implement a way to read strategies from file in DataManager


Long-term:

o interface (e.g. web)  
o dynamic portfolio ratios depending on conditions  
o benchmarks  
o reimplement withdrawals   

# Version features/change

Current version: 2.4  
WIP: 3.0

Version 1

Goals: get data, store data, project data, show data

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

Goals: simulate a basic portfolio, create framework-esque platform

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

v2.4, validation, cleanup, and fixes
- separate download logic into own Downloader class
- implement downloading from google, since yahoo stopped their free/easy to use service
- separated all classes into own files and put all util classes/functions into own file
- implement Trader class for trading logic
- implement DataManager class for managing data on disk
- implement Monitor class for statistics and record keeping during simulations
- implement Calculator class for stand-alone calculations outside simulations
- rewrote all files to follow PEP-8 and Google docstrings coding style


Version 3

Goals: more intricate user programmed strategies

v3.0, basic indicator related strategies
