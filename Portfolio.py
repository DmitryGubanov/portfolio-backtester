class Portfolio(object):

    """A Portfolio with cash, assets (definition of stocks to be held),
    and holdings (stocks actually held).

    This portfolio should not do anything on its own, i.e. should not
    house any business logic with regards to trading or positioning,
    but rather act as a container for assets to be acted on by an
    outside agent.

    Attributes:
        cash: A float representing the amount of cash in this Portfolio
        total_contributions: A counter for contributions
        holdings: A mapping of holdings to a number of shares

    Todo:
        - [code improvement, low priority] portfolio interacts with
            Market for market prices and commissions, instead of taking
            those args
        - [code improvement, low priority] market should be private,
            since it's not this Portfolio's market technically
    """

    def __init__(self, cash=0):
        """Initializes an empty Portfolio.

        Args:
            cash: A cash value for this Portfolio to start at,
                default: 0
        """
        self._market = None
        self.cash = float(cash)
        self.starting_cash = float(cash)
        self.total_contributions = 0
        self.holdings = {}
        self.trades = 0

    def use_market(self, market):
        """Sets the market this Portfolio should use for looking up
        prices.

        Args:
            market: A Market instance to use
        """
        self._market = market

    def add_cash(self, amount):
        """Adds a certain amount of cash to the portfolio.

        Args:
            amount: A value representing the amount of cash to add
        """
        self.cash += float(amount)
        self.total_contributions += float(amount)

    def buy(self, ticker, amount):
        """Adds a holding to the portfolio in the form of a buy.

        Args:
            ticker: A string for the ticker of the holding to add
            amount: A value for the number of shares to buy
        """
        if amount == 0:
            return 0
        self.trades += 1
        price = float(self._market.query_stock(ticker))
        if (float(amount) * price) > (self.cash - self._market.commissions):
            print('ERROR: not enough cash({}) to buy {}x{} at {} on {}'.format(
                self.cash, ticker, amount, price, self._market.current_date()))
            print('APPLYING FIX: buying {}x{} instead'.format(
                ticker, int((self.cash - self._market.commissions) / price)))
            return self.buy(ticker, int((self.cash - self._market.commissions)
                                        / price))
        try:
            self.holdings[ticker.upper()] += int(amount)
        except KeyError:
            self.holdings[ticker.upper()] = int(amount)
        self.cash -= int(amount) * price + self._market.commissions
        return 0

    def sell(self, ticker, amount):
        """Removes a holding from the portfolio in the form of a sell.

        Args:
            ticker: A string for the ticker of the holding to remove
            amount: A value for the number of shares to sell
        """
        if amount == 0:
            return 0
        self.trades += 1
        price = float(self._market.query_stock(ticker))
        try:
            self.holdings[ticker.upper()] -= int(amount)
        except KeyError:
            self.holdings[ticker.upper()] = -int(amount)
        self.cash += int(amount) * price - self._market.commissions
        return 0

    # def short(self, ticker, amount, price, commission):
    #     """Adds a holding to the portfolio in the form of a short, i.e.
    #     negative shares.
    #
    #     Shorting is significantly more involved and contingent on more
    #     variables, so this feature is experimental and not complete.
    #     Currently not used in main program, but still referenced.
    #
    #     Args:
    #         ticker: A string for the ticker of the holding to short
    #         amount: A value for the number of shares to sell
    #         price: A value corresponding to the price of each share
    #         commission: A value corresponding to the cost of the trade
    #     """
    #     self.sell(ticker, amount, price, commission)
    #
    # def cover(self, ticker, amount, price, commission):
    #     """Removes a holding from the portfolio in the form of a cover
    #     i.e. removes existing negative shares.
    #
    #     Shorting is significantly more involved and contingent on more
    #     variables, so this feature is experimental and not complete.
    #     Currently not used in main program, but still referenced.
    #
    #     Args:
    #         ticker: A string for the ticker of the holding to cover
    #         amount: A value for the number of shares to sell
    #         price: A value corresponding to the price of each share
    #         commission: A value corresponding to the cost of the trade
    #     """
    #     self.buy(ticker, amount, price, commission)

    def value(self):
        """Returns the total value of this Portfolio (cash + holdings).

        Returns:
            A value correspondingto the total value of this Portfolio
        """
        return self.cash + sum(
            [float(self.holdings[asset] * self._market.query_stock(asset))
             for asset in self.holdings.keys()])

    def shares_of(self, ticker):
        """Returns the number of shares this portfolio is holding of a
        given ticker."""
        try:
            shares = self.holdings[ticker.upper()]
        except KeyError:
            shares = 0
        return shares
