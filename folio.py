#!/usr/bin/python

import argparse
import urllib
import os
import os.path
import matplotlib.pyplot as pyplot
import matplotlib.dates as mdates
import datetime
from datetime import datetime as dt
import calendar
import time

from Downloader import Downloader
from DataManager import DataManager
from Market import Market
from Portfolio import Portfolio
from Simulator import Simulator
from Monitor import Monitor
from Trader import Trader
from Calculator import Calculator
from utils import *

##############################################################################
# MAIN
##############################################################################


def main():
    args = parser.parse_args()

    if args.draw:
        # parse arguments and collect data
        # price history
        if args.use_generated:
            gen = args.use_generated[0]
            src = args.use_generated[1]
            (data, _) = calc.generate_theoretical_data(gen, src)
        else:
            data = db.build_price_lut(args.draw[0])
        dates = [date_obj(date) for date in sorted(data.keys())]
        prices = [data[date_str(date)] for date in dates]
        # indicators and plot counts
        if not args.indicators:
            args.indicators = []
        plots = 1
        indicators = {}
        for indicator_code in args.indicators:
            (indicator, _) = indicator_code.split('_')
            if indicator == 'MACD':
                plots = 2
            indicators[indicator_code] = calc.get_indicator(indicator_code,
                                                            data, True)

        # plot main price data
        pyplot.subplot(plots * 100 + 11)
        pyplot.plot(dates, prices, label='{} price'.format(args.draw[0]))
        pyplot.legend(loc='upper left')

        # plot indicators
        for (indicator_code, series) in indicators.items():
            (indicator, period_code) = indicator_code.split('_')
            if indicator == 'MACD':
                pyplot.subplot(plots * 100 + 12)
                pyplot.plot(dates, series[0], label=indicator_code)
                pyplot.plot(dates, series[1],
                            label='Signal_{}'.format(period_code))
                pyplot.legend(loc='upper left')
            else:
                pyplot.subplot(plots * 100 + 11)
                pyplot.plot(dates, series, label=indicator_code)
                pyplot.legend(loc='upper left')

        pyplot.show()

    if args.generate:
        (part, full) = calc.generate_theoretical_data(args.generate[0],
                                                      args.generate[1])
        tgt_lut = db.build_price_lut(args.generate[0])
        src_lut = db.build_price_lut(args.generate[1])
        tgt_dates = [date_obj(d) for d in sorted(tgt_lut.keys())]
        src_dates = [date_obj(d) for d in sorted(part.keys())]
        tgt_gen_part_prices = [part[date_str(d)] for d in src_dates]
        tgt_gen_full_prices = [full[date_str(d)] for d in src_dates]
        src_prices = [src_lut[date_str(d)] for d in src_dates]

        pyplot.subplot(211)
        pyplot.plot([date_obj(d) for d in tgt_dates],
                    tgt_gen_full_prices[-len(tgt_dates):],
                    label='UPRO-generated')
        pyplot.plot([date_obj(d) for d in tgt_dates],
                    tgt_gen_part_prices[-len(tgt_dates):],
                    label='UPRO')
        pyplot.legend(loc='upper left')

        pyplot.subplot(212)
        pyplot.plot(src_dates, tgt_gen_part_prices, label='UPRO-generated')
        pyplot.plot(src_dates, src_prices, label='SPY')
        pyplot.legend(loc='upper left')

        pyplot.show()

    if args.portfolio:
        # init main objects
        my_market = Market()
        my_trader = Trader()
        my_portfolio = Portfolio()
        my_trader.portfolio = my_portfolio
        my_trader.set_starting_cash(args.portfolio[0])

        # init simulator
        my_monitor = Monitor(my_trader.portfolio, my_market)
        my_sim = Simulator()
        my_sim.add_trader(my_trader)
        my_sim.use_market(my_market)
        my_sim.use_monitor(my_monitor)

        # parse args
        if args.use_generated:
            for i in range(0, len(args.use_generated) // 2):
                ticker_a = args.use_generated[i * 2]
                ticker_b = args.use_generated[i * 2 + 1]
                (data, _) = calc.generate_theoretical_data(ticker_a, ticker_b)
                my_market.inject_stock_data(ticker_a, None, None, data)
        for i in range(0, len(args.portfolio[6:]) // 3):
            my_trader.add_asset_of_interest(args.portfolio[i * 3 + 6])
            my_trader.set_desired_asset_ratio(args.portfolio[i * 3 + 6],
                                              float(args.portfolio[i * 3 + 7]))
        if args.portfolio[2] != "None" and args.portfolio[1] != "None":
            my_trader.set_strategy('contributions',
                                   [args.portfolio[2], args.portfolio[1]])
        if args.portfolio[3] != "None":
            my_trader.set_strategy('rebalancing', [args.portfolio[3]])
        if args.portfolio[4]:
            my_sim.set_start_date(args.portfolio[4])
        if args.portfolio[5]:
            my_sim.set_end_date(args.portfolio[5])

        # run simulation
        my_sim.simulate()

        # print some stats
        print('##################################')
        print('# PERFORMANCE SUMMARY')
        print('##################################')
        print('initial: $' + currency(my_trader.starting_cash))
        print('final:   $' + currency(my_trader.portfolio.value()))
        print('---------------------------')
        print('CAGR:          {}%'.format(
            percent(my_monitor.get_statistic('cagr'))))
        print('Adjusted CAGR: {}%'.format(
            percent(my_monitor.get_statistic('adjusted_cagr'))))
        print('---------------------------')
        print('best year:  {}%'.format(
            percent(max(my_monitor.get_data_series('annual_returns')[1]))))
        print('worst year: {}%'.format(
            percent(min(my_monitor.get_data_series('annual_returns')[1]))))
        print('---------------------------')
        drawdown = my_monitor.get_statistic('max_drawdown')
        print('max drawdown: {}%'.format(percent(drawdown['amount'])))
        print('  between {} and {}, recovered by {}'.format(
            drawdown['from'], drawdown['to'], drawdown['recovered_by']))

        # show plots
        (x, y) = my_monitor.get_data_series('portfolio_values')
        pyplot.subplot(411)
        pyplot.plot(x, y)
        pyplot.grid(b=False, which='major', color='grey', linestyle='-')

        (x, y) = my_monitor.get_data_series('asset_allocations')
        pyplot.subplot(412)
        pyplot.stackplot(x, y, alpha=0.5)
        pyplot.grid(b=True, which='major', color='grey', linestyle='-')
        pyplot.legend(sorted(my_trader.assets_of_interest), loc='upper left')

        (x, y) = my_monitor.get_data_series('annual_returns')
        ax = pyplot.subplot(413)
        pyplot.bar(list(range(len(x))), y, 0.5, color='blue')
        ax.set_xticks(list(range(len(x))))
        ax.set_xticklabels(x)
        pyplot.grid(b=True, which='major', color='grey', linestyle='-')

        (x, y) = my_monitor.get_data_series('contribution_vs_growth')
        pyplot.subplot(414)
        pyplot.stackplot(x, y, alpha=0.5)
        pyplot.grid(b=True, which='major', color='grey', linestyle='-')
        pyplot.legend(['Contributions', 'Growth'], loc='upper left')

        pyplot.show()

    exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Stock program (WIP).')
    parser.add_argument('--generate', nargs=2)
    parser.add_argument('--portfolio', nargs='+')
    parser.add_argument('--use-generated', nargs='+')
    parser.add_argument('--draw', nargs=1)
    parser.add_argument('--indicators', nargs='+')

    db = DataManager()
    calc = Calculator()

    main()
