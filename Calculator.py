class Calculator(object):

    """A Calculator specifically designed to do stock market
    calculations.

    For example, indicator-related calculations are done here.

    Currently supports:
        - Standard Moving Average for a given period
        - Exponential Moving Average for a given period
        - Moving Average Convergence/Divergence for a given set of
            periods
        - generating theoretical ETF data
        - calculating the max drawdown given a set of portfolio values
    """

    def __init__(self):
        """Initializes a Calculator."""

    def get_sma(self, period, values):
        """Calculates the Standard Moving Average for a given period.

        Args:
            period: A value representing a number of days
            values: A set of values on which to perform the SMA
                calculations

        Returns:
            A set of values for the SMA at each point for the given
            values
        """
        return []

    def get_ema(self, period, values):
        """Calculates the Exponential Moving Average for a given
        period.

        Args:
            period: A value representing a number of days
            values: A set of values on which to perform the EMA
                calculations

        Returns:
            A set of values for the EMA at each point for the given
            values
        """
        return []

    def get_macd(self, periods, values):
        """Calculates the Moving Average Convergence/Divergence for a
        given period.

        Args:
            period: A set of values representing the days for each
                MACD period
            values: A set of values on which to perform the MACD
                calculations

        Returns:
            A set of sets of values for the MACD, signal line, and MACD
            histogram at each point for the given values, i.e. a set in
            the form [[MACD], [signal line], [MACD histogram]]
        """
        return []

    def generate_theoretical_data(self, ticker_a, ticker_b, step=0.00005,
                                  pos_adj, neg_adj):
        """Generates theoretical data for a stock based on another
        stock.

        Given two tickers, a granularity/precision step, and manual
        offset/adjustments, generates more data for the first ticker
        (ticker_a) to match the length of data in the second ticker
        (ticker_b). The generation is based on averages in existing
        real data and assumes an existing correlation between two
        tickers (e.g. UPRO and SPY)

        Args:
            ticker_a: A ticker for which to generate data
            ticker_b: A ticker to use as a reference when generating
                data for ticker_a
            step: A value corresponding to a level of precision, or the
                number of averages calculated and then used to generate
                the data. NOTE: precision != accuracy and a default
                value of 0.00005 is used if one is not given, based on
                testing done on different values
            pos_adj: A value to be used when adjusting movements in the
                positive direction, i.e. a higher value will lead to
                more pronounced positive moves (default: 0)
            neg_adj: A value to be used when adjusting movements in the
                negative direction, i.e. a higher value will lead to
                more pronounced negative moves (default: 0)

        Returns:
            A price LUT containing the existing data for ticker_a
            appended to the generated data for ticker_a
        """
        # a set of adjustments to use if not otherwise specified
        adjustments = {
            'UPRO': (0, 0),
            'TMF': (0.01, 0.05)
        }
        if step == 0.00005 and pos_adj is None and neg_adj is None:
            pos_adj = adjustments[ticker_a.upper()][0]
            neg_adj = adjustments[ticker_a.upper()][1]
        return {}

    def get_max_drawdown(self, values):
        """Calculates the max drawdown for a given set of values.

        Args:
            values: A set of portfolio values

        Returns:
            A tuple in the form (drawdown, from, to, recovered by),
            where the drawdown is a % value and from, to, and
            recovered by are date strings
        """
        return (0, '', '', '')
