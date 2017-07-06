import urllib.request
import os
import os.path
import datetime

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
    # routes to the correct source and handles errors
    # NOTE: currently sort of useless
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
        curr_date = "0000-00-00"
        last_date = datetime.date.today().strftime("%Y-%m-%d")
        data = []
        while True:
            new_data = self.__download_google_csv_data(ticker, last_date)
            if not len(new_data):
                break
            if new_data[-1][0] >= last_date:
                # new data is later than what we've read so far, i.e. it's old data
                break
            data += new_data
            last_date = (datetime.datetime.strptime(new_data[-1][0], "%Y-%m-%d") - datetime.timedelta(1)).strftime("%Y-%m-%d")
        self.__write_data_to_file(ticker, data)
        return 0

    ##
    # use the yahoo finance api to download all data for a ticker into a consistent
    # format on disk, which can then be parsed by an independent function or class
    # to access yahoo currently, a cookie from a response header needs to be scraped
    # and used to request data
    def __download_using_yahoo(self, ticker):
        return 1

    ##
    # simple URL generating function for the google finance API
    def __google_url(self, ticker, date):
        url = "http://www.google.com/finance/historical"
        url += "?q=" + ticker
        url += "&enddate=" + datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%b") + "%20"
        url += datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d") + ",%20"
        url += datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%Y")
        url += "&output=csv"
        return url

    ##
    # downloads (a year of) data from google ending at a certain date and returns an array
    # in [[date, open, high, low, close, volume], [...], ...] format
    def __download_google_csv_data(self, ticker, date):
        data = []
        csv = urllib.request.urlopen(self.__google_url(ticker, date)).readlines()
        for line in csv[1:]:
            data.append(line.decode("ASCII").strip().split(','))
            data[-1][0] = datetime.datetime.strptime(data[-1][0], "%d-%b-%y").strftime("%Y-%m-%d")
        return data

    ##
    # simple filename generating function for a ticker
    def __filename(self, ticker):
        return "data/" + ticker.upper() + ".csv"

    ##
    # writes an array in [[date, open, high, low, close, volume], [...], ...] format to CSV style file
    def __write_data_to_file(self, ticker, data):
        if os.path.isfile(self.__filename(ticker)):
            os.remove(self.__filename(ticker))
        with open(self.__filename(ticker), 'w') as file:
            for line in data:
                file.write(','.join(line) + '\n')

if __name__ == "__main__":
    downloader = Downloader()
    downloader.download('UPRO', 'google')
    exit
