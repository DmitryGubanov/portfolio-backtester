import datetime
from datetime import datetime as dt

from utils import date_str
from utils import date_obj


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
        dates_testing: A tuple indicating a range of dates to test

    Todo:
        - [new feature] multiple portfolios/traders
    """

    stat_keys = ['PORT_VAL', 'ASST_ALLOC', 'ANN_RET', 'CONTR_GRWTH']

    def __init__(self):
        """Initializes an empty simulator."""
        self._trader = None
        self._market = None
        self._monitor = None
        self.dates_testing = (None, None)

    def add_trader(self, trader):
        """Sets the Trader for this Simulator.

        Args:
            trader: A Trader instance
        """
        self._trader = trader

    def use_market(self, market):
        """Sets the Market for this Simulator to use.

        Args:
            market: A Market instance to use
        """
        self._market = market

    def use_monitor(self, monitor):
        """Sets the Monitor for this Simulator to use.

        Args:
            monitor: A Monitor instance to use
        """
        self._monitor = monitor

    def set_start_date(self, date):
        """Sets the start date for this Simulator.

        Args:
            date: A start date
        """
        self.dates_testing = (date_str(date), self.dates_testing[1])

    def set_end_date(self, date):
        """Sets the end date for this Simulator.

        Args:
            date: An end date
        """
        self.dates_testing = (self.dates_testing[0], date_str(date))

    def remove_date_limits(self):
        """Removes any date range for this Simulator."""
        self.dates_testing = (None, None)

    def simulate(self):
        """Runs this Simulator with the current configuration."""
        self._init_market()
        self._init_dates()
        self._init_trader()
        self._monitor.init_stats()
        while self._market.current_date() < self.dates_testing[1]:
            self._market.advance_day()
            self._trader.adjust_portfolio()
            self._monitor.take_snapshot()

    def _init_market(self):
        """Initializes/resets the Market to work with the current
        Simulator setup.

        Specifically, adds all stocks to the Market and resets the
        Market's dates."""
        for asset in self._trader.assets_of_interest:
            if asset not in self._market.stocks.keys():
                self._market.add_stocks(self._trader.assets_of_interest)
        self._market.set_default_dates()

    def _init_dates(self):
        """Initializes/resets the testing dates for this Simulator.

        Specifically, aligns the Simulator's dates with the Market's
        dates."""
        if (not self.dates_testing[0]
            or self.dates_testing[0] < self._market.dates[0]):
            self.dates_testing = (self._market.dates[0],
                                  self.dates_testing[1])
        else:
            self._market.set_date(self.dates_testing[0])
        if (not self.dates_testing[1]
                or self.dates_testing[1] > self._market.dates[-1]):
            self.dates_testing = (self.dates_testing[0],
                                  self._market.dates[-1])

    def _init_trader(self):
        """Initializes/resets the Trader(s) for this Simulator.

        Specifically, asigns a Market for the Trader to uses and
        initializes the Trader's Portfolio.
        """
        self._trader.use_market(self._market)
        self._trader.initialize_portfolio()
