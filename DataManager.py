import os
import os.path


class DataManger(object):
    """A DataManager is responsible for managing (i.e. storing and retrieving) data on disk.

    In other words, this class provides an interface by which stock data can be queried from or stored onto disk.
    Generally speaking, 'public' functions house high level logic for publicly used actions, while 'private' functions act as wrappers for low level or commonly used and simple, but ugly to write actions.

    Attributes:
        data_location: A string indicating where the stock data is stored on disk
    """

    def __init__(self, data_location='data/'):
        """Inits DataManager with a data location."""
        self.data_location = data_location

    def write_stock_data(self, ticker, data):
        """Writes an array of data to a file on disk.

        Args:
            ticker: A string representing the ticker of a stock
            data: An array in [[date, open, high, low, close, volume], ...] format
        """
        self._remove_file_for(ticker)
        self._write_data_to_csv_file(self._filename_for(ticker), data)

    def read_stock_data(ticker, format):
        """Retrieves stock data for a given ticker in a given format from disk.

        Args:
            ticker: A string representing the ticker of a stock
            format: A string representing whether the data should be in column or row format

        Returns:
            An array in either row or column format contaning the data for a given stock
        """
        if format == 'column':
            return self._read_csv_file_columns_for(ticker)
        if format == 'row':
            return self._read_csv_file_rows_for(ticker)
        return []

    def build_price_lut(ticker):
        """Builds a price look up table for a given ticker.

        Args:
            ticker: A string representing the ticker of a stock

        Returns:
            A dictionary with dates as keys and prices as values
        """
        price_lookup = {}
        file_content = self._readlines_for(ticker)
        for i in range(0, len(file_content)):
            line_data = file_content[i].split(',')
            price_lookup[line_data[0]] = float(line_data[4])
        return price_lookup

    def _write_data_to_csv_file(filename, data):
        """Writes an array of data to disk in CSV format.

        Args:
            filename: A string representing the file to which to write
            data: An array in [[date, open, high, low, close, volume], ...] format
        """
        with open(filename, 'w') as file:
            for line in data:
                file.write(','.join(line) + '\n')

    def _filename_for(ticker):
        """Returns the file name for a ticker, including the path to said file.

        Args:
            ticker: A string representing the ticker of a stock

        Returns:
            A String representing the filename, inluding path, for the given ticker
        """
        return self.data_location + ticker.upper() + ".csv"

    def _readlines_for(ticker):
        """Returns the lines of the file for a given ticker.

        Args:
            ticker: A string representing the ticker of a stock

        Returns:
            An array with each element containing a line of the file for the given ticker
        """
        with open(self._filename(ticker), 'r') as file:
            lines = [line.strip() for line in file]
        return lines

    def _has_file_for(ticker):
        """Returns whether a file for a given ticker exists.

        Args:
            ticker: A string representing the ticker of a stock

        Returns:
            A boolean value representing whether or not a file exists for a given ticker
        """
        return os.path.isfile(self._filename(ticker))

    def _remove_file_for(ticker):
        """Removes the file for the given ticker.

        Args:
            ticker: A string representing the ticker of a stock
        """
        os.remove(self._filename(ticker))

    def _read_csv_file_rows_for(ticker):
        """Reads and returns the data in a CSV file for a given ticker in row-by-row format.

        Args:
            ticker: A string representing the ticker of a stock

        Returns:
            An array, where each element is an array containing data for a row in a CSV file
        """
        data = []
        file_content = readlines(filename)
        eof = len(file_content) - 1
        for i in range(eof, 0, -1):
            data.append([])
            data[eof - i].append(value.strip()) for value in file_content[i].split(',')
        return data

    def _read_csv_file_columns_for(ticker):
        """Reads and returns the data in a CSV file for a given ticker in column-by-column format.

        Args:
            ticker: A string representing the ticker of a stock

        Returns:
            An array, where each element is an array containing data for a column in a CSV file
        """
        data = []
        file_content = readlines(filename)
        # create arrays for each column
        for i in range(0, len(file_content[0].split(','))):
            data.append([])
        # iterate through file
        eof = len(file_content) - 1
        for i in range(eof, 0, -1):
            values = file_content[i].split(',')
            data[j].append(values[j].strip()) for j in range(0, len(values))
        return data
