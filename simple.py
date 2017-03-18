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

##############################################################################
# GLOBAL
##############################################################################

STOCK_DIR = "/home/gubanovd/stocks/"
DATE_FORMAT = "%Y-%m-%d"

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
# CLASSES
##############################################################################

class Market:

  def __init__(self, tickers, dates):
    self.new_period = {'m': False, 'q': False, 'y': False}
    self.stocks = {}
    if tickers != None:
      self.__build_stocks(tickers)
    self.dates = None
    if dates != None:
      self.dates = dates
      self.date = (0, self.dates[0])

  def add_stocks(self, tickers):
    self.__build_stocks(tickers)

  def inject_stock_data(self, ticker, dates, prices):
    price_lut = {}
    for i in range(0, len(dates)):
      price_lut[dates[i]] = prices[i]
    self.stocks[ticker.upper()] = price_lut

  def current_date(self):
    return self.date[1]

#  def open_dates(self):
#    return self.dates

  def query_stock(self, ticker):
    try:
      return float(self.stocks[ticker.upper()][self.date[1]])
    except KeyError:
      return self.__recursive_query_stock(ticker.upper(), self.date[0] - 1)

  def __recursive_query_stock(self, ticker, date_idx):
    if date_idx < 0:
      return 0
    try:
      return float(self.stocks[ticker][self.dates[date_idx]])
    except KeyError:
      return self.__recursive_query_stock(ticker, date_idx - 1)      

  def set_date(self, date):
    if date < self.dates[0]:
      self.date = (0, self.dates[0])
      return 0
    try:
      self.date = (self.dates.index(date), date)
      return 0
    except ValueError:
      return self.set_date(date_str(date_obj(date) + datetime.timedelta(1)))

  def set_default_dates(self):
    date_range = (date_str(dt.fromordinal(1)), date_str(dt.fromordinal(999999)))
    for price_lut in self.stocks.values():
      dates = sorted(price_lut.keys())
      date_range = (max(date_range[0], dates[0]), min(date_range[1], dates[-1]))
      date_idxs  = (dates.index(date_range[0]), dates.index(date_range[1]))
      self.dates = dates[date_idxs[0]:date_idxs[1] + 1]
    self.date = (0, self.dates[0])
      
  def advance_day(self):
    self.date = (self.date[0] + 1, self.dates[self.date[0] + 1])
    self.__raise_period_flags()

  def __raise_period_flags(self):
    last_date = date_obj(self.dates[self.date[0] - 1])
    curr_date = date_obj(self.date[1])
    self.new_period = {'m': False, 'q': False, 'y': False}
    if last_date.year < curr_date.year:
      self.new_period = {'m': True, 'q': True, 'y': True}
      return 0
    if last_date.month != curr_date.month:
      self.new_period['m'] = True
      if (curr_date.month - 1) % 3 == 0:
        self.new_period['q'] = True
      return 0
    return 0

  def __build_stocks(self, tickers):
    for ticker in tickers:
      self.stocks[ticker.upper()] = build_price_lut(ticker.upper())

