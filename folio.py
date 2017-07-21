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

from Downloader import Downloader
from DataManager import DataManager
from Market import Market
from Portfolio import Portfolio
from Simulator import Simulator
from Trader import Trader
from utils import *

##############################################################################
# ARGUMENT DEFINITIONS
##############################################################################

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

##############################################################################
# HELPERS
##############################################################################

##
# Calculate SMA for period at each value, given a list of values
def get_sma(values, period):
    period = int(period)
    sma = []
    sum = 0
    for i in range(0, period - 1):
        sum += float(values[i])
        sma.append(sum / (i + 1))
    for i in range(period - 1, len(values)):
        sum = 0
        for j in range(i, i - period, -1):
            sum += float(values[j])
        sma.append(sum / period)
    return sma

##
# Calculate EMA for period at each value, given a list of values
def get_ema(values, period):
    period = int(period)
    ema = get_sma(values[0:period], period)
    multiplier = 2 / (period + 1)
    for i in range(period, len(values)):
        ema.append(float(values[i]) * multiplier + ema[-1] * (1 - multiplier))
    return ema

##
# Calculate MACD/signal/histogram for period at each value, given list of values
def get_macd(values, periods):
    for i in range(0, len(periods)):
        periods[i] = int(periods[i])
    macd_a = get_ema(values, periods[0])
    macd_b = get_ema(values, periods[1])
    macd = []
    for i in range(0, len(values)):
        macd.append(macd_a[i] - macd_b[i])
    signal = get_ema(macd, periods[2])
    histogram = []
    for i in range(0, len(values)):
        histogram.append(macd[i] - signal[i])
    return [macd, signal, histogram]


# Download historical data for a list of stocks, given their tickers
# def download_stocks_data(ticker_list, quiet):
#   download_failed = []
#   for ticker in ticker_list:
#     if not quiet:
#       print('.', end='')
#     try:
#       urllib.request.urlretrieve(yahoo_url(ticker.strip()), filename(ticker.strip()))
#     except urllib.error.ContentTooShortError as e:
#       download_failed.append(ticker.strip())
#     except urllib.error.HTTPError as e:
#       download_failed.append(ticker.strip())
#   if not quiet:
#     print('')
#   return download_failed

##
# Calculates changes in price (%) over a certain period given a list of stocks
def get_growth(period, period_unit, tickers):
    changes = {}
    for i in range(0, len(tickers)):
        price_lookup = build_price_lut(tickers[i])
        dates = sorted(price_lookup.keys())
        target_date = dates[nearest_index(subtract_date(
            period, period_unit, dates[-1]), dates, 1, 'date')]
        changes[tickers[i]] = price_lookup[dates[-1]] / \
            price_lookup[target_date] - 1
    return changes
##
# Get the best performing stocks out of a list of stocks over a period
def get_best(number, period, period_unit, tickers):
    n = number
    if n > len(tickers):
        n = len(tickers)
    growth = get_growth(period, period_unit, stock_list)
    return sorted(growth.items(), key=lambda x: x[1], reverse=True)[0:n]

##
# Goes through a list of stocks and clears out all stocks that go below a certain price
# or have splits by a factor greater than the one provided
def clean_stock_list(tickers, min_price, max_split):
    cleaned_stocks = []
    for stock in tickers:
        if not has_file(stock):
            continue
        clean = True
        data = read_csv_file_rows(filename(stock))
        for i in range(0, len(data)):
            if float(data[i][4]) < min_price and float(data[i][6]) < min_price:
                clean = False
                break
            if i > 0 and (float(data[i][6]) > float(data[i - 1][6]) * max_split or
                          float(data[i][6]) < float(data[i - i][6]) / max_split):
                clean = False
                break
        if clean:
            cleaned_stocks.append(stock)
    return cleaned_stocks

##
# Compares two sets of prices and returns the amount each changed between each point
# and the ratio of change between the two
def compare_movement(data_a, data_b):
    changes_a = []
    changes_b = []
    ratios = []
    for i in range(min(len(data_a), len(data_b)), 1, -1):
        changes_a.append(float(data_a[-i + 1]) / float(data_a[-i]) - 1)
        changes_b.append(float(data_b[-i + 1]) / float(data_b[-i]) - 1)
        if changes_b[-1] == 0:
            ratios.append(0.0)
        else:
            ratios.append(changes_a[-1] / changes_b[-1])
    return [changes_a, changes_b, ratios]


