import operator as op


class Brain(object):

    """A Brain for a Trader. Decisions regarding Portfolio allocations
    are made here.

    In other words, a Trader will 'use' their Brain to decide how much
    of each asset they should have in their Portfolio

    Attributes:
    """

    def __init__(self):
        """Initializes an empty Brain."""
        self._market = None
        self._portfolio = None
        self.assets_of_interest = set({})
        self.positions = []
        self.assets_to_trade = set({})
        self.rebalancing_period = None
        self.strategy_type = None
        self.desired_ratios = {}
        self.desired_shares = {}

    def use_market(self, market):
        """Sets the Market this Brain should use to make decisions."""
        self._market = market

    def use_portfolio(self, portfolio):
        """Sets the Portfolio this Brain should use to make decisions."""
        self._portfolio = portfolio

    def set_strategy(self, strategy):
        """NEEDS DESC WHEN MORE IMPLEMENTED

        Args:
            strategy: A keyword specifying which strategy to use."""
        self.positions = strategy

    def set_rebalancing_period(self, period):
        """Sets the rebalancing frequency. The Brain will adjust the
        shares of all assets at each period to match ratios.

        Args:
            period: A value representing the frequency of rebalancing
                e.g. 'm' for monthly
        """
        self.rebalancing_period = period

    def decide_needed_shares(self):
        """Calculates the amount of shares needed of each desired
        asset."""
        self.decide_asset_ratios()
        for asset in list(self.assets_to_trade):
            self.desired_shares[asset] = int(self._portfolio.value()
                                             * self.desired_ratios[asset]
                                             / self._market.query_stock(asset))
            self.assets_to_trade.remove(asset)

    def decide_asset_ratios(self):
        """Calculates the ratios for each desired asset.

        Specifically, checks buy and sell signals and updates which
        assets should be traded. Also handles trading all assets if a
        rebalance is needed."""
        for position in self.positions:
            if (position['is_holding']
                    and self._check_signal(position['sell_signal'])):
                position['is_holding'] = False
                self.assets_to_trade.add(position['ticker'])
                try:
                    self.desired_ratios[position['ticker']] \
                        -= position['ratio']
                except KeyError:
                    print("ERR: reducing ratio for {}".format(
                        position['ticker']))
                    self.desired_ratios[position['ticker']] = 0
            elif (not position['is_holding']
                  and self._check_signal(position['buy_signal'])):
                position['is_holding'] = True
                self.assets_to_trade.add(position['ticker'])
                try:
                    self.desired_ratios[position['ticker']] \
                        += position['ratio']
                except KeyError:
                    self.desired_ratios[position['ticker']] = position['ratio']
            elif (self.rebalancing_period
                  and self._market.new_period[self.rebalancing_period]):
                self.assets_to_trade.add(position['ticker'])

    def _check_signal(self, signal_code):
        """Given a (buy or sell) signal code, interprets it and checks
        whether or not the signal is satisfied by the market.

        Currently, buy and sell signals come in 'VALUE COMPARE VALUE'
        format, where COMPARE is an operator value and VALUE is a code
        for a value in the market (e.g. 'UPRO~SMA_200' for UPRO's
        Standard Moving Average 200 value).

        Args:
            signal_code: A code for the buy or sell signal

        Returns:
            A value for whether or not the signal is satisfied
        """
        if signal_code == 'ALWAYS':
            return True
        if signal_code == 'NEVER':
            return False
        compare_using = {
            '>': op.gt,
            '<': op.lt
        }
        (value_a_code, operator, value_b_code) = signal_code.split(' ')
        return compare_using[operator](self._decode_and_get_value(value_a_code),
                                       self._decode_and_get_value(value_b_code))

    def _decode_and_get_value(self, value_code):
        """Decodes a value code and returns the appropriate value.

        Args:
            value_code: A code for a value in the Market

        Returns:
            A value corresponding to the coding
        """
        (ticker, indicator_code) = value_code.split('~')
        if indicator_code == 'PRICE':
            return self._market.query_stock(ticker)
        return self._market.query_stock_indicator(ticker, indicator_code)
