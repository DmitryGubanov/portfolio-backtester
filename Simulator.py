import datetime
from datetime import datetime as dt

from utils import date_str, date_obj


class Simulator(object):

    """A simulator for how a portfolio would act in a market.

    Generally speaking, this is a coordinator between the Trader and
    the Market. A Market has stocks and dates, while a Trader has a
    Portfolio and strategies; both are indepedent, so this Simulator
    moves the Market and makes the Trader react to it.
    Additionally, this Simulator takes stats of the Portfolio at each
    day.

    Supported Statistics:
        - Per-day portfolio value history
        - Per-day asset allocation
        - Per-day contributions vs growth percent of total value
        - Per-year annual returns

    Attributes:
        trader: A Trader with a Portfolio
        market: A Market with stocks and dates
        dates_testing: A tuple indicating a range of dates to test
        dates_set: A tuple indicating whether or not each side of the
            testing dates range is set


    Todo:
        - [new feature] multiple portfolios/traders
        - [code improvement, medium priority] move stats into own class
    """

    stat_keys = ['PORT_VAL', 'ASST_ALLOC', 'ANN_RET', 'CONTR_GRWTH']

    def __init__(self):
        """Initializes an empty simulator."""
        self.trader = None
        self.market = None
        self.dates_set = (False, False)
        self.dates_testing = (None, None)
        self._init_stats()

    def add_trader(self, trader):
        """Sets the Trader for this Simulator.

        Args:
            trader: A Trader instance
        """
        self.trader = trader

    def set_market(self, market):
        """Sets the Market for this Simulator.

        Args:
            market: A Market instance
        """
        self.market = market

    def set_start_date(self, date):
        """Sets the start date for this Simulator.

        Args:
            date: A start date
        """
        self.dates_testing = (date, self.dates_testing[1])
        self.dates_set = (True, self.dates_set[1])

    def set_end_date(self, date):
        """Sets the end date for this Simulator.

        Args:
            date: An end date
        """
        self.dates_testing = (self.dates_testing[0], date)
        self.dates_set = (self.dates_set[0], True)

    def remove_date_limits(self):
        """Removes any date range for this Simulator."""
        self.dates_set = (False, False)
        self.dates_testing = (None, None)

    def simulate(self):
        """Runs this Simulator with the current configuration.

        Returns:
            -1 if a setup error occurs
            0  otherwise
        """
        if self._init_market() or self._init_dates() or self._init_portfolio():
            return -1
        while self.market.current_date() < self.dates_testing[1]:
            self.market.advance_day()
            self.trader.adjust_portfolio()
            self._record_stats()
        return 0

    def _init_market(self):
        """Initializes/resets the Market to work with the current
        Simulator setup.

        Returns:
            -1 if there is no Market to setup
            0  otherwise
        """
        if self.market == None:
            return -1
        if len(self.market.stocks) == 0:
            self.market.add_stocks(self.trader.assets_of_interest)
        if len(self.market.dates) == 0:
            self.market.set_default_dates()
        return 0

    def _init_dates(self):
        """Initializes/resets the testing dates for this Simulator

        Returns:
            0
        """
        if (not self.dates_set[0]
                or self.dates_testing[0] < self.market.dates[0]):
            self.dates_testing = (self.market.dates[0],
                                  self.dates_testing[1])
        else:
            self.market.set_date(self.dates_testing[0])
        if (not self.dates_set[1]
                or self.dates_testing[1] > self.market.dates[-1]):
            self.dates_testing = (self.dates_testing[0],
                                  self.market.dates[-1])

        self.dates_set = (True, True)
        return 0

    def _init_portfolio(self):
        """Initializes/resets the Portfolio(s) for this Simulator.

        Returns:
            A return code from Trader's initialize portfolio method
        """
        return self.trader.initialize_portfolio()

    def _init_stats(self):
        """Initializes/resets the stats for this Simulator."""
        self.stats = {}
        for key in self.stat_keys:
            self.stats[key] = [[], []]
            if key == self.stat_keys[2]:
                self.stats[key].append([])

    def _record_stats(self):
        """Takes a snapshot of the current Portfolio situation and
        records it."""
        # portfolio value history
        self.stats[self.stat_keys[0]][0].append(self.market.current_date())
        self.stats[self.stat_keys[0]][1].append(self.trader.portfolio.value())

        # asset allocation
        assets = sorted(self.trader.assets_of_interest)
        self.stats[self.stat_keys[1]][0].append(self.market.current_date())
        alloc = [(float(self.market.query_stock(asset))
                 * int(self.trader.portfolio.holdings[asset])
                 / self.trader.portfolio.value()) for asset in assets]

        self.stats[self.stat_keys[1]][1].append(alloc)

        # annual returns
        if (self.market.new_period['y']
                or len(self.stats[self.stat_keys[2]][2]) == 0):
            self.stats[self.stat_keys[2]][0].append(
                str(date_obj(self.market.current_date()).year - 1))
            self.stats[self.stat_keys[2]][1].append(
                self.trader.portfolio.value())
            if len(self.stats[self.stat_keys[2]][2]) == 0:
                self.stats[self.stat_keys[2]][2].append(0.0)
            else:
                self.stats[self.stat_keys[2]][2].append(
                    self.trader.portfolio.value()
                    / self.stats[self.stat_keys[2]][1][-2] - 1)

        # comtributions vs growth
        self.stats[self.stat_keys[3]][0].append(self.market.current_date())
        contribution = max(0, self.trader.portfolio.total_contributions)
        growth = max(0, self.trader.portfolio.value() - contribution)
        self.stats[self.stat_keys[3]][1].append((contribution, growth))
