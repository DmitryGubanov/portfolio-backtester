###
# A Market containing stocks and a date. The Market can be queried for stock prices at
# the current date of the market
##
class Market:

    ##
    # initialize Market with a set of dates and stocks w/ price LUTs
    def __init__(self, tickers, dates):
        self.new_period = {'m': False, 'q': False, 'y': False}
        self.stocks = {}
        if tickers != None:
            self.add_stocks(tickers)
        self.dates = None
        if dates != None:
            self.dates = dates
            self.date = (0, self.dates[0])

    ##
    # creates LUTs for a given set of stocks
    def add_stocks(self, tickers):
        for ticker in tickers:
            self.stocks[ticker.upper()] = build_price_lut(ticker.upper())

    ##
    # injects provided stock data into this market - used for generated data
    def inject_stock_data(self, ticker, dates, prices):
        price_lut = {}
        for i in range(0, len(dates)):
            price_lut[dates[i]] = prices[i]
        self.stocks[ticker.upper()] = price_lut

    ##
    # returns the current date of the Market
    def current_date(self):
        return self.date[1]

    ##
    # queries a stock at today's date
    def query_stock(self, ticker):
        try:
            return float(self.stocks[ticker.upper()][self.date[1]])
        except KeyError:
            # TODO
            print("NEEDS FIX: no data for " + ticker + " at " + self.date[1])
            return 0

    #def __recursive_query_stock(self, ticker, date_idx):
    #    if date_idx < 0:
    #        return 0
    #    try:
    #        return float(self.stocks[ticker][self.dates[date_idx]])
    #    except KeyError:
    #        return self.__recursive_query_stock(ticker, date_idx - 1)

    ##
    # sets the market to a certain date
    def set_date(self, date):
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
            # TODO
            print("NEEDS FIX: date does not exist")
            return 1
            #return self.set_date(date_str(date_obj(date) + datetime.timedelta(1)))

    ##
    # adjusts the current date range to a range in which all market's stocks have data
    def set_default_dates(self):
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

    ##
    # advances the day by one
    def advance_day(self):
        self.date = (self.date[0] + 1, self.dates[self.date[0] + 1])
        self.__raise_period_flags()

    ##
    # raises a flag if a new period has started (monthl, quarter, year...)
    def __raise_period_flags(self):
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
