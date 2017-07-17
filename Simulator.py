import datetime
from datetime import datetime as dt

from utils import date_str, date_obj, build_price_lut

###
# A simulator for a portfolio in a market, given some conditions
# Supports:
#   - rebalancing on certain time periods
#   - commissions for making a trade
#   - contributions on certain time periods
# Features:
#   - setting custom date ranges
#   - records (per day) portfolio value history
#   - records (per day) asset allocation
#   - records (per day) contribution vs growth portfolio total value
#   - records (per year) annual returns
##
class Simulator:

    stat_keys = ['PORT_VAL', 'ASST_ALLOC', 'ANN_RET', 'CONTR_GRWTH']

    ##
    # initializes an empty simulator with values set to 0, False, or None
    def __init__(self):
        self.portfolio = None
        self.trader = None
        self.contribution = (0, '', 0)
        self.rebalance_trigger = ''
        self.market = None
        self.commission_cost = 0
        self.dates_set = (False, False)
        self.dates_testing = (None, None)
        self.trade_history = [[], []]
        self.__init_stats()

    ##
    # (currently) sets the simulator's portfolio
    # TODO: make multiple portfolios
    def add_portfolio(self, portfolio):
        self.portfolio = portfolio

    def add_trader(self, trader):
        """"""
        self.trader = trader

    ##
    # sets this simulator's market
    def set_market(self, market):
        self.market = market

    ##
    # sets the commissions per trade
    def set_commission(self, cost):
        self.commission_cost = float(cost)

    ##
    # sets the date at which the simulation will start
    def set_start_date(self, date):
        self.dates_testing = (date, self.dates_testing[1])
        self.dates_set = (True, self.dates_set[1])

    ##
    # sets the date at which the simulation will end
    def set_end_date(self, date):
        self.dates_testing = (self.dates_testing[0], date)
        self.dates_set = (self.dates_set[0], True)

    ##
    # removes any date range for which to run the simulation
    def remove_date_limits(self):
        self.dates_set = (False, False)
        self.dates_testing = (None, None)

    ##
    # define an amount to contribute to the portfolio every given period
    def define_contributions(self, amount, period):
        self.contribution = (float(amount), period.lower(), 0)

    ##
    # define the trigger (i.e. period) at which to rebalance the portfolio
    # TODO: add more types of triggers
    def define_rebalancing(self, trigger):
        self.rebalance_trigger = trigger.lower()

    ##
    # runs the simulation with the given configuration
    def simulate(self):
        err = 0
        err += self.__init_market()
        print(err)
        err += self.__init_simulation_dates()
        print(err)
        err += self.trader.initialize_portfolio()
        print(err)
        if err:

            return -1

        while self.market.current_date() < self.dates_testing[1]:
            self.market.advance_day()
            holdings = list(self.trader.portfolio.holdings.keys())
            self.trader.portfolio.update_holdings_values(
                holdings, [self.market.query_stock(x) for x in holdings])
            self.trader.adjust_portfolio()
            self.__record_stats()
        return 0

    ##
    # initializes/resets the market to work with the current simulation setup
    def __init_market(self):
        if self.market == None:
            return -1
        if len(self.market.stocks) == 0:
            self.market.add_stocks(self.trader.assets_of_interest)
        if self.market.dates == None:
            self.market.set_default_dates()
        return 0

    ##
    # initializes/resets the portfolio to work with the current simulation setup
    def __init_portfolio(self):
        if self.trader.portfolio == None:
            return -1
        self.initial_cash = self.trader.portfolio.cash
        for (ticker, portion) in self.trader.portfolio.assets.items():
            self.__enter_position(
                ticker, (self.initial_cash * portion) // self.market.query_stock(ticker))
        return 0

    ##
    # sets up the dates of the simulation and market to match
    def __init_simulation_dates(self):
        if not self.dates_set[0] or self.dates_testing[0] < self.market.dates[0]:
            self.dates_testing = (self.market.dates[0], self.dates_testing[1])
        else:
            self.market.set_date(self.dates_testing[0])
        if not self.dates_set[1] or self.dates_testing[1] > self.market.dates[-1]:
            self.dates_testing = (self.dates_testing[0], self.market.dates[-1])

        self.dates_set = (True, True)
        return 0

    ##
    # initializes/resets the stats for this simulation
    # TODO: I think the whole stat system needs to be reworked to be more scalable
    def __init_stats(self):
        self.stats = {}
        for key in self.stat_keys:
            self.stats[key] = [[], []]
            if key == self.stat_keys[2]:
                self.stats[key].append([])

    ##
    # looks at the portfolio and makes adjustments based on conditions set earlier
    # TODO: move into Trader class, probably?
    # def __adjust_portfolio(self):
    #     # contributions
    #     if self.contribution[1] and self.market.new_period[self.contribution[1]]:
    #         self.portfolio.cash += self.contribution[0]
    #         self.contribution = (
    #             self.contribution[0], self.contribution[1], self.contribution[2] + self.contribution[0])
    #     # rebalancing
    #     if self.rebalance_trigger and self.market.new_period[self.rebalance_trigger]:
    #         share_changes = {}
    #         for (asset, portion) in self.portfolio.assets.items():
    #             target = int(portion * self.portfolio.value() //
    #                          self.market.query_stock(asset))
    #             share_changes[asset] = target - \
    #                 abs(self.portfolio.holdings[asset])
    #         for (asset, change) in sorted(share_changes.items(), key=lambda x: share_changes[x[0]]):
    #             if change < 0:
    #                 self.__exit_position(asset, abs(change))
    #             else:
    #                 self.__enter_position(asset, abs(change))

    ##
    # depending on the type of position, buys/shorts a position for a certain number of shares
    def __enter_position(self, ticker, shares):
        self.trade_history[0].append(self.market.current_date())
        self.trade_history[1].append(
            'enter: ' + self.portfolio.assets_types[ticker] + ' ' + ticker + ' ' + str(shares))
        if self.portfolio.assets_types[ticker] == 'long':
            self.portfolio.buy(ticker.upper(), shares, self.market.query_stock(
                ticker.upper()), self.commission_cost)
            return 0
        if self.portfolio.assets_types[ticker] == 'short':
            self.portfolio.short(ticker.upper(), shares, self.market.query_stock(
                ticker.upper()), self.commission_cost)
            return 0

    ##
    # depending on the type of position, sells/covers a position for a certain number of shares
    def __exit_position(self, ticker, shares):
        self.trade_history[0].append(self.market.current_date())
        self.trade_history[1].append(
            'exit:  ' + self.portfolio.assets_types[ticker] + ' ' + ticker + ' ' + str(shares))
        if self.portfolio.assets_types[ticker] == 'long':
            self.portfolio.sell(ticker.upper(), shares, self.market.query_stock(
                ticker.upper()), self.commission_cost)
            return 0
        if self.portfolio.assets_types[ticker] == 'short':
            self.portfolio.cover(ticker.upper(), shares, self.market.query_stock(
                ticker.upper()), self.commission_cost)
            return 0

    ##
    # takes a snapshot of the current portfolio situation and records it into the stats
    # TODO: again, probably needs to be reworked, maybe into own class
    def __record_stats(self):
        # portfolio value history
        self.stats[self.stat_keys[0]][0].append(self.market.current_date())
        self.stats[self.stat_keys[0]][1].append(self.trader.portfolio.value())

        # asset allocation
        assets = sorted(self.trader.assets_of_interest)
        self.stats[self.stat_keys[1]][0].append(self.market.current_date())
        alloc = [abs(self.trader.portfolio.holdings_values[assets[i]] /
                     self.trader.portfolio.value()) for i in range(0, len(assets))]
        self.stats[self.stat_keys[1]][1].append(alloc)

        # annual returns
        if self.market.new_period['y'] or len(self.stats[self.stat_keys[2]][2]) == 0:
            self.stats[self.stat_keys[2]][0].append(
                str(date_obj(self.market.current_date()).year - 1))
            self.stats[self.stat_keys[2]][1].append(self.trader.portfolio.value())
            if len(self.stats[self.stat_keys[2]][2]) == 0:
                self.stats[self.stat_keys[2]][2].append(0.0)
            else:
                self.stats[self.stat_keys[2]][2].append(
                    self.trader.portfolio.value() / self.stats[self.stat_keys[2]][1][-2] - 1)

        # comtributions vs growth
        self.stats[self.stat_keys[3]][0].append(self.market.current_date())
        contribution = max(0, self.trader.portfolio.total_contributions)
        growth = max(0, self.trader.portfolio.value() - contribution)
        #print("{}: {}".format(self.market.current_date(), contribution))
        self.stats[self.stat_keys[3]][1].append((contribution, growth))
