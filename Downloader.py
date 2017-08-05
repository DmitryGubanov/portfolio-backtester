import urllib.request
import os
import os.path
import datetime
import argparse
from DataManager import DataManager


class Downloader(object):

    """A Downloader that handles downloading stock data and returning
    it in a consitent format.

    Currently only supports downloading from Google Finance API.
    Stores data in CSV format with Date,Open,High,Low,Close,Volume
    columns.

    Attributes:
        sources: mapping of source string to handler method

    Todo:
        - [code improvement, low priority] implement yahoo downloading
            as backup
        - [code improvement, low priority] implement only downloading
            missing data, rather than all
        - [code improvement, low priority] implement way to verify
            data, and downloading holes from 2nd source
    """

    def __init__(self):
        """Initializes a Downlaoder used for downloading stock data."""
        self.sources = {
            'yahoo':  self._download_using_yahoo,
            'google': self._download_using_google
        }

    def download(self, ticker, preferred_source, quiet=True):
        """Downloads and returns stock data for a ticker from a source.

        A simple routing method that uses a (source -> download method)
        mapping.

        Args:
            ticker: A string representing the ticker of a stock
            preferred_source: A string representing a download source
            quiet: A boolean for whether or not to print progress
                feedback, default: True

        Returns:
            An array containing the stock data in chronological order
        """
        return self.sources[preferred_source](ticker, quiet)

    def _download_using_google(self, ticker, quiet=True):
        """Downloads and returns stock data from Google.

        A method that acts as a wrapper for logic pertaining to
        downloading from Google specifically. Unless start date is
        known, Google will only provide one year at a time. So this
        method downloads one year at a time until no new data is
        downloaded.

        Args:
            ticker: A string representing the ticker of a stock
            quiet: A boolean for whether or not to print progress
                feedback, default: True

        Returns:
            An array of stock data in chronological order
        """
        data = []
        last_date = datetime.date.today().strftime("%Y-%m-%d")
        if not quiet:
            print('Downloading {} data from Google'.format(ticker),
                  end='', flush=True)
        while True:
            new_data = self._download_google_csv_data(ticker, last_date)
            if not quiet:
                print('.', end='', flush=True)
            if not len(new_data):
                break
            if new_data[0][0] >= last_date:
                break
            data = new_data + data
            last_date = (datetime.datetime.strptime(new_data[0][0], "%Y-%m-%d")
                         - datetime.timedelta(1)).strftime("%Y-%m-%d")
        if not quiet:
            print('')
        return data

    def _download_using_yahoo(self, ticker):
        """Downloads and returns stock data from Yahoo Finance.

        Not implemented, since Google is sufficient for my purposes at
        the moment. However, it will need to scrape a cookie from a
        response header and then use it to request data
        NOTE: some people reported the above method doesnt work anymore

        Args:
            ticker: A string representing the ticker of a stock

        Returns:
            An array of stock data in chronological order
        """
        return []

    def _google_url(self, ticker, date, market=None):
        """Simple URL generating function for the Google finance API.

        Args:
            ticker: A string representing the ticker to download
            date: A string in 'YYYY-MM-DD' format representing the end
                date for the data
            market: An optional value to specify the market for the
                ticker
        """
        # special cases 'hack' to handle weirdness of Google API
        special_cases = {
            'TLT': 'NASDAQ'
        }
        dt = datetime.datetime.strptime(date, '%Y-%m-%d')
        base = 'http://www.google.com/finance/historical'
        if market:
            query = '{}%3A{}'.format(market, ticker)
        else:
            try:
                query = '{}%3A{}'.format(special_cases[ticker.upper()], ticker)
            except KeyError:
                query = '{}'.format(ticker)
        enddate = '{}%20{},%20{}'.format(
            dt.strftime('%b'), dt.strftime('%d'), dt.strftime('%Y'))
        output = 'csv'
        return '{}?q={}&enddate={}&output={}'.format(
            base, query, enddate, output)

    def _download_google_csv_data(self, ticker, date):
        """Handler for making a URL request to Google and interpretting
        the data.

        Requests data from Google via a URL and converts the data to
        [[date, open, high, low, close, volume], ...] format.

        Args:
            ticker: A string representing the ticker of a stock
            date: A string in YYYY-MM-DD format representing the end
                date for the request

        Todo:
            - error handling for urllib request
        """
        data = []
        try:
            csv = urllib.request.urlopen(
                self._google_url(ticker, date)).readlines()
        except urllib.error.HTTPError:
            csv = urllib.request.urlopen(
                self._google_url(ticker, date, 'NYSE')).readlines()
        for line in csv[1:]:
            data = [line.decode("ASCII").strip().split(',')] + data
            data[0][0] = datetime.datetime.strptime(
                data[0][0], "%d-%b-%y").strftime("%Y-%m-%d")
        return data


def download_and_write(ticker, source):
    """Wrapper for downloading and writing.

    Args:
        ticker: A string for the ticker data to download
        source: A string for the source to download from
    """
    data = downloader.download(ticker, source, False)
    if len(data) == 0:
        print("No data downloaded for {}".format(ticker))
        return
    db.write_stock_data(ticker, data, True)


def main():
    """Wrapper for main logic."""
    args = parser.parse_args()
    # handle downloading from list of files
    if args.download_from:
        for file_with_tickers in args.download_from:
            with open(file_with_tickers, 'r') as file:
                lines = file.readlines()
            for line in lines:
                download_and_write(line.strip(), args.using)
        exit()
    # handle downlaoding from list of tickers
    if args.download:
        for ticker in args.download:
            download_and_write(ticker, args.using)
        exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Downloader for historical stock data.")
    parser.add_argument('--using', default='google', nargs=1,
                        help=('a source/API from which to get the data, '
                              'default: google'))
    download_group = parser.add_mutually_exclusive_group(required=True)
    download_group.add_argument('--download', nargs='+',
                                help='the stock ticker(s) to download')
    download_group.add_argument('--download-from', nargs='+',
                                help=('file(s) containing the stock tickers to'
                                      'download'))

    downloader = Downloader()
    db = DataManager()

    main()
    print("Did nothing.")
    exit()
