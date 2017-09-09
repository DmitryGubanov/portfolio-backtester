from datetime import datetime as dt

from utils import date_str
from utils import date_obj

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
        self.commissions = 0
        self.stocks = {}
        self.stocks_indicators = {}
        if tickers != None:
            self.add_stocks(tickers)
        self.dates = []
        self.date = (-1, None)
        if dates != None:
            self.dates = dates
            self.date = (0, self.dates[0])

    def add_stocks(self, tickers):
        """Creates price LUTs and adds them to the Market. Also sets up
        the data structures for indicators.

        Args:
            tickers: An array of tickers for which to create LUTs
        """
        for ticker in tickers:
            self.stocks[ticker.upper()] \
                = self._db.build_price_lut(ticker.upper())
            # create empty dict to be populated later by indicators
            self.stocks_indicators[ticker.upper()] = {}

    def add_indicator(self, ticker, indicator, indicator_lut):
        """Adds the indicator data for a ticker to this Market.

        Args:
            ticker: A ticker for which to add indicator data
            indicator: A string for the indicator being added
            indicator_lut: A lookup table for the indicator data itself
        """
        self.stocks_indicators[ticker.upper()][indicator.upper()] = \
            indicator_lut

    def inject_stock_data(self, ticker, dates, prices, price_lut=None):
        """Injects provided stock data into this market.

        Generally used for generated data, but can be used in any case
        to bypass the default price LUT creation method.

        Args:
            ticker: A ticker for which to inject data
            dates: An array of dates corresponding to the prices
            prices: An array of prices corresponding to the dates
            price_lut: A price lookup table with dates mapping to
                prices to be used instead of building one from dates
                and prices
        """
        ticker = ticker.upper()
        self.stocks_indicators[ticker] = {}
        if price_lut:
            self.stocks[ticker] = price_lut
            return
        price_lut = {}
        for i in range(0, len(dates)):
            price_lut[dates[i]] = prices[i]
        self.stocks[ticker] = price_lut

    def current_date(self):
        """Returns the current date of this Market.

        Returns:
            A string representing the current date in this Market
        """
        return date_str(self.date[1])

    def query_stock(self, ticker, num_days=0):
        """Query a stock at the current date.

        Args:
            ticker: A ticker to query
            num_days: A value representing the number of days of prices
                going backwards from the current date to return. A
                value of 0 means only a float for today's value will be
                returned. A value >0 means an array of that many values
                will be returned (default: 0)

        Returns:
            A float representing the price of the stock
        """
        ticker = ticker.upper()
        if num_days:
            dates = self.dates[
                max(0, self.date[0] - num_days + 1):self.date[0] + 1]
            return [float(self.stocks[ticker][date]) for date in dates]
        try:
            return float(self.stocks[ticker][self.current_date()])
        except KeyError:
            print("NEEDS FIX: no data for " + ticker + " at " + self.date[1])
            return None

    def query_stock_indicator(self, ticker, indicator):
        """Query a stock indicator value or set of values at the
        current date.

        Args:
            ticker: A ticker to query
            indicator: An identifying string for the indicator value to
                return

        Returns:
            A float or set of floats representing the indicator
            value(s)
        """
        ticker = ticker.upper()
        indicator = indicator.upper()
        try:
            return float(
                self.stocks_indicators[ticker][indicator][self.current_date()])
        except KeyError:
            print('NEEDS FIX: no {} value for {} at {}'.format(
                indicator, ticker, self.current_date()))
            return None

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
            date_range = (max(date_range[0], dates[0]), min(
                date_range[1], dates[-1]))
            date_idxs = (dates.index(
                date_range[0]), dates.index(date_range[1]))
            self.dates = dates[date_idxs[0]:date_idxs[1] + 1]
        self.date = (0, self.dates[0])

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
        elif last_date.month != curr_date.month:
            self.new_period['m'] = True
            if (curr_date.month - 1) % 3 == 0:
                self.new_period['q'] = True
