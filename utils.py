"""A collection of utility classes and methods to be used throughout
the diferent modules and classes in this project.

Todo:
    - [code improvement, low priority] rewrite nearest_index using
        next() and enumerate()
    - [for fun, low priority] run benchmark on nearest_date_index
"""

import datetime
from datetime import datetime as dt
import os
import os.path

STOCK_DIR = "data/"
DATE_FORMAT = "%Y-%m-%d"

######
# CLASSES
#####


class SteppedAvgLookup(object):

    """A look up table/mapping of values to averages..

    Given a set of keys and values and a step range, calculates the
    average value for all steps based on the keys that lie in those
    steps.
    e.g. if step = 1, (keys,values) = (1.1, 10), (2.3, 5), (2.5, 3),
        then the LUT it will build is:
            0 to 2   -> 10 (0 to 2 is steps 0 to 1, and 1 to 2,
                            which has pairs (1.1, 10))
            2 to inf -> 4  (2 to inf is steps 2 to 3, 3 to 4, ... etc,
                            which has pairs (2.3, 5), (2.5, 3))

    Used for calculating the average "near" certain values, given
    enough data for such a notion to be useful, but not enough data
    to have an average for every single value.

    Currently, primary use is estimating an ETF's true leverage factor
    at its underlying asset's movement, e.g. UPRO and SPY. There is
    enough data (every day between July 2009 and today) to estimate
    how UPRO moves relative to SPY (supposedly 3x, but in reality it
    varies) at a given movement of SPY.
    """

    def __init__(self, step, keys, vals):
        """Initializes an empty lookup and then builds it based on the
        given values.

        Args:
            step: A value specifying the step size, while a higher
                value may give more precision, that does not always
                imply more accuracy
            keys: An array of keys which correspond to the values
            vals: An array of values which correspond to the keys
        """
        self._lut = {}
        self._num_points = {}
        self._build_lut(step, keys, vals)

    def get(self, val):
        """Gets the average at the neatest key greater than the given
        value.

        Args:
            val: A value for which an average is wanted

        Returns:
            A value corresponding the the average at the given value
        """
        for key in sorted(self._lut.keys()):
            if val < key:
                return self._lut[key]

    def get_num_points(self, val):
        """Returns the number of data points at the given step.

        Used internally for calculating averages.

        Args:
            val: A value for which the number of data points is wanted

        Returns:
            A value corresponding to the number of data points at the
            given value
        """
        for key in sorted(self._num_points.keys()):
            if val < key:
                return self._num_points[key]

    def _build_lut(self, step, keys, vals):
        """Internal function for building the LUT.

        Args:
            step: A value specifying the step size, while a higher
                value may give more precision, that does not always
                imply more accuracy
            keys: An array of keys which correspond to the values
            vals: An array of values which correspond to the keys
        """
        for i in range(int(min(keys) // step), int(max(keys) // step)):
            self._lut[i * step] = 0
            self._num_points[i * step] = 0
        self._lut[float("inf")] = 0
        self._num_points[float("inf")] = 0
        steps = sorted(self._lut.keys())
        for i in range(0, len(keys)):
            for j in range(0, len(steps)):
                if keys[i] < steps[j]:
                    self._lut[steps[j]] = \
                        ((self._lut[steps[j]]
                          * self._num_points[steps[j]] + vals[i])
                         / (self._num_points[steps[j]] + 1))
                    break
        for key in sorted(self._lut.keys()):
            if self._lut[key] == 0:
                del self._lut[key]


######
# FUNCTIONS
#####

def currency(number):
    """Nicer looking wrapper for converting to currency format.

    Args:
        number: A number value to covert to currency format

    Returns:
        A number in currency format
    """
    return "{0:.2f}".format(float(number))


def percent(number):
    """Nicer looking wrapper for converting to percent format.

    Args:
        number: A number value to covert to percent format

    Returns:
        A number in percent format
    """
    return "{0:.2f}".format(float(number * 100))


def date_obj(date):
    """Returns the equivalent datetime object for the given date or
    date object.

    Args:
        number: A date string or date/datetime object

    Returns:
        A datetime object representing the given date
    """
    if type(date) is dt:
        return date
    if type(date) is datetime.date:
        return dt(date.year, date.month, date.day)
    return dt.strptime(date, DATE_FORMAT)


def date_str(date):
    """Returns the equivalent date string for the given date or
    date object.

    Args:
        number: A date string or date/datetime object

    Returns:
        A date string representing the given date
    """
    if type(date) is str:
        return date
    return date.strftime(DATE_FORMAT)


def write_list_to_file(list, filename, overwrite):
    """Writes a list to a newline separated file.

    Args:
        list: An array/list to write to file
        filename: A filename of a file to which to write
        overwrite: A boolean for whether or not to overwrite an
            existing file

    Returns:
        Number of lines written
    """
    if overwrite and os.path.isfile(filename):
        os.remove(filename)
    written = 0
    with open(filename, 'a') as file:
        for item in list:
            written += 1
            file.write(item + '\n')
    return written


def list_from_csv(filename, col, s_char, r_chars):
    """Extracts a specific column from a CSV file, given a split char.
    Also removes all given chars from the values.

    Args:
        filename: A filename of a CSV file
        col: A value for a column in a CSV file
        s_char: A character representing a delimiter
        r_chars: An array of characters to remove

    Returns:
        An array of values corresponding to the stripped column
    """
    lines = readlines(filename)
    with open(filename, 'r') as file:
        lines = [line.strip() for line in file]
    column_lines = []
    for i in range(1, len(lines)):
        column_lines.append(lines[i].split(sfilname_char)[col].strip())
        for r in r_chars:
            column_lines[-1] = column_lines[-1].replace(r, '')
    return column_lines


def subtract_date(period, unit, date):
    """Subtracts the period from the given date, returns date in same
    type as input.

    Args:
        period: A period value, e.g. 3 (for 3 days/months/years)
        unit: A unit for the period, e.g. 'm' for month
        date: A date from which to subtract

    Returns:
        A new date value in the same type as input
    """
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


def nearest_index(val, vals, direction, val_type=None):
    """Given a value, finds the index of the nearest value before/after
    said value in an array of values.

    Using val_type uses an optimization. Currently only supports
    'date' as a val_type, since dates are relatively predictable in
    their distribution.

    Args:
        val: A value for which to find the nearest value in values
        vals: An array of values to look through
        direction: A 'direction' (-1 or +1) for looking, i.e. to look
            for a nearest lower value or nearest higher value
        val_type: A type of value - used for optimizations

    Returns:
        An index for the nearest value, -1 otherwise
    """
    if val_type == 'date':
        return nearest_date_index(val, vals, direction)
    if (len(vals) == 0
        or (vals[-1] < val and direction > 0)
        or (vals[0] > val and direction < 0)):
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


def nearest_date_index(date, dates, direction):
    """Optimization for nearest index for date types.

    Approximates where the date would be based on starting and ending
    dates in list and starts search there. In practise, only takes a
    few steps.

    Args:
        date: A date for which to find the nearest date in dates
        dates: An array of dates to look through
        direction: A 'direction' (-1 or +1) for looking, i.e. to look
            for a nearest lower value or nearest higher value

    Returns:
        An index for the nearest date
    """
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
        return min([i, i - 1],
                   key=lambda x: abs((date_obj(dates[x])
                                      - date_obj(date)).days))
    if direction < 0:
        return i - 1
    if direction > 0:
        return i
