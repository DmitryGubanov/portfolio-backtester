from datetime import timedelta
from math import sqrt

from utils import date_obj
from utils import days_between


class Monitor(object):

    """A Monitor for market and portfolio data in simulations, used by
    taking snapshots of a market and portfolio at various stages in a
    simulation.

    More specifically, as snapshots are taken - on a daily basis - the
    data taken from those snapshots is recorded and interpretted to
    provide a means for retrieving statistics (e.g. value history,
    indicators, max drawdowns, etc.)

    Supported portfolio statistics and data series:
        - Per-day portfolio value history
        - Per-day asset allocation
        - Per-day contributions vs growth percent of total value
        - Per-year annual returns
        - Max drawdown
        - CAGR calculation
        - Adjusted CAGR calculation

    Supported indicators:
        - Standard Moving Average (SMA) for a given period
        - Exponential Moving Average (EMA) for a given period
        - Moving Average Convergence/Divergence (MACD) for a given
            set of periods

    Attributes:
        portfolio: A Portfolio instance to monitor
        market: A Market instance to reference during monitoring
    """

    def __init__(self, trader, market):
        """Initializes a Monitior with a Portfolio and Market instance.

        Args:
            trader: A Trader instance to monitor
            market: A Market instance to reference during monitoring
        """
        # main attributes
        self.trader = trader
        self.portfolio = trader.portfolio
        self.market = market
        # getter mappings
        self._data_series_getter_for = {
            'portfolio_values': self._get_portfolio_value_data_series,
            'asset_allocations': self._get_asset_alloc_data_series,
            'annual_returns': self._get_annual_returns_data_series,
            'contribution_vs_growth': self._get_contrib_vs_growth_data_series
        }
        self._statistic_getter_for = {
            'max_drawdown': self._get_max_drawdown,
            'cagr': self._get_cagr,
            'adjusted_cagr': self._get_adjusted_cagr,
            'sharpe_ratio': self._get_sharpe_ratio,
            'sortino_ratio': self._get_sortino_ratio
        }

    def init_stats(self):
        """Runs any necessary setup that needs to happen before stats
        can be recorded."""
        # init internal values used in record keeping
        self._dates = []
        self._all_assets = {}
        self._daily_value_history = {}
        self._monthly_value_history = {}
        self._annual_value_history = {}
        self._asset_alloc_history = {}
        self._contrib_vs_growth_history = {}
        self._daily_returns = {}
        self._monthly_returns = {}
        self._annual_returns = {}
        self._max_drawdown = {
            'amount': 0, 'from': None, 'to': None, 'recovered_by': None
        }
        self._portfolio_max = 0
        self._portfolio_min_since_max = 0
        self._potential_drawdown_start = None
        # init all assets to be monitored
        self._all_assets = self.trader.get_assets_of_interest()

    def take_snapshot(self):
        """Records a snapshot of all supported stats for the Portfolio
        at the current date."""
        self._dates.append(self.market.current_date())
        self._record_portfolio_value()
        self._record_asset_allocation()
        self._record_contribution_vs_growth()
        self._record_monthly_return()
        self._record_annual_return()
        self._update_drawdown()

    def get_data_series(self, series):
        """Returns a set of data in a format meant for plotting.

        Args:
            series: A string representing the data series to get

        Returns:
            A set of X and Y series to be used in a plot
        """
        return self._data_series_getter_for[series]()

    def get_statistic(self, statistic):
        """Returns a statistic for the monitored Portfolio(s).

        Args:
            statistic: A string representing the statistic to get

        Returns:
            A value or set of values corresponding to the desired
            statistic
        """
        return self._statistic_getter_for[statistic]()

    def get_indicator(self, indicator, ticker):
        """Returns an indicator value or values for the monitored Portfolio(s).

        Args:
            indicator: A string representing the statistic to get
            ticker: A string representing the ticker for a stock

        Returns:
            A value or set of values corresponding to the desired
            statistic
        """
        return self.market.query_stock_indicator(ticker, indicator)

    def _record_portfolio_value(self):
        """Internal method for recording the Portfolio value."""
        (curr_year, curr_month, _) = self.market.current_date().split('-')
        self._daily_value_history[self.market.current_date()] \
            = self.portfolio.value()
        if self.market.new_period['m'] or not len(self._monthly_value_history):
            self._monthly_value_history[curr_year + '-' + curr_month] \
                = self.portfolio.value()
        if self.market.new_period['y'] or not len(self._annual_value_history):
            self._annual_value_history[curr_year] \
                = self.portfolio.value()

    def _record_asset_allocation(self):
        """Internal method for recording the asset allocation of the
        Portfolio."""
        alloc = {}
        for asset, shares in self.portfolio.holdings.items():
            if self.portfolio.value() == 0:
                alloc[asset] = 0
            else:
                alloc[asset] = (self.market.query_stock(asset) * int(shares)
                                / self.portfolio.value())
        self._asset_alloc_history[self.market.current_date()] = alloc

    def _record_contribution_vs_growth(self):
        """Internal method for recording the percentages of the
        Portfolio value which are from growth and contributions."""
        ratio = {'contribution': 1, 'growth': 0}
        if self.portfolio.value() != 0:
            ratio['contrib'] = (self.portfolio.total_contributions
                                / self.portfolio.value())
            ratio['growth'] = max(0, 1 - ratio['contrib'])
        self._contrib_vs_growth_history[self.market.current_date()] = ratio

    def _record_monthly_return(self):
        """Internal method for recording the Portfolio's monthly
        returns."""
        if (not self.market.new_period['m']
                or len(self._monthly_value_history) <= 1):
            return
        this_dt = date_obj(self.market.current_date())
        last_dt = (date_obj(self.market.current_date()).replace(day=1)
                   - timedelta(1))
        this_month = str(this_dt.year) + '-' + ('0' + str(this_dt.month))[-2:]
        last_month = str(last_dt.year) + '-' + ('0' + str(last_dt.month))[-2:]
        self._monthly_returns[last_month] = \
            (self._monthly_value_history[this_month]
             / self._monthly_value_history[last_month]
             - 1)

    def _record_annual_return(self):
        """Internal method for recording the Portfolio's annual
        returns."""
        if (not self.market.new_period['y']
                or len(self._annual_value_history) <= 1):
            return
        (this_year, _, _) = self.market.current_date().split('-')
        last_year = str(int(this_year) - 1)
        self._annual_returns[last_year] = \
            (self._annual_value_history[this_year]
             / self._annual_value_history[last_year]
             - 1)

    def _update_drawdown(self):
        """Updates the maximum drawdown for this Monitor's
        Portfolio."""
        if self.portfolio.value() >= self._portfolio_max:
            self._potential_drawdown_start = None
            self._portfolio_max = self.portfolio.value()
            self._portfolio_min_since_max = self._portfolio_max
            if not self._max_drawdown['recovered_by']:
                self._max_drawdown['recovered_by'] = self.market.current_date()
            return
        if self.portfolio.value() < self._portfolio_min_since_max:
            if not self._potential_drawdown_start:
                self._potential_drawdown_start = self.market.current_date()
            self._portfolio_min_since_max = self.portfolio.value()
            drawdown = self._portfolio_min_since_max / self._portfolio_max - 1
            if drawdown < self._max_drawdown['amount']:
                self._max_drawdown['amount'] = drawdown
                self._max_drawdown['from'] = self._potential_drawdown_start
                self._max_drawdown['to'] = self.market.current_date()
                self._max_drawdown['recovered_by'] = None

    def _get_portfolio_value_data_series(self):
        """Internal function which returns a data series for a
        portfoio's value history.

        The dates in the data series are returned as datetime objects,
        while the value is stored as floats. e.g.
        ([<datetime_obj>, ...], [10000.00, ...])

        Returns:
            A tuple of X and Y values meant to be plotted
        """
        dates = sorted(self._daily_value_history.keys())
        return ([date_obj(date) for date in dates],
                [self._daily_value_history[date] for date in dates])

    def _get_asset_alloc_data_series(self):
        """Internal function which returns a tuple of data series in
        (x, y) format for a portfolio's asset allocation history.

        The dates in the data series are returned as datetime objects,
        while the allocation ratios are in sets of floats. e.g.
        ([<datetime_obj>, ...], [[0.4, ...], [0.3, ...], ...])

        Returns:
            A set of X and Y values meant to be plotted
        """
        dates = sorted(self._asset_alloc_history.keys())
        allocs = [[] for i in range(len(self._all_assets))]
        for date in dates:
            for index, asset in enumerate(sorted(self._all_assets)):
                try:
                    alloc = self._asset_alloc_history[date][asset]
                except KeyError:
                    alloc = 0
                allocs[index].append(alloc)
        return ([date_obj(date) for date in dates], allocs)

    def _get_annual_returns_data_series(self):
        """Internal function which returns a tuple of data series in
        (x, y) format for a portfolio's annual returns.

        The dates in the data series are returned as string
        representation of years, while annual returns are in a set of
        floats. e.g. (['2009', ...], [0.45, ...])

        Returns:
            A set of X and Y values meant to be plotted
        """
        years = sorted(self._annual_returns.keys())
        return ([str(year) for year in years],
                [self._annual_returns[year] for year in years])

    def _get_contrib_vs_growth_data_series(self):
        """Internal function which returns a tuple of data series in
        (x, y) format for a history of a portfolio's contribution vs
        growth as a percent of the whole portfolio.

        The dates in the data series are returned as datetime objects,
        while the contributions and growth are in sets of floats. e.g.
        ([<datetime_obj>, ...], [[0.4, ...] [0.6, ...]])

        Returns:
            A set of X and Y values meant to be plotted
        """
        dates = sorted(self._daily_value_history.keys())
        ratios = [[], []]
        for date in dates:
            ratios[0].append(self._contrib_vs_growth_history[date]['contrib'])
            ratios[1].append(self._contrib_vs_growth_history[date]['growth'])
        return ([date_obj(date) for date in dates], ratios)

    def _get_max_drawdown(self):
        """Internal function for returning the max drawdown.

        Returns:
            A dictionary in the form:
                {'amount': <val>,
                 'from': <date_str>,
                 'to': <date_str>,
                 'recovered by': <date_str>}
        """
        return self._max_drawdown.copy()

    def _get_cagr(self):
        """Internal function for calculating the Cumulative Annual
        Growth Rate.

        Returns:
            A value representing the CAGR
        """
        start_val = self.portfolio.starting_cash
        end_val = self.portfolio.value()
        years = days_between(self._dates[0], self._dates[-1]) / 365.25
        return (end_val / start_val) ** (1 / years) - 1

    def _get_adjusted_cagr(self):
        """Internal function for calculating the adjusted Cumulative
        Annual Growth Rate.

        Returns:
            A value representing the adjusted CAGR
        """
        start_val = self.portfolio.starting_cash
        end_val = self.portfolio.value()
        years = days_between(self._dates[0], self._dates[-1]) / 365.25
        contrib = self.portfolio.total_contributions
        return ((end_val - contrib + start_val) / start_val) ** (1 / years) - 1

    def _get_sortino_ratio(self):
        """Internal function for calculating the Sortino ratio of a
        portfolio.

        Returns:
            A value representing the Sortino ratio.
        """
        # risk_free_return = 0.01  # yearly 08/2017 1-month T-bill rate
        risk_free_return = 0.00083  # monthly 08/2017 1-month T-bill rate
        # excess_returns
        excess_returns = []
        neg_excess_returns = []
        for ret in self._monthly_returns.values():
            excess_returns.append(ret - risk_free_return)
            if ret - risk_free_return < 0:
                neg_excess_returns.append(ret - risk_free_return)
        excess_return_mean = sum(excess_returns) / len(excess_returns)
        neg_excess_return_mean = (sum(neg_excess_returns)
                                  / len(neg_excess_returns))
        # standard deviation
        if len(neg_excess_returns) <= 1:
            return 'undef'
        stdev = sqrt(
            sum([(ret - neg_excess_return_mean) ** 2
                 for ret in neg_excess_returns])
            / len(excess_returns))
        return excess_return_mean / stdev

    def _get_sharpe_ratio(self):
        """Internal function for calculating the Sharpe ratio of a
        portfolio.

        Returns:
            A value representing the Sharpe ratio.
        """
        # risk_free_return = 0.01  # yearly 08/2017 1-month T-bill rate
        risk_free_return = 0.00083  # monthly 08/2017 1-month T-bill rate
        # excess_returns
        excess_returns = []
        for ret in self._monthly_returns.values():
            excess_returns.append(ret - risk_free_return)
        excess_return_mean = sum(excess_returns) / len(excess_returns)
        # standard deviation
        stdev = sqrt(
            sum([(ret - excess_return_mean) ** 2 for ret in excess_returns])
            / len(excess_returns))
        return excess_return_mean / stdev
