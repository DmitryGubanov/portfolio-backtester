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
    # TODO: HUGE: this whole main is sort of a disaster of hacked together statements that I wrote whenever I wanted to output something. Will replace this whole thing completely when I start the interface part of this project
    args = parser.parse_args()

    # NOTE testing SMA calcs
    # upro_lut = db.build_price_lut('UPRO')
    # price_series = [upro_lut[x] for x in sorted(upro_lut.keys())]
    # ema1_lut = calc.get_macd([12, 26, 9], upro_lut)
    #
    # ema1 = [ema1_lut[x] for x in sorted(ema1_lut.keys())]
    # ema2 = get_macd(price_series, [12, 26, 9])
    # ema3 = calc.get_macd_series([12, 26, 9], upro_lut)
    #
    # print('length: {} vs {}'.format(len(ema1), len(ema2)))
    # for i in range(len(ema1)):
    #     print('sma: {} vs {} vs {}, with URO at {}'.format(ema1[i], [ema2[0][i], ema2[1][i], ema2[2][i]], [ema3[0][i], ema3[1][i], ema3[2][i]], price_series[i]))

    if args.download != None:
        failed = download_stocks_data(args.download, True)
        if len(failed) == len(args.download):
            print("failed to download provided stock(s). exiting.")
        if len(failed) > 0:
            failed_stocks = ', '.join(failed)
            print("failed to download:\n" + failed_stocks)

    if args.download_using != None:
        failed = download_stocks_data(
            [line.strip() for line in readlines(args.download_using[0])], False)
        if len(failed) == len(args.download):
            print("failed to download provided stock(s). exiting.")
        if len(failed) > 0:
            failed_stocks = ', '.join(failed)
            print("failed to download:\n" + failed_stocks)

    if args.download_using_csv != None:
        failed = download_stocks_data(list_from_csv(
            args.download_using_csv[0], 0, ',', ['"']), False)
        if len(failed) == len(args.download):
            print("failed to download provided stock(s). exiting.")
        if len(failed) > 0:
            failed_stocks = ', '.join(failed)
            print("failed to download:\n" + failed_stocks)

    if args.best_stocks != None:
        stock_list = clean_stock_list(list_from_csv(
            args.best_stocks[2], 0, ',', ['"']), 1, 5)
        i = 0
        while i < len(stock_list):
            if not has_file(stock_list[i]):
                del stock_list[i]
            else:
                i += 1
        best_data = get_best(int(args.best_stocks[0]),
                             int(args.best_stocks[1][0:-1]),
                             args.best_stocks[1][-1],
                             stock_list)
        for tuple in best_data:
            print(tuple[0] + ":\t" + percent(tuple[1]) + '%')

    if args.generate != None:
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

    # if args.draw_chart != None:
    #     stock_data = read_csv_file_columns(filename(args.draw_chart[0]))
    #     if len(stock_data) == 0:
    #         print("no data. exiting.")
    #         exit()
    #     x = 0
    #     dates = []
    #     for i in range(0, len(stock_data[0])):
    #         dates.append(i)
    #     plots = 1
    #     if args.macd != None:
    #         plots = 2
    #     pyplot.subplot(plots * 100 + 11)
    #     pyplot.plot(dates[x:], stock_data[6][x:])
    #     if args.sma != None:
    #         for period in args.sma:
    #             sma_data = get_sma(stock_data[6], period)
    #             pyplot.plot(dates[x:], sma_data[x:], label='SMA ' + period)
    #     if args.ema != None:
    #         for period in args.ema:
    #             ema_data = get_ema(stock_data[6], period)
    #             pyplot.plot(dates[x:], ema_data[x:], label='EMA ' + period)
    #     pyplot.legend(loc='upper left')
    #     if args.macd != None:
    #         macd_data = get_macd(stock_data[6], args.macd)
    #         pyplot.subplot(212)
    #         pyplot.plot(dates[x:], macd_data[0][x:])
    #         pyplot.plot(dates[x:], macd_data[1][x:])
    #         pyplot.bar(dates[x:], macd_data[2][x:])
    #     pyplot.show()

    if args.portfolio != None:
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
        if args.use_generated != None:
            for i in range(0, len(args.use_generated) // 2):
                (data, _) = calc.generate_theoretical_data(
                    args.use_generated[i * 2], args.use_generated[i * 2 + 1])
                my_market.inject_stock_data(
                    args.use_generated[i * 2], None, None, data)
        for i in range(0, len(args.portfolio[6:]) // 3):
            my_trader.add_asset_of_interest(args.portfolio[i * 3 + 6])
            my_trader.set_desired_asset_ratio(args.portfolio[i * 3 + 6], float(args.portfolio[i * 3 + 7]))
        if args.portfolio[2] != "None" and args.portfolio[1] != "None":
            my_trader.set_strategy('contributions', [args.portfolio[2], args.portfolio[1]])
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
    parser.add_argument('--download', nargs='+')
    parser.add_argument('--download-using', nargs=1)
    parser.add_argument('--download-using-csv', nargs=1)
    parser.add_argument('--draw-chart', nargs=1)
    parser.add_argument('--sma', nargs='+')
    parser.add_argument('--ema', nargs='+')
    parser.add_argument('--macd', nargs=3)
    parser.add_argument('--best-stocks', nargs=3)
    parser.add_argument('--generate', nargs=2)
    parser.add_argument('--portfolio', nargs='+')
    parser.add_argument('--use-generated', nargs='+')

    db = DataManager()
    calc = Calculator()

    main()
