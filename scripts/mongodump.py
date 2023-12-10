from trisigma.domain.portfolio import PortfolioManager, StrategyAllocation, Exposure, ExposureTable
from trisigma.domain.brokerage import Order, order_status, FinancialAccount
from trisigma.domain.trading import Trader, StrategyDefinition, to_strategy_uri
from trisigma.domain.common import modelfactory
from trisigma.domain.market import Instrument
from pymongo import MongoClient
import datetime
import os

"""
collections:
    order
    portfolio_manager
    strategy_allocation
    portfolio_position
    portfolio_snapshot
    financial_account
    strategy_definitions
    trader
    trader_observations
    trader_comments
"""

class Seed():
    def account_id(self, s):
        return 100000000 + s
    def pm_id(self, s):
        return 200000000 + s
    def trader_id(self, s):
        return 300000000 + s
    def order_id(self, s):
        return hex(int(("1" + "0"*31), 16) + s)[2:]

seed = Seed()
DB_NAME = "trisigma_test"
MONGO_URI = os.getenv("MONGO_URI"); assert MONGO_URI

client = MongoClient(MONGO_URI)
client.drop_database(DB_NAME)
def _insert(collection, data):
    client[DB_NAME][collection].insert_one(data)

def push_trader(
    account_id, strategy_uri, start_time, trader_id, meta=None):
    o = Trader(
            account_id=account_id,
            strategy_uri=strategy_uri,
            start_time=start_time,
            trader_id=trader_id,
            meta=meta or {})
    _insert("trader", modelfactory.deconstruct(o))

def push_account(account_id, portfolio_manager_id, name, platform, paper, meta=None):
    o = FinancialAccount(
            account_id=account_id,
            portfolio_manager_id=portfolio_manager_id,
            name=name,
            platform=platform,
            paper=paper,
            meta=meta or {})
    _insert("financial_account", modelfactory.deconstruct(o))

def push_pm(portfolio_manager_id, name, meta=None):
    o = PortfolioManager(
            portfolio_manager_id=portfolio_manager_id,
            name=name,
            meta=meta or {})
    _insert("portfolio_manager_id", modelfactory.deconstruct(o))

def push_strategy_allocation(portfolio_manager_id, allocation, meta=None):
    _insert("strategy_allocation", {
        'portfolio_manager_id': portfolio_manager_id,
        'allocation': allocation,
        'meta': meta or {}})

def push_strategy_allocation_naming(portfolio_manager_id, naming, meta=None):
    _insert("strategy_allocation_naming", {
        'portfolio_manager_id': portfolio_manager_id,
        'naming': naming,
        'meta': meta or {}})