##
# Given two tickers, a granularity/precision step, and manual offset/adjustments, and generates
# more data for the one with fewer data points to match the one with more. The generation is based on
# averages in existing real data and assumes an existing correlation between two tickers (e.g. UPRO and SPY)
def generate_theoretical_data(ticker_a, ticker_b, step, pos_adj, neg_adj):
    data_a = db._read_csv_file_columns_for(ticker_a)
    data_b = db._read_csv_file_columns_for(ticker_b)
    if len(data_a[0]) > len(data_b[0]):
        source_data = data_a
        target_data = data_b
    else:
        source_data = data_b
        target_data = data_a
    changes = compare_movement(target_data[4], source_data[4])
    lut = SteppedAvgLookup(step, changes[1], changes[2])
    generated_data = [float(target_data[4][0])]
    for i in range(source_data[0].index(target_data[0][0]), 0, -1):
        change = float(source_data[4][i]) / float(source_data[4][i - 1]) - 1
        if change >= 0:
            price = generated_data[0] / (change * (lut.get(change) + pos_adj) + 1)
        else:
            price = generated_data[0] / (change * (lut.get(change) + neg_adj) + 1)
        generated_data.insert(0, price)
    for i in range(source_data[0].index(target_data[0][0]) + 1, len(source_data[0])):
        change = float(source_data[4][i]) / float(source_data[4][i - 1]) - 1
        if change >= 0:
            price = generated_data[-1] * (change * (lut.get(change) + pos_adj) + 1)
        else:
            price = generated_data[-1] * (change * (lut.get(change) + neg_adj) + 1)
        generated_data.append(price)
    return [generated_data, source_data[0].index(target_data[0][0]), target_data, source_data, changes]


##############################################################################
# MAIN
##############################################################################

