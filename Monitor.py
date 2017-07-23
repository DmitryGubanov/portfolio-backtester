from utils import date_obj


class Monitor(object):

    """A Monitor for portfolios. Takes snapshots and records them for
    statistics purposes.

    Supported Statistics:
        - Per-day portfolio value history
        - Per-day asset allocation
        - Per-day contributions vs growth percent of total value
        - Per-year annual returns

    Attributes:
        portfolio: A Portfolio instance to monitor
        market: A Market instance to reference during monitoring
    """

    def __init__(self, portfolio, market):
        """Initializes a Monitior with a Portfolio and Market instance.

        Args:
            portfolio: A Portfolio instance to monitor
            market: A Market instance to reference during monitoring
        """
        # main attributes
        self.portfolio = portfolio
        self.market = market
        # records
        self._daily_value_history = {}
        self._annual_value_history = {}
        self._asset_alloc_history = {}
        self._contrib_vs_growth_history = {}
        self._annual_returns = {}
        # getter mapping
        self.data_series_getter_for = {
            'portfolio_values': self._get_portfolio_data_series,
            'asset_allocations': self._get_asset_alloc_data_series,
            'annual_returns': self._get_annual_returns_data_series,
            'contribution_vs_growth': self._get_contrib_vs_growth_data_series
        }

    def init_stats(self):
        """Runs any necessary setup that needs to happen before stats
        can be recorded."""

    def take_snapshot(self):
        """Records a snapshot of all supported stats for the Portfolio
        at the current date."""
        self._record_portfolio_value()
        self._record_asset_allocation()
        self._record_contribution_vs_growth()
        if self.market.new_period['y']:
            self._record_annual_return()

    def get_data_series(self, series):
        """Returns a set of data in a format meant for plotting.

        Args:
            series: A value representing the data series to get

        Returns:
            A set of X and Y series to be used in a plot
        """
        return self.data_series_getter_for[series]()

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
            ratio['contribution'] = (self.portfolio.total_contributions
                                     / self.portfolio.value())
            ratio['growth'] = max(0, 1 - ratio['contribution'])
        self._contrib_vs_growth_history[self.market.current_date()] = ratio

    def _record_annual_return(self):
        """Internal method for recording the Portfolio's annual
        returns."""
        this_year = date_obj(self.market.current_date()).year
        if len(self._annual_value_history) > 1:
            self._annual_returns[str(this_year - 1)] = \
                (self._annual_value_history[str(this_year)]
                 / self._annual_value_history[str(this_year - 1)]
                 - 1)

    def _get_portfolio_data_series(self):
        """Internal function which returns a data series for a
        portfoio's value history.

        Returns:
            A set of X and Y values meant to be plotted
        """
        return ([0], [0])

    def _get_asset_alloc_data_series(self):
        """Internal function which returns a data series for a
        portfolio's asset allocation history.

        Returns:
            A set of X and Y values meant to be plotted
        """
        return ([0], [0])

    def _get_annual_returns_data_series(self):
        """Internal function which returns a data series for a
        portfolio's annual returns.

        Returns:
            A set of X and Y values meant to be plotted
        """
        return ([0], [0])

    def _get_contrib_vs_growth_data_series(self):
        """Internal function which returns a data series for a
        history of a portfolio's contribution vs growth as a percent
        of the whole portfolio.

        Returns:
            A set of X and Y values meant to be plotted
        """
        return ([0], [0])
