# portfolio-backtester

A command-line script I made to help me with making decisions with regards to choosing stocks in the stock market.

It's not very user friendly (yet)...

In short, given a portfolio, it'll tell you how that portfolio would've done in the past.
Given a portfolio and portfolio settings (stocks, desired ratios, rebalance frequency, initial amount, contribution amounts and contribution frequency, withdrawal amounts and withdrawal frequencies), simulates the passage of time and collects data on the portfolio for each day within a given time period. Displays the different sets of information on different graphs.
- Lets you download the latest stock data for a given stock from yahoo finance.
- Extrapolates data from before the inception of an ETF that follow an index (you don't need to specify leverage factor or management fees; it'll factor that in by default from current data)
