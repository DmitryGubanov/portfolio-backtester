###
# A Portfolio with cash, assets (definition of stocks to be held), and holdings (stocks
# actually held). This portfolio shouldn't do anything on its own and just functions
# as a container for another class/program to manage
##
class Portfolio:

    ##
    # initializes an empty portfolio
    def __init__(self, cash=0):
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

    ##
    # adds an asset to the portfolio which is a desired holding under certain conditions
    # NOTE asset types: 'long' & 'short'
    def add_asset(self, ticker, portion, asset_type):
        self.assets[ticker.upper()] = float(portion)
        self.assets_types[ticker.upper()] = asset_type
        self.holdings[ticker.upper()] = 0
        self.holdings_values[ticker.upper()] = float(0)

    # TODO: market as singleton eventually, so change to query market here for commission and price

    ##
    # adds a holding to the portfolio in the form of a buy
    def buy(self, ticker, amount, price, commission):
        """Adds a holding to the portfolio in the form of a buy.

        Args:
            ticker: A string for the ticker of the holding to add
            amount: A value corresponding to the number of shares to buy
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
        self.holdings_values[ticker.upper()] = self.holdings[ticker.upper()] * float(price)
        self.cash -= int(amount) * float(price) - float(commission)
        return 0

    ##
    # removes a holding to the portfolio in the form of a sell
    def sell(self, ticker, amount, price, commission):
        try:
            self.holdings[ticker.upper()] -= int(amount)
        except KeyError:
            self.holdings[ticker.upper()] = -int(amount)
        self.holdings_values[ticker.upper()] = self.holdings[ticker.upper()] * float(price)
        self.cash += int(amount) * float(price) - float(commission)
        return 0

    ##
    # adds a holding to the portfolio in the form of a short (negative shares)
    def short(self, ticker, amount, price, commission):
        self.sell(ticker, amount, price, commission)

    ##
    # removes a holding to the portfolio in the form of a cover
    def cover(self, ticker, amount, price, commission):
        self.buy(ticker, amount, price, commission)

    ##
    # updates the values of all the holdings to a new set of values
    def update_holdings_values(self, tickers, new_prices):
        for i in range(0, len(tickers)):
            self.holdings_values[tickers[i].upper()] = float(
                new_prices[i]) * int(self.holdings[tickers[i].upper()])

    ##
    # the total value of this portfolio (cash + assets)
    def value(self):
        return self.cash + sum(self.holdings_values.values())

    def shares_of(self, ticker):
        """Returns the number of shares this portfolio is holding of a given ticker."""
        try:
            shares = self.holdings[ticker.upper()]
        except KeyError:
            shares = 0
        return shares
