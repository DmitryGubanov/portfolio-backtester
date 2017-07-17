
class Trader(object):
    """A Trader is meant to emulate the role of a trader in the stock market.

    A Trader will have a Portfolio and make decisions based on a set of criteria.

    Attributes:
        portfolio: A Portfolio instance to manage
        assets_of_interest: An array of strings, each of which represent a ticker of interest
    """

    def __init__(self, market=None, starting_cash=0, portfolio=None, assets_of_interest=[]):
        """Initializes a Trader.

        Args:
            market: A Market in which this Trader participates
            starting_cash: A value representing the amount of cash this Trader starts with
            portfolio: A Portfolio instance to be managed by this Trader
            assets_of_interest: An array of strings, each of which represent a ticker of interest
        """
        # general
        self.market = market # TODO: make setter
        self.set_starting_cash(starting_cash)
        self.portfolio = portfolio # TODO: make setter
        self.assets_of_interest = []
        for asset in assets_of_interest:
            self.add_asset_of_interest(asset)
        # asset management
        self._desired_asset_ratios = {}
        self._desired_asset_shares = {}
        self._desired_trades = {'sell': {}, 'buy': {}}
        # strategy management
        self._strategy_ordering = [
            'contributions', 'rebalancing'
        ]
        self._strategy_settings = {
            'contributions': None,
            'rebalancing': None
        }
        self._strategies = {
            'contributions': self._contribute,
            'rebalancing': self._rebalance
        }

    def set_starting_cash(self, amount):
        """Sets the starting cash of this trader.

        Args:
            amount: A value representing the starting cash
        """
        self.starting_cash = float(amount)

    def set_strategy(self, strategy, setting):
        """Sets one of the predefined strategies to a certain setting.

        Strategy setting formats:
            contributions: [period/frequency, amount], e.g. ['m', 1000] for 1000/month
            rebalancing: [period/frequency], e.g. ['q'] for quarterly rebalance

        Args:
            strategy: A string representing a strategy
            setting: A setting for that strategy"""
        self._strategy_settings[strategy] = setting

    def initialize_portfolio(self):
        """Sets up the portfolio to the current desired ratios. Intended to run once at start."""
        if self.portfolio == None:
            return -1
        self.portfolio.add_cash(self.starting_cash)
        self._calculate_desired_shares()
        self._calculate_trades_needed()
        self._execute_trades()
        return 0

    def adjust_portfolio(self):
        """Decides a new portfolio asset allocation, if applicable, and adjusts the Portfolio to it."""
        #self._update_desired_asset_allocation() TODO: worry about this later
        for strategy in self._strategy_ordering:
            self._strategies[strategy]()

    def add_asset_of_interest(self, ticker):
        """Adds a ticker for an asset to the list of assets of interest.

        Args:
            ticker: A string representing the ticker of a desired asset
        """
        self.assets_of_interest.append(ticker.upper())

    def set_desired_asset_ratio(self, ticker, ratio):
        """Sets an allocation for an asset.

        Args:
            ticker: A string representing the ticker of a desired asset
            ratio: An int corresponding to the desired ratio for the given ticker
        """
        self._desired_asset_ratios[ticker] = ratio

    # TODO: worry about this with dynamic portfolios
    #def _update_desired_asset_allocation(self):
    #    """Uses the current market state to decide new portfolio asset allocations."""
    #    pass

    def _calculate_desired_shares(self):
        """Calculates the shares required of each asset, to satisfy the desired ratios."""
        for asset in self.assets_of_interest:
            self._desired_asset_shares[asset] = int(self.portfolio.value() * self._desired_asset_ratios[asset] / self.market.query_stock(asset))
            #print(asset + " cost on " + self.market.current_date())
            #print( + self.market.query_stock(asset))
        #print("desired shares")
        #print(self._desired_asset_shares)

    def _calculate_trades_needed(self):
        """Calculates the trades needed to be made to satisfy the desired shares."""
        for asset in self.assets_of_interest:
            change = self._desired_asset_shares[asset] - self.portfolio.shares_of(asset)
            if change < 0:
                self._desired_trades['sell'][asset] = abs(change)
            elif change > 0:
                self._desired_trades['buy'][asset] = abs(change)
        #print("desired trades")
        #print(self._desired_trades)

    def _execute_trades(self):
        """Executes the trades required to have the desired shares of each asset."""
        # TODO: when market singleton, remove market.query and commission args
        # perform sells
        for trade in list(self._desired_trades['sell'].items()):
            #print("selling {} shares of {}".format(trade[1], trade[0]))
            self.portfolio.sell(trade[0], trade[1], self.market.query_stock(trade[0]), 0)
            del(self._desired_trades['sell'][trade[0]])
        # perform buys
        for trade in list(self._desired_trades['buy'].items()):
            #print("buying {} shares of {}".format(trade[1], trade[0]))
            self.portfolio.buy(trade[0], trade[1], self.market.query_stock(trade[0]), 0)
            del(self._desired_trades['buy'][trade[0]])
        #self._desired_trades = {'sell': {}, 'buy': {}}

    def _contribute(self):
        """Contributes to the portfolio according to the set contribution settings."""
        if self._strategy_settings['contributions'] == None:
            return
        if self.market.new_period[self._strategy_settings['contributions'][0]]:
            self.portfolio.add_cash(self._strategy_settings['contributions'][1])

    def _rebalance(self):
        """Rebalances the portfolio according to the set rebalancing settings."""
        if self._strategy_settings['rebalancing'] == None:
            return
        if self.market.new_period[self._strategy_settings['rebalancing'][0]]:
            self._calculate_desired_shares()
            self._calculate_trades_needed()
            self._execute_trades()
