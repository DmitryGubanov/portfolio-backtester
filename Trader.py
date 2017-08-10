from Brain import Brain


class Trader(object):
    """A Trader is meant to emulate the role of a trader in the stock
    market.

    A Trader will have a Portfolio and make decisions based on a set of
    criteria.

    Supported Portfolio Management:
        - contributions every month/quarter/year
        - rebalancing every month/quarter/year

    Attributes:
        portfolio: A Portfolio instance to manage
        assets_of_interest: An array of strings, each of which
            represent a ticker of interest

    Todo:
        - [new feature] reimplement withdrawals
        - [new feature] dynamic strategies (need to plan specifics)
    """

    def __init__(self, starting_cash, portfolio, market):
        """Initializes a Trader.

        Args:
            starting_cash: A value representing the amount of cash this
                Trader starts with
            portfolio: A Portfolio to be managed by this Trader
            assets_of_interest: An array of strings, each of which
                represent a ticker of interest
        """
        # general setup
        self._brain = Brain()
        self._contributions = None
        self.use_portfolio(portfolio)
        self.use_market(market)
        self.set_starting_cash(starting_cash)

        # asset management
        # self._desired_asset_ratios = {}
        # self._desired_asset_shares = {}
        # self._desired_trades = {'sell': {}, 'buy': {}}
        # contributions

        # self._strategy_settings = {
        #     'contributions': None,
        #     'rebalancing': None
        # }
        # self._strategies = {
        #     'contributions': self._contribute,
        #     'rebalancing': self._rebalance
        # }

    def use_portfolio(self, portfolio):
        """Sets the Portfolio this Trader should use. Propagates the
        Portfolio to the Brain as well.

        Args:
            portfolio: A Portfoio instance to use
        """
        self.portfolio = portfolio
        self._brain.use_portfolio(portfolio)

    def use_market(self, market):
        """Sets the market this Trader should use for looking up
        prices. Propagates the Market to the Brain as well.

        Args:
            market: A Market instance to use
        """
        self._market = market
        self._brain.use_market(market)
        self.portfolio.use_market(market)

    def set_starting_cash(self, amount):
        """Sets the starting cash of this trader.

        Args:
            amount: A value representing the starting cash
        """
        self.starting_cash = float(amount)
        self.portfolio.starting_cash = float(amount)

    def set_contributions(self, amount, period):
        """Sets the amount of cash to contribute per period.

        Args:
            amount: A value representing the amount to contribute
            period: A value representing the frequency of contributions
                e.g. 'm' for monthly
        """
        self._contributions = (amount, period)

    def set_rebalancing_period(self, period):
        """Sets the rebalancing frequency. Propagates the value to the
        Brain. The Trader will rebalance every new period, regardless
        of ratios or if the Portfolio was recently rebalanced.

        Args:
            period: A value representing the frequency of rebalancing
                e.g. 'm' for monthly
        """
        self._brain.set_rebalancing_period(period)

    def set_strategy(self, strategy):
        """Sets to one of the predefined strategies."""
        self._brain.set_strategy(strategy)

    def initialize_portfolio(self):
        """Sets up the portfolio to the current desired ratios.
        Intended to run once at start."""
        self.portfolio.add_cash(self.starting_cash)
        self._brain.decide_needed_shares()
        self._execute_trades()

    def adjust_portfolio(self):
        """Decides a new portfolio asset allocation, if applicable, and
        adjusts the Portfolio to it."""
        self._contribute()
        self._brain.decide_needed_shares()
        self._execute_trades()

    def get_assets_of_interest(self):
        """Returns this Trader's assets of interest.

        Returns:
            A list of assets
        """
        return self._brain.assets_of_interest.copy()

    def add_asset_of_interest(self, ticker):
        """Adds a ticker for an asset to the assets of interest.

        Args:
            ticker: A string representing the ticker of a desired asset
        """
        self._brain.assets_of_interest.append(ticker.upper())

    def set_desired_asset_ratio(self, ticker, ratio):
        """Sets an allocation for an asset.

        Args:
            ticker: A string representing the ticker of a desired asset
            ratio: An int corresponding to the desired ratio for the
                given ticker
        """
        self._brain.desired_asset_ratios[ticker] = ratio

    # def _calculate_desired_shares(self):
    #     """Calculates the shares required of each asset, to satisfy the
    #     desired ratios."""
    #     for asset in self._brain.assets_of_interest:
    #         self._brain.desired_asset_shares[asset] = int(
    #             self.portfolio.value()
    #             * self._brain.desired_asset_ratios[asset]
    #             / self._market.query_stock(asset))

    def _execute_trades(self):
        """Calculates the trades needed to be made to satisfy the
        desired shares and executes the trades.

        NOTE: Sometimes there isn't the right amount of cash for a buy,
            in which case a buy/sell performs the maximum amount it can
            do. As a result, the desired shares need to be updated to
            avoid trying to buy/sell the remaining shares every
            following day."""
        # calculate trades needed
        desired_trades = {'buy': {}, 'sell': {}}
        # TODO sort out whole assets of interest shit
        for asset in self._brain.assets_of_interest:
            change = (self._brain.desired_shares[asset]
                      - self.portfolio.shares_of(asset))
            if change < 0:
                desired_trades['sell'][asset] = abs(change)
            elif change > 0:
                desired_trades['buy'][asset] = abs(change)
        # perform sells
        for (ticker, amount) in desired_trades['sell'].items():
            self.portfolio.sell(ticker, amount)
            self._brain.desired_shares[ticker] \
                = self.portfolio.shares_of(ticker)
        # perform buys
        for (ticker, amount) in desired_trades['buy'].items():
            self.portfolio.buy(ticker, amount)
            self._brain.desired_shares[ticker] \
                = self.portfolio.shares_of(ticker)

    def _contribute(self):
        """Contributes to the portfolio according to the set
        contribution settings."""
        if self._contributions == None:
            return
        if self._market.new_period[self._contributions[1]]:
            self.portfolio.add_cash(float(self._contributions[0]))

    # def _rebalance(self):
    #     """Rebalances the portfolio according to the set rebalancing
    #     settings."""
    #     if self._rebalancing_period == None:
    #         return
    #     if self._market.new_period[self._rebalancing_period]:
    #         # rebalance
