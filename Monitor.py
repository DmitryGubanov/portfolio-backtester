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
            'adjusted_cagr': self._get_adjusted_cagr
        }
        # TODO remove?
        # self._indicator_getter_for = {
        #     'sma': self._get_sma,
        #     'ema': self._get_ema,
        #     'macd': self._get_macd
        # }

    def init_stats(self):
        """Runs any necessary setup that needs to happen before stats
        can be recorded."""
        # init internal values used in record keeping
        self._dates = []
        self._all_assets = {}
        self._daily_value_history = {}
        self._annual_value_history = {}
        self._asset_alloc_history = {}
        self._contrib_vs_growth_history = {}
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
        self._daily_value_history[self.market.current_date()] \
            = self.portfolio.value()
        if self.market.new_period['y'] or len(self._annual_value_history) == 0:
            curr_year = str(date_obj(self.market.current_date()).year)
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

    def _record_annual_return(self):
        """Internal method for recording the Portfolio's annual
        returns."""
        if not self.market.new_period['y']:
            return
        this_year = date_obj(self.market.current_date()).year
        if len(self._annual_value_history) > 1:
            self._annual_returns[str(this_year - 1)] = \
                (self._annual_value_history[str(this_year)]
                 / self._annual_value_history[str(this_year - 1)]
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