class Simulator:

  stat_keys = ['PORT_VAL', 'ASST_ALLOC', 'ANN_RET', 'CONTR_GRWTH']

  def __init__(self):
    self.portfolio = None
    self.contribution = (0, '', 0)
    self.rebalance_trigger = ''
    self.market = None
    self.commission_cost = 0
    self.dates_set = (False, False)
    self.dates_testing = (None, None)
    self.trade_history = [[],[]]
    self.__init_stats()

  def add_portfolio(self, portfolio):
    self.portfolio = portfolio

  def set_market(self, market):
    self.market = market

  def set_commission(self, cost):
    self.commission_cost = float(cost)

  def set_start_date(self, date):
    self.dates_testing = (date, self.dates_testing[1])
    self.dates_set = (True, self.dates_set[1])

  def set_end_date(self, date):
    self.dates_testing = (self.dates_testing[0], date)
    self.dates_set = (self.dates_set[0], True)

  def remove_date_limits(self):
    self.dates_set = (False, False)
    self.dates_testing = (None, None)

  def define_contributions(self, amount, period):
    self.contribution = (float(amount), period.lower(), 0)

  def define_rebalancing(self, trigger):
    self.rebalance_trigger = trigger.lower()

  def simulate(self):
    err = 0
    err += self.__init_market()
    err += self.__init_simulation_dates()
    err += self.__init_portfolio()
    if err:
      return -1
    
    while self.market.current_date() < self.dates_testing[1]:
      self.market.advance_day()
      holdings = list(self.portfolio.holdings.keys())
      self.portfolio.update_holdings_values(holdings, [self.market.query_stock(x) for x in holdings])
      self.__adjust_portfolio()
      self.__record_stats()
    return 0
    
  def __init_market(self):
    if self.market == None:
      return -1
    if len(self.market.stocks) == 0:
      self.market.add_stocks(self.portfolio.assets.keys())
    if self.market.dates == None:
      self.market.set_default_dates()
    return 0

  def __init_portfolio(self):
    if self.portfolio == None:
      return -1
    self.initial_cash = self.portfolio.cash
    for (ticker,portion) in self.portfolio.assets.items():
      self.__enter_position(ticker, (self.initial_cash * portion) // self.market.query_stock(ticker))
    return 0
  
  def __init_simulation_dates(self):
    if not self.dates_set[0] or self.dates_testing[0] < self.market.dates[0]:
      self.dates_testing = (self.market.dates[0], self.dates_testing[1])
    else:
      self.market.set_date(self.dates_testing[0])
    if not self.dates_set[1] or self.dates_testing[1] > self.market.dates[-1]:
      self.dates_testing = (self.dates_testing[0], self.market.dates[-1])
      
    self.dates_set = (True, True)
    return 0

  def __init_stats(self):
    self.stats = {}
    for key in self.stat_keys:
      self.stats[key] = [[],[]]
      if key == self.stat_keys[2]:
        self.stats[key].append([])

  def __adjust_portfolio(self):
    # contributions
    if self.contribution[1] and self.market.new_period[self.contribution[1]]:
      self.portfolio.cash += self.contribution[0]
      self.contribution = (self.contribution[0], self.contribution[1], self.contribution[2] + self.contribution[0])
    # rebalancing
    if self.rebalance_trigger and self.market.new_period[self.rebalance_trigger]:
      share_changes = {}
      for (asset, portion) in self.portfolio.assets.items():
        target = int(portion * self.portfolio.value() // self.market.query_stock(asset))
        share_changes[asset] = target - abs(self.portfolio.holdings[asset])
      for (asset, change) in sorted(share_changes.items(), key=lambda x: share_changes[x[0]]):
        if change < 0:
          self.__exit_position(asset, abs(change))
        else: 
          self.__enter_position(asset, abs(change))

  def __enter_position(self, ticker, shares):
    self.trade_history[0].append(self.market.current_date())
    self.trade_history[1].append('enter: ' + self.portfolio.assets_types[ticker] + ' ' + ticker + ' ' + str(shares))
    if self.portfolio.assets_types[ticker] == 'long':
      self.portfolio.buy(ticker.upper(), shares, self.market.query_stock(ticker.upper()), self.commission_cost)
      return 0
    if self.portfolio.assets_types[ticker] == 'short':
      self.portfolio.short(ticker.upper(), shares, self.market.query_stock(ticker.upper()), self.commission_cost)
      return 0

  def __exit_position(self, ticker, shares):
    self.trade_history[0].append(self.market.current_date())
    self.trade_history[1].append('exit:  ' + self.portfolio.assets_types[ticker] + ' ' + ticker + ' ' + str(shares))
    if self.portfolio.assets_types[ticker] == 'long':
      self.portfolio.sell(ticker.upper(), shares, self.market.query_stock(ticker.upper()), self.commission_cost)
      return 0
    if self.portfolio.assets_types[ticker] == 'short':
      self.portfolio.cover(ticker.upper(), shares, self.market.query_stock(ticker.upper()), self.commission_cost)
      return 0


  def __record_stats(self):
    # portfolio value history
    self.stats[self.stat_keys[0]][0].append(self.market.current_date())
    self.stats[self.stat_keys[0]][1].append(self.portfolio.value())

    # asset allocation
    assets = sorted(self.portfolio.assets.keys())
    self.stats[self.stat_keys[1]][0].append(self.market.current_date())
    alloc = [abs(self.portfolio.holdings_values[assets[i]] / self.portfolio.value()) for i in range(0, len(assets))]
    self.stats[self.stat_keys[1]][1].append(alloc)
      
    # annual returns
    if self.market.new_period['y'] or len(self.stats[self.stat_keys[2]][2]) == 0:
      self.stats[self.stat_keys[2]][0].append(str(date_obj(self.market.current_date()).year - 1))
      self.stats[self.stat_keys[2]][1].append(self.portfolio.value())
      if len(self.stats[self.stat_keys[2]][2]) == 0:
        self.stats[self.stat_keys[2]][2].append(0.0)
      else:
        self.stats[self.stat_keys[2]][2].append(self.portfolio.value() / self.stats[self.stat_keys[2]][1][-2] - 1)

    # comtributions vs growth
    self.stats[self.stat_keys[3]][0].append(self.market.current_date())
    contribution = max(0, self.contribution[2] + self.initial_cash)
    growth = max(0, self.portfolio.value() - contribution)
    self.stats[self.stat_keys[3]][1].append((contribution, growth))

class Portfolio:

  def __init__(self, cash):
    self.cash = float(cash)
    self.holdings = {}
    self.holdings_values = {}
    self.assets = {}
    self.assets_types = {}

  def add_asset(self, ticker, portion, asset_type):
    self.assets[ticker.upper()] = float(portion)
    self.assets_types[ticker.upper()] = asset_type

  def buy(self, ticker, amount, price, commission):
    try:
      self.holdings[ticker.upper()] += int(amount)
    except KeyError:
      self.holdings[ticker.upper()] = int(amount)
    self.holdings_values[ticker.upper()] = self.holdings[ticker.upper()] * float(price)
    self.cash -= int(amount) * float(price) - float(commission)
    return 0

  def sell(self, ticker, amount, price, commission):
    try:
      self.holdings[ticker.upper()] -= int(amount)
    except KeyError:
      self.holdings[ticker.upper()] = -int(amount)
    self.holdings_values[ticker.upper()] = self.holdings[ticker.upper()] * float(price)
    self.cash += int(amount) * float(price) - float(commission)
    return 0

  def short(self, ticker, amount, price, commission):
    self.sell(ticker, amount, price, commission)

  def cover(self, ticker, amount, price, commission):
    self.buy(ticker, amount, price, commission)

  def update_holdings_values(self, tickers, new_prices):
    for i in range(0, len(tickers)):
      self.holdings_values[tickers[i].upper()] = float(new_prices[i]) * int(self.holdings[tickers[i].upper()])

  def value(self):
    return self.cash + sum(self.holdings_values.values())


class SteppedAvgLookup:

  def __init__(self, step, keys, vals):
    self.__lut = {}
    self.__num_points = {}
    self.__build_lut(step, keys, vals)

  def get(self, val):
    for key in sorted(self.__lut.keys()):
      if val < key:
        return self.__lut[key]

  def get_num_points(self, val):
    for key in sorted(self.__num_points.keys()):
      if val < key:
        return self.__num_points[key]

  def __build_lut(self, step, keys, vals):
    for i in range(int(min(keys)//step), int(max(keys)//step)):
      self.__lut[i*step] = 0
      self.__num_points[i*step] = 0
    self.__lut[float("inf")] = 0
    self.__num_points[float("inf")] = 0
    steps = sorted(self.__lut.keys())
    for i in range(0, len(keys)):
      for j in range(0, len(steps)):
        if keys[i] < steps[j]:
          self.__lut[steps[j]] = ((self.__lut[steps[j]] * self.__num_points[steps[j]] + vals[i]) /
                                  (self.__num_points[steps[j]] + 1))
          break
    for key in sorted(self.__lut.keys()):
      if self.__lut[key] == 0:
        del self.__lut[key]


##############################################################################
# SIMPLE HELPERS
##############################################################################

def filename(ticker):
  return STOCK_DIR + ticker + ".csv"

def readlines(filename):
  with open(filename, 'r') as file:
    lines = [line.strip() for line in file]
  return lines
    
def currency(number):
  return "{0:.2f}".format(float(number))

def percent(number):
  return "{0:.2f}".format(float(number * 100))

def yahoo_url(ticker):
  return "http://ichart.finance.yahoo.com/table.csv?s=" + ticker

def has_file(ticker):
  return os.path.isfile(filename(ticker))

def date_obj(date):
  if type(date) is dt:
    return date
  if type(date) is datetime.date:
    return dt(date.year, date.month, date.day)
  return dt.strptime(date, DATE_FORMAT)

def date_str(date):
  if type(date) is str:
    return date
  return date.strftime(DATE_FORMAT)


##############################################################################
# MAIN HELPERS
##############################################################################

# Calculate SMA for period at each value, given a list of values
def get_sma(values, period):
  period = int(period)
  sma = []
  sum = 0
  for i in range(0, period - 1):
    sum += float(values[i])
    sma.append(sum/(i + 1))
  for i in range(period - 1, len(values)):
    sum = 0
    for j in range(i, i - period, -1): 
      sum += float(values[j])
    sma.append(sum/period)
  return sma

# Calculate EMA for period at each value, given a list of values
def get_ema(values, period):
  period = int(period)
  ema = get_sma(values[0:period], period)
  multiplier = 2 / (period + 1)
  for i in range(period, len(values)):
    ema.append(float(values[i]) * multiplier + ema[-1] * (1 - multiplier))
  return ema

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

###
# NOTE ON PERFORMANCE: readlines >>>>>> read_rows > read_columns
#                      use readlines where possible
#

def read_csv_file_rows(filename):
  data = []
  file_content = readlines(filename)
  if file_content == 0:
    return data
  eof = len(file_content) - 1
  for i in range(eof, 0, -1):
    data.append([])
    for value in file_content[i].split(','):
      data[eof - i].append(value.strip())
  return data

def read_csv_file_columns(filename):
  try:
    file = open(filename)
  except FileNotFoundError as e:
    print("error: no such file '" + filename + "'")
    return []
  data = []
  for line in file:
    values = line.split(',')
    for i in range(0, len(values)):
      if len(data) < len(values):
        data.append([])
      data[i].append(values[i].strip())
  for i in range(0, len(values)):
    del data[i][0]
    data[i] = data[i][::-1]
  file.close()
  return data

def write_list_to_file(list, filename, overwrite):
  if overwrite and os.path.isfile(filename):
    os.remove(filename)
  written = 0
  with open(filename, 'w') as file:
    for item in list:
      written += 1
      file.write(item + '\n')
  return written

# Builds a dictionary from a file, dates as keys and prices as values
def build_price_lut(ticker):
  price_lookup = {}
  file_content = readlines(filename(ticker))
  for i in range(1, len(file_content)):
    price_lookup[file_content[i].split(',')[0]] = float(file_content[i].split(',')[6])
  return price_lookup

# Download historical data for a list of stocks, given their tickers
def download_stocks_data(ticker_list, quiet):
  download_failed = []
  for ticker in ticker_list:
    if not quiet:
      print('.', end='')
    try:
      urllib.request.urlretrieve(yahoo_url(ticker.strip()), filename(ticker.strip()))
    except urllib.error.ContentTooShortError as e:
      download_failed.append(ticker.strip())
    except urllib.error.HTTPError as e:
      download_failed.append(ticker.strip())
  if not quiet:
    print('')
  return download_failed

def list_from_csv(filename, col, s_char, r_chars):
  lines = readlines(filename)
  l = []
  for i in range(1, len(lines)):
    l.append(lines[i].split(s_char)[col].strip())
    for r in r_chars:
      l[-1] = l[-1].replace(r, '')
  return l

# Subtracts the period from the given date, returns date in same type as input
def subtract_date(period, unit, date):
  diffs = {'y': 0, 'm': 0, 'd': 0}
  diffs[unit.lower()] = int(period)
  new = {}
  new['y'] = date_obj(date).year - diffs['y'] - diffs['m'] // 12
  new['m'] = date_obj(date).month - diffs['m'] % 12
  if new['m'] < 1:
    new['y'] = new['y'] + (new['m'] - 1) // 12
    new['m'] = new['m'] - ((new['m'] - 1) // 12) * 12
  new['d'] = min(calendar.monthrange(new['y'], new['m'])[1], date_obj(date).day)
  new_date = dt(new['y'], new['m'], new['d']) - datetime.timedelta(diffs['d'])
  if type(date) is str:
    return date_str(new_date)
  return new_date

def nearest_index(val, vals, direction, val_type):
  if val_type == 'date':
    return nearest_date_index(val, vals, direction)
  if len(vals) == 0 or (vals[-1] < val and direction > 0) or (vals[0] > val and direction < 0):
    return -1
  if direction > 0 and vals[0] > val:
    return 0
  if direction < 0 and vals[-1] < val:
    return len(vals) - 1
  for i in range(0, (len(vals) - 1)):
    if (val > vals[i] and val <= vals[i+1] and direction > 0):
      return i+1
    if (val <= vals[i] and val > vals[i+1] and direction < 0):
      return i
  return -1

def nearest_date_index(date, dates, direction):
  if len(dates) == 0 or date_str(dates[-1]) < date_str(date):
    return -1
  if date_str(dates[0]) >= date_str(date):
    return 0
  last_date = date_obj(dates[-1])
  first_date = date_obj(dates[0])
  target_date = date_obj(date)
  approx_factor = len(dates) / (last_date - first_date).days
  i = int((target_date - first_date).days * approx_factor)
  if i > 0:
    i -= 1
  if date_str(dates[i]) == date_str(date):
    return i
  if date_str(dates[i]) < date_str(date):
    while date_str(dates[i]) < date_str(date):
      i += 1
  else:
    while date_str(dates[i - 1]) >= date_str(date):
      i -= 1
  if direction == 0:
    return min([i, i-1], key=lambda x: abs((date_obj(dates[x]) - date_obj(date)).days))
  if direction < 0:
    return i - 1
  if direction > 0:
    return i

# Calculates changes in price (%) over a certain period given a list of stocks
def get_growth(period, period_unit, tickers):
  changes = {}
  for i in range(0, len(tickers)):
    price_lookup = build_price_lut(tickers[i])
    dates = sorted(price_lookup.keys())
    target_date = dates[nearest_index(subtract_date(period, period_unit, dates[-1]), dates, 1, 'date')]
    changes[tickers[i]] = price_lookup[dates[-1]] / price_lookup[target_date] - 1
  return changes

# Get the best performing stocks out of a list of stocks over a period
def get_best(number, period, period_unit, tickers):
  n = number
  if n > len(tickers):
    n = len(tickers)
  growth = get_growth(period, period_unit, stock_list)
  return sorted(growth.items(), key=lambda x: x[1], reverse=True)[0:n]

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
      if i > 0 and (float(data[i][6]) > float(data[i-1][6]) * max_split or
                    float(data[i][6]) < float(data[i-i][6]) / max_split):
        clean = False
        break
    if clean:
      cleaned_stocks.append(stock)
  return cleaned_stocks

def compare_movement(data_a, data_b):
  changes_a = []
  changes_b = []
  ratios = []
  for i in range(min(len(data_a),len(data_b)), 1, -1):
    changes_a.append(float(data_a[-i+1])/float(data_a[-i]) - 1)
    changes_b.append(float(data_b[-i+1])/float(data_b[-i]) - 1)
    if changes_b[-1] == 0:
      ratios.append(0.0)
    else:
      ratios.append(changes_a[-1]/changes_b[-1])
  return [changes_a, changes_b, ratios]

def generate_theoretical_data(ticker_a, ticker_b, step, pos_adj, neg_adj):
  data_a = read_csv_file_columns(filename(ticker_a))
  data_b = read_csv_file_columns(filename(ticker_b))
  if len(data_a[0]) > len(data_b[0]):
    source_data = data_a
    target_data = data_b
  else:
    source_data = data_b
    target_data = data_a
  changes = compare_movement(target_data[6], source_data[6])
  lut = SteppedAvgLookup(step, changes[1], changes[2])
  generated_data = [float(target_data[6][0])]
  for i in range(source_data[0].index(target_data[0][0]), 0, -1):
    change = float(source_data[6][i])/float(source_data[6][i-1]) - 1
    if change >= 0:
      price = generated_data[0] / (change * (lut.get(change) + pos_adj) + 1)
    else:
      price = generated_data[0] / (change * (lut.get(change) + neg_adj) + 1)
    generated_data.insert(0, price)
  for i in range(source_data[0].index(target_data[0][0]) + 1, len(source_data[0])):
    change = float(source_data[6][i])/float(source_data[6][i-1]) - 1
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

  args = parser.parse_args()

  if args.download != None:
    failed = download_stocks_data(args.download, True)
    if len(failed) == len(args.download):
      print("failed to download provided stock(s). exiting.")
    if len(failed) > 0:
      failed_stocks = ', '.join(failed)
      print("failed to download:\n" + failed_stocks)
      
  if args.download_using != None:
    failed = download_stocks_data([line.strip() for line in readlines(args.download_using[0])], False)
    if len(failed) == len(args.download):
      print("failed to download provided stock(s). exiting.")
    if len(failed) > 0:
      failed_stocks = ', '.join(failed)
      print("failed to download:\n" + failed_stocks)

  if args.download_using_csv != None:
    failed = download_stocks_data(list_from_csv(args.download_using_csv[0], 0, ',', ['"']), False)
    if len(failed) == len(args.download):
      print("failed to download provided stock(s). exiting.")
    if len(failed) > 0:
      failed_stocks = ', '.join(failed)
      print("failed to download:\n" + failed_stocks)

  if args.best_stocks != None:
    stock_list = clean_stock_list(list_from_csv(args.best_stocks[2], 0, ',', ['"']), 1, 5)
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
    adjustments = {'UPRO': (0.19, 0.2), 'TMF': (0.19, 0.2)}
    adjustment = (0, 0)
    if args.generate[0] in adjustments.keys():
      adjustment = adjustments[args.generate[0]]
    [gen_prices, idx, etf, src, changes] = generate_theoretical_data(args.generate[0], args.generate[1], 0.00009, adjustment[0], adjustment[1])
    dates = [[],[]]
    dates[0] = [dt.strptime(d, "%Y-%m-%d").date() for d in etf[0]]
    dates[1] = [dt.strptime(d, "%Y-%m-%d").date() for d in src[0]]
    pyplot.subplot(211)
    pyplot.plot(dates[0], etf[6], label=args.generate[0])
    pyplot.plot(dates[0], gen_prices[-len(etf[6]):], label=args.generate[0]+'-generated')
    pyplot.legend(loc='upper left')
    pyplot.subplot(212)
    pyplot.plot(dates[1], src[6], label=args.generate[1])
    pyplot.plot(dates[1], gen_prices, label=args.generate[0]+'-generated')
    pyplot.legend(loc='upper left')
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
    my_market = Market(None, None)
    if args.use_generated != None:
      for i in range(0, len(args.use_generated) // 2):
        data = generate_theoretical_data(args.use_generated[i*2], args.use_generated[i*2+1], 0.00009, 0.19, 0.2)
        my_market.inject_stock_data(args.use_generated[i*2], data[3][0], data[0])
    
    my_portfolio = Portfolio(float(args.portfolio[0]))
    for i in range(0, len(args.portfolio[6:]) // 3):
      my_portfolio.add_asset(args.portfolio[i*3+6], float(args.portfolio[i*3+7]), args.portfolio[i*3+8])

    my_sim = Simulator()
    my_sim.add_portfolio(my_portfolio)
    my_sim.set_market(my_market)
    my_sim.define_contributions(args.portfolio[1], args.portfolio[2])
    my_sim.define_rebalancing(args.portfolio[3])
    if args.portfolio[4]:
      my_sim.set_start_date(args.portfolio[4])
    if args.portfolio[5]:
      my_sim.set_end_date(args.portfolio[5])

    port_vals = []
    port_vals.append(my_portfolio.value())
    my_sim.simulate()
    port_vals.append(my_portfolio.value())

    print('initial -> $' + currency(port_vals[0]))
    print('final ---> $' + currency(port_vals[1]))
    
#    for i in range(0, len(my_sim.trade_history[0])):
#      print(my_sim.trade_history[0][i] + ' : ' + my_sim.trade_history[1][i])

    (dates, y) = my_sim.stats[Simulator.stat_keys[0]]
    x = [dt.strptime(d, "%Y-%m-%d").date() for d in dates]

    years = (x[-1] - x[0]).days / 365.25
    print('CAGR ----> ' + percent((port_vals[1] / port_vals[0]) ** (1/years) - 1) + '%')

    pyplot.subplot(411)
    pyplot.plot(x, y)
    pyplot.grid(b=True, which='major', color='grey', linestyle='-')

    (dates, ratios) = my_sim.stats[Simulator.stat_keys[1]]
    x = [dt.strptime(d, "%Y-%m-%d").date() for d in dates]
    y = [[ratio[i] for ratio in ratios] for i in range(0, len(ratios[0]))]
    legend = sorted(my_portfolio.assets.keys())
    

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
    print(' from ' + drawdown_start  + ' to ' + drawdown_end + ' recovered by ' + drawdown_recover)

    # plot contributions vs growth

    (dates, values) = my_sim.stats[Simulator.stat_keys[3]]
    x = [date_obj(d).date() for d in dates]
    y = [[c/(c+g) for c,g in values], [g/(c+g)for c,g in values]]

    pyplot.subplot(414)
    pyplot.stackplot(x, y, alpha=0.5)
    pyplot.grid(b=True, which='major', color='grey', linestyle='-')
    pyplot.legend(['Contributions', 'Growth'], loc='upper left')

    # figure out total contributions, ratio of contributions:value, CAGR ignoring contributions
    print('---')
    print('total contributions: $' + currency(my_sim.contribution[2]))
    print('total growth: $' + currency(my_portfolio.value() - my_sim.contribution[2] - port_vals[0]))
    print('adjusted CAGR: ' + percent(((my_portfolio.value() - my_sim.contribution[2]) / port_vals[0]) ** (1/years) - 1) + '%')

    pyplot.show()
    
  exit()

if __name__ == "__main__":
  main()
