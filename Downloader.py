import urllib.request
import os
import os.path
import datetime
import argparse
from DataManager import DataManager

###
# Argument definitions for the usage of the Downloader class directly from the command line
##
parser = argparse.ArgumentParser(description="Downloader for historical stock data.")
download_group = parser.add_mutually_exclusive_group(required=True)
download_group.add_argument('--download', nargs='+', help='the stock ticker(s) to download')
download_group.add_argument('--download-from', nargs='+', help='file(s) containing the stock tickers to download')
parser.add_argument('--using', default='google', nargs=1, help='a source/API from which to get the data, default: google')


###
# A class that handles downloading and coverting stock data into a format usable by the
# rest of the program
##
class Downloader:

    def __init__(self):
        self.sources = {
            'yahoo':  self.__download_using_yahoo,
            'google': self.__download_using_google
        }

    ##
    # given a ticker and preferred source, downloads all ticker data from source to disk
    def download(self, ticker, preferred_source):
        if preferred_source:
            return self.__download_from_source(preferred_source, ticker)
        for source in self.sources:
            err = self.__download_from_source(source, ticker)
            if not err:
                return 0
        print('error: could not download from any sources')

    ##
    # given a file and preferred source, downloads all the ticker(s) data from source to disk
    def download_from_files(self, ticker_files, preferred_source):
        for ticker_file in ticker_files:
            with open(ticker_file, 'r') as file:
                ticker_lines = file.readlines()
            for line in ticker_lines:
                self.download(line.strip(), preferred_source)

    ##
    # given a list and preferred source, downloads all ticker(s) data in list from source to disk
    def download_from_list(self, ticker_list, preferred_source):
        for ticker in ticker_list:
            self.download(ticker, preferred_source)

    ##
    # routes to the correct source and handles errors
    # TODO: currently sort of useless
    def __download_from_source(self, source, ticker):
        err = self.sources[source](ticker)
        if err:
            print('error: could not download ' + ticker + ' using ' + source)
        return err


    ##
    # use the google finance api to download all data for a ticker into a consistent
    # format on disk, which can then be parsed by an independent function or class
    # unless an exact start date is known, google finance returns 1 year at a time, so
    # this will download and convert one year at a time going backwards until it
    # reaches the end
    def __download_using_google(self, ticker):
        last_date = datetime.date.today().strftime("%Y-%m-%d")
        data = []
        while True:
            new_data = self.__download_google_csv_data(ticker, last_date)
            if not len(new_data):
                break
            if new_data[0][0] >= last_date:
                # new data is later than what we've read so far, i.e. it's old data
                break
            data = new_data + data
            last_date = (datetime.datetime.strptime(new_data[0][0], "%Y-%m-%d") - datetime.timedelta(1)).strftime("%Y-%m-%d")
        self.__write_data_to_file(ticker, data)
        return 0

    ##
    # use the yahoo finance api to download all data for a ticker into a consistent
    # format on disk, which can then be parsed by an independent function or class
    # to access yahoo currently, a cookie from a response header needs to be scraped
    # and used to request data
    def __download_using_yahoo(self, ticker):
        return 1

    def __google_url(self, ticker, date):
        """Simple URL generating function for the Google finance API.

        Args:
            ticker: A string representing the ticker to download
            date: A string in 'YYYY-MM-DD' format representing the end date for the data
        """
        # TODO: adhere to string formatting guidelines
        # TODO: currently implementing a hackish way to generate the URL
        special_cases = {
            'TLT': 'NASDAQ'
        }
        quote_ticker = ticker
        if ticker.upper() in special_cases.keys():
            quote_ticker = special_cases[ticker.upper()] + '%3A' + ticker
        url = "http://www.google.com/finance/historical"
        url += "?q=" + quote_ticker
        url += "&enddate=" + datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%b") + "%20"
        url += datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d") + ",%20"
        url += datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%Y")
        url += "&output=csv"
        print(url)
        return url

    ##
    # downloads (a year of) data from google ending at a certain date and returns an array
    # in [[date, open, high, low, close, volume], [...], ...] format
    def __download_google_csv_data(self, ticker, date):
        data = []
        csv = urllib.request.urlopen(self.__google_url(ticker, date)).readlines()
        for line in csv[1:]:
            data = [line.decode("ASCII").strip().split(',')] + data
            #data.append(line.decode("ASCII").strip().split(','))
            data[0][0] = datetime.datetime.strptime(data[0][0], "%d-%b-%y").strftime("%Y-%m-%d")
        return data

    ##
    # simple filename generating function for a ticker
    # TODO: moved to DataManager
    def __filename(self, ticker):
        return "data/" + ticker.upper() + ".csv"

    ##
    # writes an array in [[date, open, high, low, close, volume], [...], ...] format to CSV style file
    # TODO: moved to DataManager, should now move this out of the downloader class altogerher
    def __write_data_to_file(self, ticker, data):
        db = DataManager()
        db.write_stock_data(ticker, data, True)


###
# MAIN
##
if __name__ == "__main__":
    downloader = Downloader()
    args = parser.parse_args()
    if args.download_from:
        downloader.download_from_files(args.download_from, args.using)
        exit()
    if args.download:
        downloader.download_from_list(args.download, args.using)
        exit()
    exit()
