from datetime import datetime as dt

from utils import date_str, date_obj

from DataManager import DataManager


class Market(object):

    """A Market containing stocks and a date.

    Can be queried for stock prices at the current date of this Market

    Attributes:
        stocks: A map of stock tickers to price LUTs
        new_period: A map of flags for market periods
        dates: An array of dates for the market
        date: A tuple containing (curr date index in dates, curr date)

    Todo:
    """

    def __init__(self, tickers=None, dates=None):
        """Intialize a Market with a set of dates and stock tickers
        with corresponding price LUTs.

        Args:
            tickers: An array of tickers for which to build price LUTs
            dates: An array of dates
        """
        self._db = DataManager()
        self.new_period = {'m': False, 'q': False, 'y': False}
        self.stocks = {}
        if tickers != None:
            self.add_stocks(tickers)
        self.dates = []
        self.date = (-1, None)
        if dates != None:
            self.dates = dates
            self.date = (0, self.dates[0])

    def add_stocks(self, tickers):
        """Creates price LUTs and adds them to the Market.

        Args:
            tickers: An array of tickers for which to create LUTs
        """
        for ticker in tickers:
            self.stocks[ticker.upper()] \
                = self._db.build_price_lut(ticker.upper())

    def inject_stock_data(self, ticker, dates, prices):
        """Injects provided stock data into this market.

        Generally used for generated data, but can be used in any case
        to bypass the default price LUT creation method.

        Args:
            ticker: A ticker for which to inject data
            dates: An array of dates corresponding to the prices
            prices: An array of prices corresponding to the dates
        """
        price_lut = {}
        for i in range(0, len(dates)):
            price_lut[dates[i]] = prices[i]
        self.stocks[ticker.upper()] = price_lut

    def current_date(self):
        """Returns the current date of this Market.

        Returns:
            A string representing the current date in this Market
        """
        return self.date[1]

    def query_stock(self, ticker):
        """Query a stock at the current date.

        Args:
            ticker: A ticker to query

        Returns:
            A float representing the price of the stock
        """
        try:
            return float(self.stocks[ticker.upper()][self.date[1]])
        except KeyError:
            print("NEEDS FIX: no data for " + ticker + " at " + self.date[1])
            return 0

    def set_date(self, date):
        """Sets this Market to a given date.

        Args:
            date: A date to which to set this Market
        """
        if date < self.dates[0]:
            self.date = (0, self.dates[0])
            return 0
        if date > self.dates[-1]:
            self.date = (len(self.dates) - 1, self.dates[-1])
            return 0
        try:
            self.date = (self.dates.index(date), date)
            return 0
        except ValueError:
            print("NEEDS FIX: date does not exist")
            return 1

    def set_default_dates(self):
        """Sets a default range for this Market's dates.

        Based on existing stocks in this Market, decides an appropriate
        range in which all stocks have prices.
        """
        date_range = (date_str(dt.fromordinal(1)),
                      date_str(dt.fromordinal(999999)))
        for price_lut in self.stocks.values():
            dates = sorted(price_lut.keys())
            #print(dates)
            #print('------------------------')
            date_range = (max(date_range[0], dates[0]), min(
                date_range[1], dates[-1]))
            date_idxs = (dates.index(
                date_range[0]), dates.index(date_range[1]))
            self.dates = dates[date_idxs[0]:date_idxs[1] + 1]
        self.date = (0, self.dates[0])
        #print(date_range)

    def advance_day(self):
        """Advances this Market's date by one day."""
        self.date = (self.date[0] + 1, self.dates[self.date[0] + 1])
        self._raise_period_flags()

    def _raise_period_flags(self):
        """Internal function to handle setting flags at new periods."""
        last_date = date_obj(self.dates[self.date[0] - 1])
        curr_date = date_obj(self.date[1])
        self.new_period = {'m': False, 'q': False, 'y': False}
        if last_date.year < curr_date.year:
            self.new_period = {'m': True, 'q': True, 'y': True}
            return 0
        if last_date.month != curr_date.month:
            self.new_period['m'] = True
            if (curr_date.month - 1) % 3 == 0:
                self.new_period['q'] = True
            return 0
        return 0
