#############
# A collection of utility classes and functions to be used throughout the different
# files and classes in this project
###########

from datetime import datetime as dt
import os
import os.path

STOCK_DIR = "data/"
DATE_FORMAT = "%Y-%m-%d"

######
# CLASSES
#####

###
# A look up table/mapping of values to averages. Given a set of keys and values and a step range,
# calculates the average value for all steps based on the keys that lie in those steps
# e.g. if step = 1, (keys,values) = (1.1, 10), (2.3, 5), (2.5, 3), then the LUT it will build is:
#      0 to 2   -> 10 (0 to 2 is steps 0 to 1, and 1 to 2, which has (1.1, 10))
#      2 to inf -> 4  (2 to inf is steps 2 to 3, 3 to 4, ... etc, which has (2.3, 5), (2.5, 3))
# Used for calculating the average "near" certain values, given enough data for such a
# notion to be useful, but not enough data to have an average for every single value
##
class SteppedAvgLookup:

    ##
    # initializes an empty lookup and then builds it based on given values
    def __init__(self, step, keys, vals):
        self.__lut = {}
        self.__num_points = {}
        self.__build_lut(step, keys, vals)

    ##
    # gets the average at the nearest key greater than the given value
    def get(self, val):
        for key in sorted(self.__lut.keys()):
            if val < key:
                return self.__lut[key]

    ##
    # gets the number of points at each step (used for calculating average)
    def get_num_points(self, val):
        for key in sorted(self.__num_points.keys()):
            if val < key:
                return self.__num_points[key]

    ##
    # internal function for building the LUT
    def __build_lut(self, step, keys, vals):
        for i in range(int(min(keys) // step), int(max(keys) // step)):
            self.__lut[i * step] = 0
            self.__num_points[i * step] = 0
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


######
# FUNCTIONS
#####

##
# the filename of the data for a given ticker
def filename(ticker):
    return STOCK_DIR + ticker + ".csv"


##
# like traditional readlines, just also does some boilerplate stuff
def readlines(filename):
    with open(filename, 'r') as file:
        lines = [line.strip() for line in file]
    return lines


##
# nicer looking wrapper for converting to currency format
def currency(number):
    return "{0:.2f}".format(float(number))


##
# nicer looking wrapper for converting to percent format
def percent(number):
    return "{0:.2f}".format(float(number * 100))


##
# the yahoo URL to the yahoo finance API for a given ticker
# NOTE deprecated, since yahoo discontinued this service
def yahoo_url(ticker):
    return "http://ichart.finance.yahoo.com/table.csv?s=" + ticker


##
# nicer looking wrapper for checking if a file exists
def has_file(ticker):
    return os.path.isfile(filename(ticker))


##
# takes a date str or datetime/date object and returns the equivalent datetime object
def date_obj(date):
    if type(date) is dt:
        return date
    if type(date) is datetime.date:
        return dt(date.year, date.month, date.day)
    return dt.strptime(date, DATE_FORMAT)


##
# takes a date string of datetime/date object and returns the equivalent date string
def date_str(date):
    if type(date) is str:
        return date
    return date.strftime(DATE_FORMAT)


##
# returns the rows of a CSV file, where each row is an array
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


##
# returns the columns of a CSV file, where each column is an array
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


##
# writes a list to a newline separated file
def write_list_to_file(list, filename, overwrite):
    if overwrite and os.path.isfile(filename):
        os.remove(filename)
    written = 0
    with open(filename, 'w') as file:
        for item in list:
            written += 1
            file.write(item + '\n')
    return written


##
# extracts a specific column from a CSV file, given a split char and chars to remove
# NOTE really specific use case and might be removed
def list_from_csv(filename, col, s_char, r_chars):
    lines = readlines(filename)
    l = []
    for i in range(1, len(lines)):
        l.append(lines[i].split(s_char)[col].strip())
        for r in r_chars:
            l[-1] = l[-1].replace(r, '')
    return l


##
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
    new['d'] = min(calendar.monthrange(
        new['y'], new['m'])[1], date_obj(date).day)
    new_date = dt(new['y'], new['m'], new['d']) - \
        datetime.timedelta(diffs['d'])
    if type(date) is str:
        return date_str(new_date)
    return new_date


##
# given a value, finds the index of the nearest value before/after said value
# val_type is for implemented optimizations, currently supports:
# - 'date' for arrays of dates
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
        if (val > vals[i] and val <= vals[i + 1] and direction > 0):
            return i + 1
        if (val <= vals[i] and val > vals[i + 1] and direction < 0):
            return i
    return -1


##
# optimization for nearest index for date types. approximates where the date would be based on
# starting and ending dates in list and starts search there. in practise, only takes a few steps
# TODO: for fun, run some benchmarks just to see
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
        return min([i, i - 1], key=lambda x: abs((date_obj(dates[x]) - date_obj(date)).days))
    if direction < 0:
        return i - 1
    if direction > 0:
        return i


##
# Builds a dictionary from a file, dates as keys and prices as values
def build_price_lut(ticker):
    price_lookup = {}
    file_content = readlines(filename(ticker))
    for i in range(1, len(file_content)):
        price_lookup[file_content[i].split(',')[0]] = float(
            file_content[i].split(',')[6])
    return price_lookup