def push_exposure_table(account_id, exposure_table):
    _insert("exposure_table", {
        'account_id': account_id,
        'exposure_table': modelfactory.deconstruct(exposure_table)}

def push_strategydef(name, version, options, meta=None):
    o = StrategyDefinition(
            name=name,
            version=version,
            options=options,
            meta=meta or {})
    _insert("strategy_definitions", modelfactory.deconstruct(o))

def push_order(instrument, side, qty, order_type, t, order_status=order_status.FILLED, price=None, tif=None, account_id=None, meta=None):
    meta = meta or {}
    o = Order(
            time=t,
            instrument=instrument,
            side=side,
            qty=qty,
            status=order_status,
            order_type=order_type,
            price=price,
            tif=tif,
            account_id=account_id,
            meta=meta)
    _insert("order", modelfactory.deconstruct(o))

def push_portfolio_pos(portfolio_manager_id, pos):
    _insert("portfolio_position", {'portfolio_manager_id': portfolio_manager_id, 'position': pos})

def push_portfolio_snapshot(portfolio_manager_id, t, snapshot):
    _insert("portfolio_snapshot", {
        'portfolio_manager_id': portfolio_manager_id,
        'time': t,
        'snapshot': {'positions': snapshot}})

def push_trader_observation(trader_id, observation):
    _insert("trader_observations", {'trader_id': trader_id, 'observation': observation})

def push_trader_comment(trader_id, comment):
    _insert("trader_comments", {'trader_id': trader_id, 'comment': comment})

def main():
    ST1 = to_strategy_uri('strategy1', {'asset':'AAPL', 'ncandle': 3})
    ST2 = to_strategy_uri('strategy2', {'asset':'SPY', 'letter': 'A'})
    ST3 = to_strategy_uri('strategy3', {'asset':'TSLA', 'ncandle': 0.3})
    T1 = datetime.datetime(2023, 2, 11, 17, 45, 30, 123).timestamp()
    T2 = datetime.datetime(2023, 11, 29, 12, 15, 13, 123).timestamp()
    T3 = datetime.datetime(2023, 11, 29, 12, 15, 14, 123).timestamp()

    push_strategydef("strategy1", "v1", {'asset': {'type': '$asset'}, 'ncandle': {'type': 'rangeint', 'min': 1, 'max': 15}})
    push_strategydef("strategy2", "v1.1", {'asset': {'type': '$asset'}, 'letter': {'type': 'dropdown', 'options': ['A', 'B', 'C']}})
    push_strategydef("strategy3", "v2.0", {'asset': {'type': '$asset', 'exclude': ['SPY']}, 'exp': {'type': 'range', 'min': 0, 'max': 1}})
    push_pm(seed.pm_id(1), "pm1")
    push_pm(seed.pm_id(2), "pm2")
    push_account(seed.account_id(0), seed.pm_id(0), "acc3", "Webull", False)
    push_account(seed.account_id(1), seed.pm_id(1), "acc1", "IBKR", True)
    push_account(seed.account_id(2), seed.pm_id(1), "acc2", "IBKR", False)
    push_account(seed.account_id(3), seed.pm_id(1), "acc3", "Webull", False)
    push_strategy_allocation(seed.pm_id(1), {ST1: 0.5, ST2: 0.3, ST3: 0.1})
    push_strategy_allocation_naming(seed.pm_id(1), {ST1: "first strategy", ST2: "second strategy", ST3: "third strategy"})

    acc_scl = [100, 1000, 10000]
    ppos = {str(seed.account_id(i-1)): {'AAPL': 1*acc_scl[i], 'SPY': -1*acc_scl[i], 'USD': 100*acc_scl[i]} for i in range(3)}
    push_portfolio_pos(seed.pm_id(1), ppos)

    for i in range(1, 4):
        exposure_table = ExposureTable(
                {ST1:Exposure(alloc={'AAPL': 0.3}, buffer={}),
                 ST2:Exposure(alloc={'SPY': -1}, buffer={}),
                 ST3:Exposure(alloc={'TESLA': 1}, buffer={})},
                {ST1: 0.5, ST2, 0.3, ST3: 0.1})
        push_exposure_table(account_id=seed.account_id(i), exposure_table=exposure_table)

        push_trader(seed.account_id(i), ST1, T2, seed.trader_id(1 + (i-1)*3))
        push_trader(seed.account_id(i), ST2, T2, seed.trader_id(2 + (i-1)*3))
        push_trader(seed.account_id(i), ST3, T2, seed.trader_id(3 + (i-1)*3))

        scl = acc_scl[i-1]
        meta = {'trader_id': seed.trader_id(1 + (i-1)*3)}
        push_order(Instrument.stock('AAPL', 'USD'), "BUY", 2*scl, "MARKET", account_id=seed.account_id(i), t=T3-86400+100, meta=meta)
        push_order(Instrument.stock('AAPL', 'USD'), "SELL", 1*scl, "MARKET", account_id=seed.account_id(i), t=T3-86400+200, meta=meta)
        push_order(Instrument.stock('AAPL', 'USD'), "BUY", 1*scl, "MARKET", account_id=seed.account_id(i), t=T3-86400+300, meta=meta)
        push_order(Instrument.stock('AAPL', 'USD'), "SELL", 1*scl, "MARKET", account_id=seed.account_id(i), t=T3-86400+400, meta=meta)

        meta = {'trader_id': seed.trader_id(2 + (i-1)*3)}
        push_order(Instrument.stock('SPY', 'USD'), "SELL", 1*scl, "MARKET", account_id=seed.account_id(i), t=T3-86400+130, meta=meta)
        push_order(Instrument.stock('SPY', 'USD'), "BUY", 2*scl, "MARKET", account_id=seed.account_id(i), t=T3-86400+230, meta=meta)
        push_order(Instrument.stock('SPY', 'USD'), "SELL", 2*scl, "MARKET", account_id=seed.account_id(i), t=T3-86400+330, meta=meta)

        meta = {'trader_id': seed.trader_id(3 + (i-1)*3)}
        push_order(Instrument.stock('TSLA', 'USD'), "SELL", 1*scl, "MARKET", account_id=seed.account_id(i), t=T3-86400+120, meta=meta)
        push_order(Instrument.stock('TSLA', 'USD'), "BUY", 1*scl, "LIMIT", price=300, account_id=seed.account_id(i), t=T3-86400+220, meta=meta)
        push_order(Instrument.stock('TSLA', 'USD'), "BUY", 1*scl, "LIMIT", price=310, account_id=seed.account_id(i), t=T3-86400+320, meta=meta)
        push_order(Instrument.stock('TSLA', 'USD'), "SELL", 1*scl, "LIMIT", price=308, account_id=seed.account_id(i), t=T3-86400+420, meta=meta)
        push_order(Instrument.stock('TSLA', 'USD'), "SELL", 1*scl, "LIMIT", price=308,
                   order_status=order_status.SUBMITTED, account_id=seed.account_id(i), t=T3-86400+230, meta=meta)


        obs1 = {'time': T3 - 86400+103, 'observation': {'price?asset=AAPL': 100.15, 'SMA?asset=AAPL&n=20': 104}}
        obs2 = {'time': T3 - 86400+113, 'observation': {'price?asset=AAPL': 101.80, 'SMA?asset=AAPL&n=20': 104.11}}
        obs3 = {'time': T3 - 86400+123, 'observation': {'price?asset=AAPL': 100.78, 'SMA?asset=AAPL&n=20': 104.08}}
        obs4 = {'time': T3 - 86400+133, 'observation': {'price?asset=AAPL': 103.45, 'SMA?asset=AAPL&n=20': 104.12}}
        push_trader_observation(seed.trader_id(1 + (i-1)*3), obs1)
        push_trader_observation(seed.trader_id(1 + (i-1)*3), obs2)
        push_trader_observation(seed.trader_id(1 + (i-1)*3), obs3)
        push_trader_observation(seed.trader_id(1 + (i-1)*3), obs4)

        obs1 = {'time': T3 - 86400+103, 'observation': {'price?asset=SPY': 400.15, 'SMA?asset=AAPL&n=25': 404}}
        obs2 = {'time': T3 - 86400+113, 'observation': {'price?asset=SPY': 401.80, 'SMA?asset=AAPL&n=25': 404.11}}
        obs3 = {'time': T3 - 86400+123, 'observation': {'price?asset=SPY': 400.78, 'SMA?asset=AAPL&n=25': 404.08}}
        obs4 = {'time': T3 - 86400+133, 'observation': {'price?asset=SPY': 403.45, 'SMA?asset=AAPL&n=25': 404.12}}
        push_trader_observation(seed.trader_id(2 + (i-1)*3), obs1)
        push_trader_observation(seed.trader_id(2 + (i-1)*3), obs2)
        push_trader_observation(seed.trader_id(2 + (i-1)*3), obs3)
        push_trader_observation(seed.trader_id(2 + (i-1)*3), obs4)

        obs1 = {'time': T3 - 86400+103, 'observation': {'price?asset=SPY': 300.15, 'SMA?asset=AAPL&n=10': 304}}
        obs2 = {'time': T3 - 86400+113, 'observation': {'price?asset=SPY': 301.80, 'SMA?asset=AAPL&n=10': 304.11}}
        obs3 = {'time': T3 - 86400+123, 'observation': {'price?asset=SPY': 300.78, 'SMA?asset=AAPL&n=10': 304.08}}
        obs4 = {'time': T3 - 86400+133, 'observation': {'price?asset=SPY': 303.45, 'SMA?asset=AAPL&n=10': 304.12}}
        push_trader_observation(seed.trader_id(3 + (i-1)*3), obs1)
        push_trader_observation(seed.trader_id(3 + (i-1)*3), obs2)
        push_trader_observation(seed.trader_id(3 + (i-1)*3), obs3)
        push_trader_observation(seed.trader_id(3 + (i-1)*3), obs4)

        com1 = {'time': T3 - 86400+101, 'comment': 'some comment'}
        com2 = {'time': T3 - 86400+111, 'comment': 'about to go into the next tick'}
        com3 = {'time': T3 - 86400+121, 'comment': 'this is from the first strategy'}
        com4 = {'time': T3 - 86400+131,  'comment': 'the last but not least comment'}
        push_trader_comment(seed.trader_id(1 + (i-1)*3), com1)
        push_trader_comment(seed.trader_id(1 + (i-1)*3), com2)
        push_trader_comment(seed.trader_id(1 + (i-1)*3), com3)
        push_trader_comment(seed.trader_id(1 + (i-1)*3), com4)

        com1 = {'time': T3 - 86400+101, 'comment': 'some comment'}
        com2 = {'time': T3 - 86400+111, 'comment': 'about to go into the next tick'}
        com3 = {'time': T3 - 86400+121, 'comment': 'this is from the second strategy'}
        com4 = {'time': T3 - 86400+131,  'comment': 'the last but not least comment'}
        push_trader_comment(seed.trader_id(2 + (i-1)*3), com1)
        push_trader_comment(seed.trader_id(2 + (i-1)*3), com2)
        push_trader_comment(seed.trader_id(2 + (i-1)*3), com3)
        push_trader_comment(seed.trader_id(2 + (i-1)*3), com4)

        com1 = {'time': T3 - 86400+101, 'comment': 'some comment'}
        com2 = {'time': T3 - 86400+111, 'comment': 'about to go into the next tick'}
        com3 = {'time': T3 - 86400+121, 'comment': 'this is from the third strategy'}
        com4 = {'time': T3 - 86400+131,  'comment': 'the last but not least comment'}
        push_trader_comment(seed.trader_id(3 + (i-1)*3), com1)
        push_trader_comment(seed.trader_id(3 + (i-1)*3), com2)
        push_trader_comment(seed.trader_id(3 + (i-1)*3), com3)
        push_trader_comment(seed.trader_id(3 + (i-1)*3), com4)

    spos = {str(seed.account_id(i-1)): {
        'AAPL': {'qty': 1*acc_scl[i], 'value': 130*acc_scl[i]},
        'SPY': {'qty': -1*acc_scl[i], 'value': -430*acc_scl[i]},
        'USD': {'qty': 500*acc_scl[i], 'value': 500*acc_scl[i]}} for i in range(3)}
    push_portfolio_snapshot(seed.pm_id(1), T3 - 86400*20, spos)

    spos = {str(seed.account_id(i-1)): {
        'AAPL': {'qty': 1*acc_scl[i], 'value': 120*acc_scl[i]},
        'SPY': {'qty': -1*acc_scl[i], 'value': -400*acc_scl[i]},
        'USD': {'qty': 500*acc_scl[i], 'value': 500*acc_scl[i]}} for i in range(3)}
    push_portfolio_snapshot(seed.pm_id(1), T3 - 86400*15, spos)

    spos = {str(seed.account_id(i-1)): {
        'AAPL': {'qty': 2*acc_scl[i], 'value': 330*acc_scl[i]},
        'SPY': {'qty': 0*acc_scl[i], 'value': 0*acc_scl[i]},
        'USD': {'qty': 250*acc_scl[i], 'value': 250*acc_scl[i]}} for i in range(3)}
    push_portfolio_snapshot(seed.pm_id(1), T3 - 86400*10, spos)

    spos = {str(seed.account_id(i-1)): {
        'AAPL': {'qty': 1*acc_scl[i], 'value': 120*acc_scl[i]},
        'SPY': {'qty': -1*acc_scl[i], 'value': -400*acc_scl[i]},
        'USD': {'qty': 500*acc_scl[i], 'value': 500*acc_scl[i]}} for i in range(3)}
    push_portfolio_snapshot(seed.pm_id(1), T3 - 86400*5, spos)

    spos = {str(seed.account_id(i-1)): {
        'AAPL': {'qty': 1*acc_scl[i], 'value': 120*acc_scl[i]},
        'SPY': {'qty': -1*acc_scl[i], 'value': -400*acc_scl[i]},
        'USD': {'qty': 500*acc_scl[i], 'value': 500*acc_scl[i]}} for i in range(3)}
    push_portfolio_snapshot(seed.pm_id(1), T3, spos)


if __name__ == "__main__":
    main()