def main():
    # TODO: HUGE: this whole main is sort of a disaster of hacked together statements that I wrote whenever I wanted to output something. Will replace this whole thing completely when I start v3, i.e. the interface part of this project

    args = parser.parse_args()

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
        adjustments = {'UPRO': (0.0, 0.00), 'TMF': (0.01, 0.05)}
        adjustment = (0, 0)
        if args.generate[0] in adjustments.keys():
            adjustment = adjustments[args.generate[0]]
        [gen_prices, idx, etf, src, changes] = generate_theoretical_data(
            args.generate[0], args.generate[1], 0.00005, adjustment[0], adjustment[1])
        dates = [[], []]
        dates[0] = [dt.strptime(d, "%Y-%m-%d").date() for d in etf[0]]
        dates[1] = [dt.strptime(d, "%Y-%m-%d").date() for d in src[0]]
        pyplot.subplot(311)
        pyplot.plot(dates[0], etf[4], label=args.generate[0])
        pyplot.plot(dates[0], gen_prices[-len(etf[4]):],
                    label=args.generate[0] + '-generated')
        pyplot.legend(loc='upper left')
        pyplot.subplot(312)
        pyplot.plot(dates[1], src[4], label=args.generate[1])
        pyplot.plot(dates[1], gen_prices,
                    label=args.generate[0] + '-generated')
        pyplot.legend(loc='upper left')
        pyplot.subplot(313)
        pyplot.plot(changes[0], changes[2], '.')
        pyplot.show()

    if args.draw_chart != None:
        stock_data = read_csv_file_columns(filename(args.draw_chart[0]))
        if len(stock_data) == 0:
            print("no data. exiting.")
            exit()
        x = 0
        dates = []
        for i in range(0, len(stock_data[0])):
            dates.append(i)
        plots = 1
        if args.macd != None:
            plots = 2
        pyplot.subplot(plots * 100 + 11)
        pyplot.plot(dates[x:], stock_data[6][x:])
        if args.sma != None:
            for period in args.sma:
                sma_data = get_sma(stock_data[6], period)
                pyplot.plot(dates[x:], sma_data[x:], label='SMA ' + period)
        if args.ema != None:
            for period in args.ema:
                ema_data = get_ema(stock_data[6], period)
                pyplot.plot(dates[x:], ema_data[x:], label='EMA ' + period)
        pyplot.legend(loc='upper left')
        if args.macd != None:
            macd_data = get_macd(stock_data[6], args.macd)
            pyplot.subplot(212)
            pyplot.plot(dates[x:], macd_data[0][x:])
            pyplot.plot(dates[x:], macd_data[1][x:])
            pyplot.bar(dates[x:], macd_data[2][x:])
        pyplot.show()

    if args.portfolio != None:
        # init main objects
        my_market = Market()
        my_trader = Trader()
        my_portfolio = Portfolio()
        my_trader.portfolio = my_portfolio
        my_trader.set_starting_cash(args.portfolio[0])

        # init simulator
        my_sim = Simulator()
        my_sim.add_trader(my_trader)
        my_sim.use_market(my_market)

        # parse args
        if args.use_generated != None:
            adjustments = {'UPRO': (0.0, 0.00), 'TMF': (0.01, 0.05)}
            adjustment = (0, 0)
            for i in range(0, len(args.use_generated) // 2):
                adjustment = adjustments[args.use_generated[i * 2]]
                data = generate_theoretical_data(
                    args.use_generated[i * 2], args.use_generated[i * 2 + 1], 0.00005, adjustment[0], adjustment[1])
                my_market.inject_stock_data(
                    args.use_generated[i * 2], data[3][0], data[0])
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

        port_vals = []
        port_vals.append(my_trader.starting_cash)
        my_sim.simulate()
        port_vals.append(my_trader.portfolio.value())

        print('initial -> $' + currency(port_vals[0]))
        print('final ---> $' + currency(port_vals[1]))

#    for i in range(0, len(my_sim.trade_history[0])):
#      print(my_sim.trade_history[0][i] + ' : ' + my_sim.trade_history[1][i])

        (dates, y) = my_sim.stats[Simulator.stat_keys[0]]
        x = [dt.strptime(d, "%Y-%m-%d").date() for d in dates]

        years = (x[-1] - x[0]).days / 365.25
        print('CAGR ----> ' +
              percent((port_vals[1] / port_vals[0]) ** (1 / years) - 1) + '%')

        pyplot.subplot(411)
        pyplot.plot(x, y)
        pyplot.grid(b=True, which='major', color='grey', linestyle='-')

        (dates, ratios) = my_sim.stats[Simulator.stat_keys[1]]
        x = [dt.strptime(d, "%Y-%m-%d").date() for d in dates]
        y = [[ratio[i] for ratio in ratios] for i in range(0, len(ratios[0]))]
        legend = sorted(my_trader.assets_of_interest)

        #print(len(x))
        #print(len(y))
        pyplot.subplot(412)
        pyplot.stackplot(x, y, alpha=0.5)
        pyplot.grid(b=True, which='major', color='grey', linestyle='-')
        pyplot.legend(legend, loc='upper left')

        (dates, values, y) = my_sim.stats[Simulator.stat_keys[2]]
        x = [dt.strptime(d, "%Y").date() for d in dates]

        pyplot.subplot(413)
        pyplot.bar(x, y, 200, color="blue")
        pyplot.grid(b=True, which='major', color='grey', linestyle='-')

        print('---')
        print('best year ----> ' + percent(max(y)) + '%')
        print('worst year ---> ' + percent(min(y)) + '%')

        # figure out max drawdown, need from, to, recovered by
        (dates, values) = my_sim.stats[Simulator.stat_keys[0]]
        last_high = values[0]
        lowest_since = values[0]
        drawdown = 0
        potential_start = dates[0]
        potential_end = dates[0]
        for i in range(1, len(values)):
            if values[i] > last_high:
                last_high = values[i]
                if drawdown > (lowest_since / last_high - 1):
                    drawdown = lowest_since / last_high - 1
                    drawdown_start = potential_start
                    drawdown_end = potential_end
                    drawdown_recover = dates[i]
                lowest_since = values[i]
                potential_start = dates[i]
            else:
                if values[i] < lowest_since:
                    lowest_since = values[i]
                    potential_end = dates[i]

        print('max drawdown -> ' + percent(drawdown) + '%')
        print(' from ' + drawdown_start + ' to ' +
              drawdown_end + ' recovered by ' + drawdown_recover)

        # plot contributions vs growth

        (dates, values) = my_sim.stats[Simulator.stat_keys[3]]
        x = [date_obj(d).date() for d in dates]
        y = [[c / (c + g) for c, g in values], [g / (c + g)for c, g in values]]

        pyplot.subplot(414)
        pyplot.stackplot(x, y, alpha=0.5)
        pyplot.grid(b=True, which='major', color='grey', linestyle='-')
        pyplot.legend(['Contributions', 'Growth'], loc='upper left')

        # figure out total contributions, ratio of contributions:value, CAGR ignoring contributions
        print('---')
        print('total contributions: $' + currency(my_portfolio.total_contributions))
        print('total growth: $' + currency(my_portfolio.value() -
                                           my_portfolio.total_contributions - port_vals[0]))
        print('adjusted CAGR: ' + percent(((my_portfolio.value() -
                                            my_portfolio.total_contributions) / port_vals[0]) ** (1 / years) - 1) + '%')

        pyplot.show()

    exit()


if __name__ == "__main__":
    db = DataManager()
    main()
