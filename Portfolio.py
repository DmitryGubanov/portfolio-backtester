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
        holdings_values: A mapping of holdings to a cash value
        assets: A map of assets to a ratio
            (potentially deprecated)
        assets_types: A map of assets to either 'long' or 'short'
            (potentially deprecated)

    Todo:
        - (low priority) holding_values is sort of unnecessary
        - (low priority) portfolio interacts with singleton Market for
            market prices and commissions, instead of taking those args
    """

    def __init__(self, cash=0):
        """Initializes an empty Portfolio.

        Args:
            cash: A cash value for this Portfolio to start at,
                default: 0
        """
        self.cash = float(cash)
        self.total_contributions = 0
        self.holdings = {}
        self.holdings_values = {}
        self.assets = {}
        self.assets_types = {}

    def add_cash(self, amount):
        """Adds a certain amount of cash to the portfolio.

        Args:
            amount: A value representing the amount of cash to add
        """
        self.cash += float(amount)
        self.total_contributions += float(amount)

    def buy(self, ticker, amount, price, commission):
        """Adds a holding to the portfolio in the form of a buy.

        Args:
            ticker: A string for the ticker of the holding to add
            amount: A value for the number of shares to buy
            price: A value corresponding to the price of each share
            commission: A value corresponding to the cost of the trade
        """
        if float(amount) * float(price) > self.cash:
            print("NOT ENOUGH CASH TO BUY " + ticker)
            return 1
        try:
            self.holdings[ticker.upper()] += int(amount)
        except KeyError:
            self.holdings[ticker.upper()] = int(amount)
        self.holdings_values[ticker.upper()] = \
            self.holdings[ticker.upper()] * float(price)
        self.cash -= int(amount) * float(price) - float(commission)
        return 0

    def sell(self, ticker, amount, price, commission):
        """Removes a holding from the portfolio in the form of a sell.

        Args:
            ticker: A string for the ticker of the holding to remove
            amount: A value for the number of shares to sell
            price: A value corresponding to the price of each share
            commission: A value corresponding to the cost of the trade
        """
        try:
            self.holdings[ticker.upper()] -= int(amount)
        except KeyError:
            self.holdings[ticker.upper()] = -int(amount)
        self.holdings_values[ticker.upper()] = \
            self.holdings[ticker.upper()] * float(price)
        self.cash += int(amount) * float(price) - float(commission)
        return 0

    def short(self, ticker, amount, price, commission):
        """Adds a holding to the portfolio in the form of a short, i.e.
        negative shares.

        Shorting is significantly more involved and contingent on more
        variables, so this feature is experimental and not complete.
        Currently not used in main program, but still referenced.

        Args:
            ticker: A string for the ticker of the holding to short
            amount: A value for the number of shares to sell
            price: A value corresponding to the price of each share
            commission: A value corresponding to the cost of the trade
        """
        self.sell(ticker, amount, price, commission)

    def cover(self, ticker, amount, price, commission):
        """Removes a holding from the portfolio in the form of a cover
        i.e. removes existing negative shares.

        Shorting is significantly more involved and contingent on more
        variables, so this feature is experimental and not complete.
        Currently not used in main program, but still referenced.

        Args:
            ticker: A string for the ticker of the holding to cover
            amount: A value for the number of shares to sell
            price: A value corresponding to the price of each share
            commission: A value corresponding to the cost of the trade
        """
        self.buy(ticker, amount, price, commission)

    def update_holdings_values(self, tickers, new_prices):
        """Updates the values of all the holdings based on a new set of
        provided prices.

        Args:
            tickers: An array of tickers for which to update values
            prices: An array of prices to use to calculate new values
        """
        for i in range(0, len(tickers)):
            self.holdings_values[tickers[i].upper()] = float(
                new_prices[i]) * int(self.holdings[tickers[i].upper()])

    def value(self):
        """Returns the total value of this Portfolio (cash + holdings).

        Returns:
            A value correspondingto the total value of this Portfolio
        """
        return self.cash + sum(self.holdings_values.values())

    def shares_of(self, ticker):
        """Returns the number of shares this portfolio is holding of a
        given ticker."""
        try:
            shares = self.holdings[ticker.upper()]
        except KeyError:
            shares = 0
        return shares
