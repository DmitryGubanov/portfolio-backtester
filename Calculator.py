import time

from utils import SteppedAvgLookup
from DataManager import DataManager


class Calculator(object):

    """A Calculator specifically designed to do stock market related
    calculations on stock data.

    For example, indicator data series can be calculated here for
    charting purposes.

    NOTE: To add an indicator, write two getter methods, one for a
        dictionary and another for a series, named
        'get_<indicator-name>' and 'get_<indicator-name>_series'. Then,
        in the get_indicator method, add the two methods to the correct
        mapping. Currently indicator getter functions need at least one
        argument, even if a None will be passed.

    Currently supports:
        - Standard Moving Average for a given period
        - Exponential Moving Average for a given period
        - Moving Average Convergence/Divergence for a given set of
            periods
        - generating theoretical ETF data
        - Previous High (i.e. the highest price the stock has been,
            including the current day)
    """

    def __init__(self):
        """Initializes a Calculator."""

    def get_indicator(self, indicator_code, price_lut, series=False):
        """A mapping function for indicator functions. Primarily used
        for cases where indicators are dynamic and hardcoding functions
        is impractical.

        Args:
            indicator_code: A string coding the indicator and period
            price_lut: A price lookup table for the data on which the
                indicator should be applied
            series: A value for whether or not to map to a series
                indicator function

        Returns:
            A dictionary mapping dates to indicator values
        """
        # decode
        code_parts = indicator_code.split('_')
        indicator = code_parts[0]
        if len(code_parts) == 1:
            period = None
        else:
            period = code_parts[1].split('-')
            if len(period) == 1:
                period = period[0]
        # create mapping to methods
        if series:
            mapping = {
                'SMA': self.get_sma_series,
                'EMA': self.get_ema_series,
                'MACD': self.get_macd_series,
                'MACDSIGNAL': self.get_macd_series,
                'PREVHIGH': self.get_prev_high_series
            }
        else:
            mapping = {
                'SMA': self.get_sma,
                'EMA': self.get_ema,
                'MACD': self.get_macd,
                'MACDSIGNAL': self.get_macd_signal,
                'PREVHIGH': self.get_prev_high
            }
        # call correct method
        return mapping[indicator](period, price_lut)

    def get_sma(self, period, price_lut):
        """Calculates the Standard Moving Average for a given period
        and returns a dictionary of SMA values.

        Args:
            period: A value representing a number of days
            price_lut: A price LUT, i.e. a dictionary mapping dates to
                prices

        Returns:
            A dictionary with dates mapping to SMA values
        """
        sma = {}
        period = int(period)
        dates = sorted(price_lut.keys())
        prices = []  # keep track of all prices as we go, for performance
        for i, date in enumerate(dates):
            prices.append(price_lut[date])
            if i < period:
                sma[date] = sum(prices) / len(prices)
            else:
                sma[date] = sum(prices[-period:]) / period
        return sma

    def get_sma_series(self, period, price_lut):
        """Calculates the Standard Moving Average for a given period
        and returns a list of SMA values.

        Args:
            period: A value representing a number of days
            price_lut: A price LUT, i.e. a dictionary mapping dates to
                prices

        Returns:
            A list with SMA values corresponding to ordered dates in
            the provided price LUT
        """
        sma = []
        period = int(period)
        dates = sorted(price_lut.keys())
        prices = []  # keep track of all prices as we go, for performance
        for i, date in enumerate(dates):
            prices.append(price_lut[date])
            if i < period:
                sma.append(sum(prices) / len(prices))
            else:
                sma.append(sum(prices[-period:]) / period)
        return sma

    def get_ema(self, period, price_lut):
        """Calculates the Exponential Moving Average for a given
        period and returns a dictionary of EMA values.

        Args:
            period: A value representing a number of days
            price_lut: A price LUT, i.e. a dictionary mapping dates to
                prices

        Returns:
            A dictionary with dates mapping to EMA values
        """
        ema = {}
        period = int(period)
        dates = sorted(price_lut.keys())
        ema = self.get_sma(period, {d: price_lut[d] for d in dates[0:period]})
        multiplier = 2 / (period + 1)  # used in EMA calulations
        for i, date in enumerate(dates[period:]):
            ema[date] = (float(price_lut[date]) * multiplier
                         + ema[dates[period + i - 1]] * (1 - multiplier))
        return ema

    def get_ema_series(self, period, price_lut):
        """Calculates the Exponential Moving Average for a given
        period and returns a list of EMA values.

        Args:
            period: A value representing a number of days
            price_lut: A price LUT, i.e. a dictionary mapping dates to
                prices

        Returns:
            A list with EMA values corresponding to the ordered dates
            in the provided price LUT
        """
        ema = []
        period = int(period)
        dates = sorted(price_lut.keys())
        ema = self.get_sma_series(period,
                                  {d: price_lut[d] for d in dates[0:period]})
        multiplier = 2 / (period + 1)  # used in EMA calulations
        for i, date in enumerate(dates[period:]):
            ema.append(float(price_lut[date]) * multiplier
                       + ema[-1] * (1 - multiplier))
        return ema

    def get_macd(self, periods, price_lut):
        """Calculates the Moving Average Convergence/Divergence for a
        given period and returns a dictionary mapping dates to MACD.

        Args:
            period: A set of values representing the days for each
                MACD period, i.e. [short, long, exponential/signal]
            price_lut: A set of values on which to perform the MACD
                calculations

        Returns:
            A dictionary mapping dates to MACD values
        """
        # ret = {}
        macd = {}
        # signal = {}
        # histogram = {}
        dates = sorted(price_lut.keys())
        macd_short = self.get_ema(periods[0], price_lut)
        macd_long = self.get_ema(periods[1], price_lut)
        # calculate MACD first - needed for signal and histogram
        for date in dates:
            macd[date] = macd_short[date] - macd_long[date]
        return macd
        # calculate signal - needed for histogram
        # signal = self.get_ema(periods[2], macd)
        # # calculate histogram
        # for date in dates:
        #     histogram[date] = macd[date] - signal[date]
        # # now convert everything to return format
        # for date in dates:
        #     ret[date] = [macd[date], signal[date], histogram[date]]
        # return ret

    def get_macd_signal(self, periods, price_lut):
        """Calculates the signal line for the Moving Average
        Convergence/Divergence for a given set of periods and returns a
        dictionary mapping dates to signal line values.

        Args:
            period: A set of values representing the days for each
                MACD period, i.e. [short, long, exponential/signal]
            price_lut: A set of values on which to perform the MACD
                calculations

        Returns:
            A dictionary mapping dates to MACD signal values
        """
        macd = {}
        dates = sorted(price_lut.keys())
        macd_short = self.get_ema(periods[0], price_lut)
        macd_long = self.get_ema(periods[1], price_lut)
        # calculate MACD first - needed for signal
        for date in dates:
            macd[date] = macd_short[date] - macd_long[date]
        return self.get_ema(periods[2], macd)

    def get_macd_series(self, periods, price_lut):
        """Calculates the Moving Average Convergence/Divergence for a
        given period and returns lists for MACD, signal, and histogram.

        Args:
            period: A set of values representing the days for each
                MACD period
            price_lut: A set of values on which to perform the MACD
                calculations

        Returns:
            A set of sets of values for the MACD, signal line, and MACD
            histogram at each point for the given values, i.e. a set in
            the form [[MACD], [signal line], [MACD histogram]]
        """
        macd = {}
        signal = []
        histogram = []
        dates = sorted(price_lut.keys())
        macd_short = self.get_ema(periods[0], price_lut)
        macd_long = self.get_ema(periods[1], price_lut)
        # calculate MACD first - needed for signal and histogram
        for date in dates:
            macd[date] = macd_short[date] - macd_long[date]
        # calculate signal - needed for histogram
        signal = self.get_ema_series(periods[2], macd)
        # calculate histogram
        for i, date in enumerate(dates):
            histogram.append(macd[date] - signal[i])
        return [[macd[d] for d in dates], signal, histogram]

    def get_prev_high(self, period, price_lut):
        """Calculates the previous high value for every point in the
        given LUT.

        Args:
            period: A placeholder, just pass None for now
            price_lut: A set f values on which to perform the previous
                high calculation
        Returns:
            A dictionary of dates mapping to values
        """
        prev_high = {}
        dates = sorted(price_lut.keys())
        prev_high[dates[0]] = price_lut[dates[0]]
        for i, date in enumerate(dates[1:]):
            prev_high[date] = max(price_lut[date], prev_high[dates[i]])
        return prev_high

    def get_prev_high_series(self, period, price_lut):
        """Calculates the previous high value for every point in the
        given LUT.

        Args:
            period: A placeholder, just pass None for now
            price_lut: A set f values on which to perform the previous
                high calculation
        Returns:
            A dictionary of dates mapping to values
        """
        prev_high = []
        dates = sorted(price_lut.keys())
        prev_high.append(price_lut[dates[0]])
        for date in dates[1:]:
            prev_high.append(max(price_lut[date], prev_high[-1]))
        return prev_high

    def generate_theoretical_data(self, ticker_tgt, ticker_src,
                                  step=0.00005, pos_adj=None, neg_adj=None):
        """Generates theoretical data for a stock based on another
        stock.

        Given two tickers, a granularity/precision step, and manual
        offset/adjustments, generates more data for the first stock
        (gen) to match the length of data in the second stock (src).
        The generation is based on averages in existing real data and
        assumes an existing correlation between two stocks (e.g. UPRO
        and SPY supposedly have a correlation, or leverage factor of 3)

        Args:
            ticker_tgt: A ticker of the stock for which data should be
                generated, i.e. the target for the generation
            ticker_src: A ticker of the stock to be used as the data
                source to aid in data generation.
                NOTE: This implies the source data should be longer
                than the data for the stock for which the generation
                occurs
            step: A value corresponding to a level of precision, or the
                number of averages calculated and then used to generate
                the data. NOTE: precision != accuracy and a default
                value of 0.00005 is used if one is not given, based on
                testing done on different values
            pos_adj: A value to be used when adjusting movements in the
                positive direction, i.e. a higher value will lead to
                more pronounced positive moves (default: None, if None
                a hardcoded default value will be used depending on
                the ticker, typically 0)
            neg_adj: A value to be used when adjusting movements in the
                negative direction, i.e. a higher value will lead to
                more pronounced negative moves (default: None, if None
                a hardcoded default value will be used depending on
                the ticker, typically 0)

        Returns:
            A tuple of price LUTs, one LUT containing real data
            appended to a part of the generated data, the other
            containing a full set of generated data. The former is
            intended to be used in backtesting strategies, while the
            latter is intended to be used for verifying generation
            accuracy against existing real data.
        """
        db = DataManager()
        # get prices for tickers
        price_lut_tgt = db.build_price_lut(ticker_tgt)
        price_lut_src = db.build_price_lut(ticker_src)
        # before doing any calculations, check if all data is on disk already
        price_lut_gen_part = db.build_price_lut(ticker_tgt + '--GEN-PART')
        price_lut_gen_full = db.build_price_lut(ticker_tgt + '--GEN-FULL')
        if (len(price_lut_gen_part) == len(price_lut_src)
                and len(price_lut_gen_full) == len(price_lut_src)):
            return (price_lut_gen_part, price_lut_gen_full)
        # sorted dates needed later
        src_dates = sorted(price_lut_src.keys())
        gen_dates = sorted(price_lut_tgt.keys())
        # part of data will be real data
        price_lut_gen_part = price_lut_tgt.copy()
        # fully generated data needs a real point as an anchor
        price_lut_gen_full = {gen_dates[0]: price_lut_tgt[gen_dates[0]]}
        # a set of adjustments to use if not otherwise specified
        adjustments = {
            'UPRO': (0, 0),
            'TMF': (0.01, 0.05)
        }
        if step == 0.00005 and pos_adj is None and neg_adj is None:
            try:
                pos_adj = adjustments[ticker_tgt.upper()][0]
                neg_adj = adjustments[ticker_tgt.upper()][1]
            except KeyError:
                pos_adj = 0
                neg_adj = 0
        # calculate % movements and leverage ratio, to use for the SA-LUT
        moves = {}
        ratios = {}
        for i in range(len(gen_dates) - 1):
            change_src = (price_lut_src[gen_dates[i + 1]]
                          / price_lut_src[gen_dates[i]]
                          - 1)
            change_gen = (price_lut_tgt[gen_dates[i + 1]]
                          / price_lut_tgt[gen_dates[i]]
                          - 1)
            moves[gen_dates[i + 1]] = change_src
            if change_src == 0:
                ratios[gen_dates[i + 1]] = 0.0
            else:
                ratios[gen_dates[i + 1]] = change_gen / change_src
        sa_lut = SteppedAvgLookup(step,
                                  [moves[d] for d in gen_dates[1:]],
                                  [ratios[d] for d in gen_dates[1:]])
        # generate data going forward from gen data's anchor point
        for i in range(len(gen_dates) - 1):
            move = moves[gen_dates[i + 1]]
            if move >= 0:
                adj = pos_adj
            else:
                adj = neg_adj
            price_lut_gen_full[gen_dates[i + 1]] = \
                (price_lut_gen_full[gen_dates[i]]
                 * (move * (sa_lut.get(move) + adj) + 1))
        # generate data going backwards from gen data's anchor point
        for i in range(len(src_dates) - len(gen_dates) - 1, -1, -1):
            move = (price_lut_src[src_dates[i + 1]]
                    / price_lut_src[src_dates[i]]
                    - 1)
            if move >= 0:
                adj = pos_adj
            else:
                adj = neg_adj
            gen_price = (price_lut_gen_full[src_dates[i + 1]]
                         / (move * (sa_lut.get(move) + adj) + 1))
            price_lut_gen_full[src_dates[i]] = gen_price
            price_lut_gen_part[src_dates[i]] = gen_price
        # save data to disk for faster retrieval next time
        db.write_stock_data(ticker_tgt + '--GEN-FULL',
                            [[date,
                              '-',
                              '-',
                              '-',
                              str(price_lut_gen_full[date]),
                              '-'] for date in src_dates],
                            False)
        db.write_stock_data(ticker_tgt + '--GEN-PART',
                            [[date,
                              '-',
                              '-',
                              '-',
                              str(price_lut_gen_part[date]),
                              '-'] for date in src_dates],
                            False)
        return (price_lut_gen_part, price_lut_gen_full)
