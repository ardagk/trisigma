from trisigma.domain.portfolio import PortfolioManager, StrategyAllocation, Exposure, ExposureTable
from trisigma.domain.brokerage import Order, order_status, FinancialAccount
from trisigma.domain.trading import Trader, StrategyDefinition, to_strategy_uri
from trisigma.domain.common import modelfactory
from trisigma.domain.market import Instrument
from pymongo import MongoClient
import datetime
import os
from copy import deepcopy
from datetime import datetime
import pandas as pd
import numpy as np


def generate_trade_data(start, end, asset, prices, qty, duration, meta={}):
    size = int((end - start).total_seconds() // duration)
    rng = np.random.RandomState(1)
    noise = rng.rand(size) * 0.1 + 1
    start_price, end_price = prices
    buy = True
    orders = []
    observations = []
    comments = []
    words = ['foo bar eggs', 'Zzzzzzzzz', 'Lorem impus', 'dolor sit amet']
    for i in range(size):
        time = start.timestamp() + i * duration
        price = start_price + (end_price - start_price) \
            * (time - start.timestamp()) \
            / (end.timestamp() - start.timestamp()) \
            * float(noise[i])

        orders.append({'instrument': asset,
                        'side': 'BUY' if buy else 'SELL',
                        'time': time,
                        'qty': qty,
                        'order_type': 'MARKET',
                        'order_status': 'FILLED',
                        'price': round(price,2),
                        'meta': meta.copy(),
                        'tif': None})
        if i % 3 == 0:
            comments.append({'time': time, 'comment': rng.choice(words, 1)[0]})
        observations.append({'time': time, 'observations':{f"{asset}_price": price}})
        buy = not buy
    return orders, observations, comments


def generate_positions(orders, start, end, init_balance, record_duration):
    positions = []
    balance = init_balance
    next_time = (start.timestamp() // record_duration + 1) * record_duration
    i = 0
    cur_position = {}
    for order in orders:
        if order['time'] > next_time:
            positions.append({'time': next_time, 'position': deepcopy(cur_position)})
            next_time = (next_time // record_duration + 1) * record_duration
        if order['instrument'] not in cur_position:
            cur_position[order['instrument']] = {'qty': 0, 'value': 0}
        sign = 1 if order['side'] == 'BUY' else -1
        cur_position[order['instrument']]['qty'] += order['qty'] * sign
        cur_position[order['instrument']]['value'] = cur_position[order['instrument']]['qty'] * order['price']
        balance -= order['qty'] * order['price'] * sign
        cur_position['USD'] = {'qty': balance, 'value': balance}
    return positions


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

buffer = {}
def _insert(collection, data):
    buffer.setdefault(collection, []).append(data)

def _flush():
    print('# collections:', len(buffer.keys()))
    for collection, data in buffer.items():
        print('inserting', collection+"...")
        client[DB_NAME][collection].insert_many(data)
    buffer.clear()

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
        'exposure_table': modelfactory.deconstruct(exposure_table)})

def push_strategydef(name, version, options, meta=None):
    o = StrategyDefinition(
            name=name,
            version=version,
            options=options,
            meta=meta or {})
    _insert("strategy_definitions", modelfactory.deconstruct(o))

def push_order(instrument, side, qty, order_type, t, order_status=order_status.FILLED, price=None, tif=None, account_id=None, meta=None):
    meta = meta or {}
    assert account_id is not None
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
    acc_scl = [5, 10, 20]
    ST1 = to_strategy_uri('strategy1', {'asset':'AAPL', 'ncandle': 3})
    ST2 = to_strategy_uri('strategy2', {'asset':'SPY', 'letter': 'A'})
    ST3 = to_strategy_uri('strategy3', {'asset':'TSLA', 'ncandle': 0.3})

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

    start = datetime(2023, 8, 1)
    end = datetime.now()
    T2 = start.timestamp()
    full_pos = {}
    historic_pos = {}
    for i in range(1, 4):
        historic_pos[str(seed.account_id(i-1))] = []
        exposure_table = ExposureTable(
                {ST1:Exposure(alloc={'AAPL': 0.3}, buffer={}),
                 ST2:Exposure(alloc={'SPY': -1}, buffer={}),
                 ST3:Exposure(alloc={'TESLA': 1}, buffer={})},
                {ST1: 0.5, ST2: 0.3, ST3: 0.1})
        push_exposure_table(account_id=seed.account_id(i), exposure_table=exposure_table)

        push_trader(seed.account_id(i), ST1, T2, seed.trader_id(1 + (i-1)*3))
        push_trader(seed.account_id(i), ST2, T2, seed.trader_id(2 + (i-1)*3))
        push_trader(seed.account_id(i), ST3, T2, seed.trader_id(3 + (i-1)*3))

        last_positions = []
        #Strategy 1
        duration = 60*7
        record_duration = 600
        init_balance = 5000 * acc_scl[i-1]
        trader_id = seed.trader_id(1 + (i-1)*3)
        qty = acc_scl[i-1]
        meta = {'trader_id': trader_id}
        orders1, obs1, comm1 = generate_trade_data(start, end, 'AAPL', (100,200), qty, duration, meta)
        orders2, obs2, comm2 = generate_trade_data(start, end, 'SPY', (300,400), qty, duration, meta)
        orders = (orders1 + orders2)
        orders.sort(key=lambda x: x['time'])
        for order in orders:
            push_order(Instrument.stock(order['instrument'], 'USD'), order['side'],
                order['qty'], order['order_type'], account_id=seed.account_id(i),
                t=order['time'], meta=order['meta'])
        observations = (obs1 + obs2)
        observations.sort(key=lambda x: x['time'])
        for obs in observations:
            push_trader_observation(trader_id, deepcopy(obs))
        comments = (comm1 + comm2)
        comments.sort(key=lambda x: x['time'])
        for comm in comments:
            push_trader_comment(trader_id, deepcopy(comm))
        
        positions = generate_positions(orders, start, end, init_balance, record_duration)
        historic_pos[str(seed.account_id(i-1))].append(positions)
        last_positions.append(positions[-1])

        #Strategy 2
        duration = 60*8
        trader_id = seed.trader_id(2 + (i-1)*3)
        init_balance = 5000 * acc_scl[i-1]
        qty = acc_scl[i-1]
        meta = {'trader_id': trader_id}
        orders1, obs1, comm1 = generate_trade_data(start, end, 'AAPL', (100,200), qty, duration, meta)
        orders2, obs2, comm2 = generate_trade_data(start, end, 'MSFT', (200,300), qty, duration, meta)
        orders = (orders1 + orders2)
        orders.sort(key=lambda x: x['time'])
        for order in orders:
            push_order(Instrument.stock(order['instrument'], 'USD'), order['side'],
                order['qty'], order['order_type'], account_id=seed.account_id(i),
                t=order['time'], meta=order['meta'])
        observations = (obs1 + obs2)
        observations.sort(key=lambda x: x['time'])
        for obs in observations:
            push_trader_observation(trader_id, deepcopy(obs))
        comments = (comm1 + comm2)
        comments.sort(key=lambda x: x['time'])
        for comm in comments:
            push_trader_comment(trader_id, deepcopy(comm))
        
        positions = generate_positions(orders, start, end, init_balance, record_duration)
        historic_pos[str(seed.account_id(i-1))].append(positions)
        last_positions.append(positions[-1])

        #Strategy 3
        duration = 60*7
        trader_id = seed.trader_id(3 + (i-1)*3)
        init_balance = 5000 * acc_scl[i-1]
        qty = acc_scl[i-1] * 2
        meta = {'trader_id': trader_id}
        orders1, obs1, comm1 = generate_trade_data(start, end, 'AAPL', (100,200), qty, duration, meta)
        orders2, obs2, comm2 = [], [], []
        orders = (orders1 + orders2)
        orders.sort(key=lambda x: x['time'])
        for order in orders:
            push_order(Instrument.stock(order['instrument'], 'USD'), order['side'],
                order['qty'], order['order_type'], account_id=seed.account_id(i),
                t=order['time'], meta=order['meta'])
        observations = (obs1 + obs2)
        observations.sort(key=lambda x: x['time'])
        for obs in observations:
            push_trader_observation(trader_id, deepcopy(obs))
        comments = (comm1 + comm2)
        comments.sort(key=lambda x: x['time'])
        for comm in comments:
            push_trader_comment(trader_id, deepcopy(comm))
        
        positions = generate_positions(orders, start, end, init_balance, record_duration)
        historic_pos[str(seed.account_id(i-1))].append(positions)
        last_positions.append(positions[-1])

        full_acc_pos = {}
        for pos in last_positions:
            for asset, info in pos['position'].items():
                full_acc_pos.setdefault(asset, 0)
                full_acc_pos[asset] += info['qty']
        full_pos[str(seed.account_id(i-1))] = full_acc_pos
        
    snapshots = []
    account_ids = list(historic_pos.keys())
    trader_size = len(historic_pos[account_ids[0]])
    history_size = len(historic_pos[account_ids[0]][0])
    for i in range(history_size):
        snapshot = {'time': None, 'positions':{}}
        for acc_id in account_ids:
            positions = [
                    historic_pos[acc_id][k][i] 
                    for k in range(trader_size)]
            full_pos = {}
            t = None
            for pos in positions:
                t = pos['time']
                for asset, info in pos['position'].items():
                    full_pos.setdefault(asset, {'qty': 0, 'value': 0})
                    full_pos[asset]['qty']+=info['qty']
                    full_pos[asset]['value']+=info['value']
            snapshot['time'] = t
            snapshot['positions'][acc_id] = full_pos
        push_portfolio_snapshot(seed.pm_id(1), snapshot['time'], snapshot['positions'])

if __name__ == "__main__":
    main()
    print('inserting')
    _flush()

