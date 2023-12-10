import random
import asyncio
from contextlib import contextmanager
from .common import TestResultContainer
from tests.util import statics
from tests.mock.brokerage_adapter import MockBrokerageAdapter
from tests.mock.portfolio_repository import MockPortfolioRepository
from tests.mock.order_repository import MockOrderRepository
from trisigma.app.usecase import OrderPlacementUseCase
from trisigma.domain.brokerage import FinancialAccount
from trisigma.domain.portfolio import (
        Exposure, ExposureTable, PortfolioManager)
from trisigma.domain.trading import OrderSignal

loop = asyncio.get_event_loop()

#test runner
PI = 2
PRICES = dict(
    AAPL = 100,
    SPY = 250.0,
    MSFT = 200.0,
    TSLA = 300.0)


@contextmanager
def global_settings(partitions, pos, price, fl, key, worth = 4000):
    global floor
    global allocation_table
    global portfolio
    global position
    global prices
    global exposure_table
    global financial_account
    global portfolio_manager

    floor = fl

    prices = PRICES.copy()
    prices['AAPL'] = price
    position = {
        'AAPL': pos,
        'SPY': 4, 
        'USD': worth - ((pos*price) + 1000)}
    prices = PRICES.copy()
    portfolio = {
        asset: {'qty': position[asset], 'value': prices[asset] * position[asset]}
        if asset != 'USD' else {'qty': position[asset], 'value': position[asset]}
        for asset in position}

    exposures = {strategy: Exposure(rest['alloc'], rest['open']) for strategy, rest in partitions.items()}
    weights = {strategy: rest['weight'] for strategy, rest in partitions.items()}
    exposure_table = ExposureTable(exposures, weights)


    financial_account = FinancialAccount(
        account_id=123, portfolio_manager_id=555, name='demopaper', platform='ibkr', paper=True)

    portfolio_manager = PortfolioManager(
                portfolio_manager_id = 555,
                name = 'demo', meta = {})

    account_id = 123
    portfolio_manager_id = 555

    statics['floor'] = floor
    statics['portfolio'] = portfolio
    statics['prices'] = prices
    statics['exposure_table'] = exposure_table
    statics['financial_account'] = financial_account
    statics['portfolio_manager'] = portfolio_manager
    yield

def order_signal_factory(asset, amount, method, partition):
    return OrderSignal(
            asset=asset,
            amount=amount,
            method=method,
            trader_id=888,
            partition=partition)


def test_case_1():
    #test case - external exp half short reverse
    with global_settings(
        {"A": dict(alloc={'SPY': 1.0}, weight=0.25, open={}),
         "B": dict(alloc={'AAPL': -0.2}, weight=0.2, open={}),
         "C": dict(alloc={'AAPL': -0.5}, weight=0.5, open={})},
        pos=-10, price=100, fl=False, key='main'):
        asset = 'AAPL'
        exp = -0.5
        strategy = 'C'
        expected_qty = 11.6
        expected_quote_qty = 1160
        expected_side = 'SELL'

        usecase = OrderPlacementUseCase(
            portfolio_repository=MockPortfolioRepository(),
            order_repository=MockOrderRepository(),
            brokerage_adapter=MockBrokerageAdapter())
        order_signal = order_signal_factory(asset, exp, {'order_type': 'MARKET'}, strategy)

        ref = loop.run_until_complete(usecase.run(123, order_signal))
        res = TestResultContainer(usecase, init_table=exposure_table)

        assert bool(ref)
        assert len(usecase.order_repo.calls) == 1 #pyright: ignore
        assert res.submitted_orders[0] == (
            asset, expected_side, expected_qty, 'MARKET', None)

        assert usecase.brokerage_adapter.calls[1] == ('quantify_asset', (asset, expected_quote_qty)) #pyright: ignore
        assert len(usecase.portfolio_repo.calls) == 2 #pyright: ignore

def test_case_2():
    #test case - external exp half long
    with global_settings(
        {"A": dict(alloc={'SPY': 1.0}, weight=0.25, open={}),
         "B": dict(alloc={'AAPL': 0.2}, weight=0.2, open={}),
         "C": dict(alloc={'AAPL': 0.5}, weight=0.5, open={})},
        pos=11.6, price=100, fl=False, key='main'):
        asset = 'AAPL'
        exp = 0.5
        strategy = 'C'
        expected_qty = 10
        expected_quote_qty = 1000
        expected_side = 'BUY'

        usecase = OrderPlacementUseCase(
            portfolio_repository=MockPortfolioRepository(),
            order_repository=MockOrderRepository(),
            brokerage_adapter=MockBrokerageAdapter())

        order_signal = order_signal_factory(asset, exp, {'order_type': 'MARKET'}, strategy)
        ref = loop.run_until_complete(usecase.run(123, order_signal))
        res = TestResultContainer(usecase, init_table=exposure_table)

        assert bool(ref)
        assert len(usecase.order_repo.calls) == 1 #pyright: ignore
        assert res.submitted_orders[0] == (
            asset, expected_side, expected_qty, 'MARKET', None)

        assert usecase.brokerage_adapter.calls[1] == ('quantify_asset', (asset, expected_quote_qty)) #pyright: ignore
        assert len(usecase.portfolio_repo.calls) == 2 #pyright: ignore

def test_case_3():
    #test case - external exp half long w/ poslack
    with global_settings(
        {"A": dict(alloc={'SPY': 1.0}, weight=0.25, open={}),
         "B": dict(alloc={'AAPL': 0.2}, weight=0.2, open={}),
         "C": dict(alloc={'AAPL': 0.5}, weight=0.5, open={})},
        pos=10, price=100, fl=False, key='main'):
        asset = 'AAPL'
        exp = 0.5
        strategy = 'C'
        expected_qty = 11.6
        expected_quote_qty = 1160
        expected_side = 'BUY'

        usecase = OrderPlacementUseCase(
            portfolio_repository=MockPortfolioRepository(),
            order_repository=MockOrderRepository(),
            brokerage_adapter=MockBrokerageAdapter())
        order_signal = order_signal_factory(asset, exp, {'order_type': 'MARKET'}, strategy)
        ref = loop.run_until_complete(usecase.run(123, order_signal))
        res = TestResultContainer(usecase, init_table=exposure_table)

        assert bool(ref)
        assert len(usecase.order_repo.calls) == 1 #pyright: ignore
        assert res.submitted_orders[0] == (
            asset, expected_side, expected_qty, 'MARKET', None)

        assert usecase.brokerage_adapter.calls[1] == ('quantify_asset', (asset, expected_quote_qty)) #pyright: ignore
        assert len(usecase.portfolio_repo.calls) == 2 #pyright: ignore

def test_case_4():
    #test case - external exp half long w/ extshort
    with global_settings(
        {"A": dict(alloc={'SPY': 1.0}, weight=0.25, open={}),
         "B": dict(alloc={'AAPL': -0.2}, weight=0.2, open={}),
         "C": dict(alloc={'AAPL': 0.5}, weight=0.5, open={})},
        pos=10, price=100, fl=False, key='main'):
        asset = 'AAPL'
        exp = 0.5
        strategy = 'C'
        expected_qty = 8.4
        expected_quote_qty = 840
        expected_side = 'BUY'

        usecase = OrderPlacementUseCase(
            portfolio_repository=MockPortfolioRepository(),
            order_repository=MockOrderRepository(),
            brokerage_adapter=MockBrokerageAdapter())
        order_signal = order_signal_factory(asset, exp, {'order_type': 'MARKET'}, strategy)
        ref = loop.run_until_complete(usecase.run(123, order_signal))
        res = TestResultContainer(usecase, init_table=exposure_table)

        assert bool(ref)
        assert len(usecase.order_repo.calls) == 1 #pyright: ignore
        assert res.submitted_orders[0] == (
            asset, expected_side, expected_qty, 'MARKET', None)

        assert usecase.brokerage_adapter.calls[1] == ('quantify_asset', (asset, expected_quote_qty)) #pyright: ignore
        assert len(usecase.portfolio_repo.calls) == 2 #pyright: ignore

def test_case_5():
    #test case - external exp half long w/ ext full short
    with global_settings(
        {"A": dict(alloc={'SPY': 1.0}, weight=0.25, open={}),
         "B": dict(alloc={'AAPL': -1}, weight=0.2, open={}),
         "C": dict(alloc={'AAPL': 0.5}, weight=0.5, open={})},
        pos=10, price=100, fl=False, key='main'):
        asset = 'AAPL'
        exp = 0.5
        strategy = 'C'
        expected_qty = 2
        expected_quote_qty = 200
        expected_side = 'BUY'

        usecase = OrderPlacementUseCase(
            portfolio_repository=MockPortfolioRepository(),
            order_repository=MockOrderRepository(),
            brokerage_adapter=MockBrokerageAdapter())
        order_signal = order_signal_factory(asset, exp, {'order_type': 'MARKET'}, strategy)
        ref = loop.run_until_complete(usecase.run(123, order_signal))
        res = TestResultContainer(usecase, init_table=exposure_table)

        assert bool(ref)
        assert len(usecase.order_repo.calls) == 1 #pyright: ignore
        assert res.submitted_orders[0] == (
            asset, expected_side, expected_qty, 'MARKET', None)

        assert usecase.brokerage_adapter.calls[1] == ('quantify_asset', (asset, expected_quote_qty)) #pyright: ignore
        assert len(usecase.portfolio_repo.calls) == 2 #pyright: ignore

def test_case_6():
    #test case - external exp slight long
    with global_settings(
        {"A": dict(alloc={'SPY': 1.0}, weight=0.25, open={}),
         "B": dict(alloc={'AAPL': 0.2}, weight=0.2, open={}),
         "C": dict(alloc={'AAPL': 0.5}, weight=0.5, open={})},
        pos=10, price=100, fl=False, key='main'):
        asset = 'AAPL'
        exp = 0.232
        strategy = 'C'
        expected_qty = 6.24
        expected_quote_qty = 624
        expected_side = 'BUY'

        usecase = OrderPlacementUseCase(
            portfolio_repository=MockPortfolioRepository(),
            order_repository=MockOrderRepository(),
            brokerage_adapter=MockBrokerageAdapter())
        order_signal = order_signal_factory(asset, exp, {'order_type': 'MARKET'}, strategy)
        ref = loop.run_until_complete(usecase.run(123, order_signal))
        res = TestResultContainer(usecase, init_table=exposure_table)

        assert bool(ref)
        assert len(usecase.order_repo.calls) == 1 #pyright: ignore
        assert res.submitted_orders[0] == (
            asset, expected_side, expected_qty, 'MARKET', None)

        assert usecase.brokerage_adapter.calls[1] == ('quantify_asset', (asset, expected_quote_qty)) #pyright: ignore
        assert len(usecase.portfolio_repo.calls) == 2 #pyright: ignore

def test_case_7():
    #test case - external exp arbit long
    with global_settings(
        {"A": dict(alloc={'SPY': 1.0}, weight=0.25, open={}),
         "B": dict(alloc={'AAPL': 0.2}, weight=0.2, open={}),
         "C": dict(alloc={'AAPL': 0.5}, weight=0.5, open={})},
        pos=10, price=100, fl=False, key='main'):
        asset = 'AAPL'
        exp = 0.232
        strategy = 'C'
        expected_qty = 6.24
        expected_quote_qty = 624
        expected_side = 'BUY'

        usecase = OrderPlacementUseCase(
            portfolio_repository=MockPortfolioRepository(),
            order_repository=MockOrderRepository(),
            brokerage_adapter=MockBrokerageAdapter())
        order_signal = order_signal_factory(asset, exp, {'order_type': 'MARKET'}, strategy)
        ref = loop.run_until_complete(usecase.run(123, order_signal))
        res = TestResultContainer(usecase, init_table=exposure_table)

        assert bool(ref)
        assert len(usecase.order_repo.calls) == 1 #pyright: ignore
        assert res.submitted_orders[0] == (
            asset, expected_side, expected_qty, 'MARKET', None)

        assert usecase.brokerage_adapter.calls[1] == ('quantify_asset', (asset, expected_quote_qty)) #pyright: ignore
        assert len(usecase.portfolio_repo.calls) == 2 #pyright: ignore

def test_case_8():
    #test case - arbit long
    with global_settings(
        {"A": dict(alloc={'SPY': 1.0}, weight=0.25, open={}),
         "B": dict(alloc={'AAPL': 0.0}, weight=0.2, open={}),
         "C": dict(alloc={'AAPL': 0.5}, weight=0.5, open={})},
        pos=10, price=100, fl=False, key='main'):
        asset = 'AAPL'
        exp = 0.35
        strategy = 'C'
        expected_qty = 7
        expected_quote_qty = 700
        expected_side = "BUY"

        usecase = OrderPlacementUseCase(
            portfolio_repository=MockPortfolioRepository(),
            order_repository=MockOrderRepository(),
            brokerage_adapter=MockBrokerageAdapter())
        order_signal = order_signal_factory(asset, exp, {'order_type': 'MARKET'}, strategy)
        ref = loop.run_until_complete(usecase.run(123, order_signal))
        res = TestResultContainer(usecase, init_table=exposure_table)

        assert bool(ref)
        assert len(usecase.order_repo.calls) == 1 #pyright: ignore
        assert res.submitted_orders[0] == (
            asset, expected_side, expected_qty, 'MARKET', None)

        assert usecase.brokerage_adapter.calls[1] == ('quantify_asset', (asset, expected_quote_qty)) #pyright: ignore
        assert len(usecase.portfolio_repo.calls) == 2 #pyright: ignore

def test_case_9():
    #test case - sell long
    with global_settings(
        {"A": dict(alloc={'SPY': 1.0}, weight=0.25, open={}),
         "B": dict(alloc={'AAPL': 0.0}, weight=0.2, open={}),
         "C": dict(alloc={'AAPL': 0.5}, weight=0.5, open={})},
        pos=10, price=100, fl=False, key='main'):
        asset = 'AAPL'
        exp = -0.141
        strategy = 'C'
        expected_qty = 2.82
        expected_quote_qty = 282
        expected_side = 'SELL'

        usecase = OrderPlacementUseCase(
            portfolio_repository=MockPortfolioRepository(),
            order_repository=MockOrderRepository(),
            brokerage_adapter=MockBrokerageAdapter())
        order_signal = order_signal_factory(asset, exp, {'order_type': 'MARKET'}, strategy)
        ref = loop.run_until_complete(usecase.run(123, order_signal))
        res = TestResultContainer(usecase, init_table=exposure_table)

        assert bool(ref)
        assert len(usecase.order_repo.calls) == 1 #pyright: ignore
        assert res.submitted_orders[0] == (
            asset, expected_side, expected_qty, 'MARKET', None)

        assert usecase.brokerage_adapter.calls[1] == ('quantify_asset', (asset, expected_quote_qty)) #pyright: ignore
        assert len(usecase.portfolio_repo.calls) == 2 #pyright: ignore

def test_case_10():
    #test case - neutral
    with global_settings(
        {"A": dict(alloc={'SPY': 1.0}, weight=0.25, open={}),
         "B": dict(alloc={'AAPL': 0.0}, weight=0.2, open={}),
         "C": dict(alloc={'AAPL': 0.5}, weight=0.5, open={})},
        pos=10, price=100, fl=False, key='main'):
        asset = 'AAPL'
        exp = -0.5
        strategy = 'C'
        expected_qty = 10
        expected_quote_qty = 1000
        expected_side = 'SELL'

        usecase = OrderPlacementUseCase(
            portfolio_repository=MockPortfolioRepository(),
            order_repository=MockOrderRepository(),
            brokerage_adapter=MockBrokerageAdapter())
        order_signal = order_signal_factory(asset, exp, {'order_type': 'MARKET'}, strategy)
        ref = loop.run_until_complete(usecase.run(123, order_signal))
        res = TestResultContainer(usecase, init_table=exposure_table)

        assert bool(ref)
        assert len(usecase.order_repo.calls) == 1 #pyright: ignore
        assert res.submitted_orders[0] == (
            asset, expected_side, expected_qty, 'MARKET', None)

        assert usecase.brokerage_adapter.calls[1] == ('quantify_asset', (asset, expected_quote_qty)) #pyright: ignore
        assert len(usecase.portfolio_repo.calls) == 2 #pyright: ignore

def test_case_11():
    #test case - arbit short
    with global_settings(
        {"A": dict(alloc={'SPY': 1.0}, weight=0.25, open={}),
         "B": dict(alloc={'AAPL': 0.0}, weight=0.2, open={}),
         "C": dict(alloc={'AAPL': 0.5}, weight=0.5, open={})},
        pos=10, price=100, fl=False, key='main'):
        asset = 'AAPL'
        exp = -0.6
        strategy = 'C'
        expected_qty = 12
        expected_quote_qty = 1200
        expected_side = 'SELL'

        usecase = OrderPlacementUseCase(
            portfolio_repository=MockPortfolioRepository(),
            order_repository=MockOrderRepository(),
            brokerage_adapter=MockBrokerageAdapter())
        order_signal = order_signal_factory(asset, exp, {'order_type': 'MARKET'}, strategy)
        ref = loop.run_until_complete(usecase.run(123, order_signal))
        res = TestResultContainer(usecase, init_table=exposure_table)

        assert bool(ref)
        assert len(usecase.order_repo.calls) == 1 #pyright: ignore
        assert res.submitted_orders[0] == (
            asset, expected_side, expected_qty, 'MARKET', None)

        assert usecase.brokerage_adapter.calls[1] == ('quantify_asset', (asset, expected_quote_qty)) #pyright: ignore
        assert len(usecase.portfolio_repo.calls) == 2 #pyright: ignore

def test_case_12():
    #test case - full short
    with global_settings(
        {"A": dict(alloc={'SPY': 1.0}, weight=0.25, open={}),
         "B": dict(alloc={'AAPL': 0.0}, weight=0.2, open={}),
         "C": dict(alloc={'AAPL': 0.5}, weight=0.5, open={})},
        pos=10, price=100, fl=False, key='main'):
        asset = 'AAPL'
        exp = -1.5
        strategy = 'C'
        expected_qty = 30
        expected_quote_qty = 3000
        expected_side = 'SELL'

        usecase = OrderPlacementUseCase(
            portfolio_repository=MockPortfolioRepository(),
            order_repository=MockOrderRepository(),
            brokerage_adapter=MockBrokerageAdapter())
        order_signal = order_signal_factory(asset, exp, {'order_type': 'MARKET'}, strategy)
        ref = loop.run_until_complete(usecase.run(123, order_signal))

        assert bool(ref)
        assert len(usecase.order_repo.calls) == 1 #pyright: ignore
        assert usecase.brokerage_adapter.calls[PI][1] == ( #pyright:ignore
                asset, expected_side, expected_qty, {'order_type': 'MARKET'})
        assert usecase.brokerage_adapter.calls[1] == ('quantify_asset', (asset, expected_quote_qty)) #pyright: ignore
        assert len(usecase.portfolio_repo.calls) == 2 #pyright: ignore

def test_case_13():
    #test case - full short - LIMIT
    with global_settings(
        {"A": dict(alloc={'SPY': 1.0}, weight=0.25, open={}),
         "B": dict(alloc={'AAPL': 0.0}, weight=0.2, open={}),
         "C": dict(alloc={'AAPL': 0.5}, weight=0.5, open={})},
        pos=10, price=100, fl=False, key='main'):
        asset = 'AAPL'
        exp = -1.5
        curexp = 0.5
        strategy = 'C'
        expected_qty = 30
        expected_quote_qty = 3000
        expected_side = 'SELL'

        usecase = OrderPlacementUseCase(
            portfolio_repository=MockPortfolioRepository(),
            order_repository=MockOrderRepository(),
            brokerage_adapter=MockBrokerageAdapter())
        order_signal = order_signal_factory(asset, exp, {'order_type': 'LIMIT', 'price':100}, strategy)
        ref = loop.run_until_complete(usecase.run(123, order_signal))

        assert bool(ref)
        assert len(usecase.order_repo.calls) == 1 #pyright: ignore
        assert usecase.brokerage_adapter.calls[PI][1] == ( #pyright:ignore
            asset, expected_side, expected_qty, {'order_type': 'LIMIT', 'price':100})

        assert usecase.brokerage_adapter.calls[1] == ('quantify_asset', (asset, expected_quote_qty)) #pyright: ignore
        assert len(usecase.portfolio_repo.calls) == 2 #pyright: ignore

def test_case_14():
    #test case - arbit short - LIMIT
    with global_settings(
        {"A": dict(alloc={'SPY': 1.0}, weight=0.25, open={}),
         "B": dict(alloc={'AAPL': 0.0}, weight=0.2, open={}),
         "C": dict(alloc={'AAPL': 0.5}, weight=0.5, open={})},
        pos=10, price=100, fl=False, key='main'):
        asset = 'AAPL'
        exp = -0.6
        curexp = 0.5
        strategy = 'C'
        expected_qty = 12
        expected_quote_qty = 1200
        expected_side = 'SELL'

        usecase = OrderPlacementUseCase(
            portfolio_repository=MockPortfolioRepository(),
            order_repository=MockOrderRepository(),
            brokerage_adapter=MockBrokerageAdapter())
        order_signal = order_signal_factory(asset, exp, {'order_type': 'LIMIT', 'price':123}, strategy)
        ref = loop.run_until_complete(usecase.run(123, order_signal))

        assert bool(ref)
        assert len(usecase.order_repo.calls) == 1 #pyright: ignore
        assert usecase.brokerage_adapter.calls[PI][1] == ( #pyright:ignore
            asset, expected_side, expected_qty, {'order_type': 'LIMIT', 'price':123})

        assert usecase.brokerage_adapter.calls[1] == ('quantify_asset', (asset, expected_quote_qty)) #pyright: ignore
        assert len(usecase.portfolio_repo.calls) == 2 #pyright: ignore

def test_case_15():
    #test case - full long
    with global_settings(
        {"A": dict(alloc={'SPY': 1.0}, weight=0.25, open={}),
         "B": dict(alloc={'AAPL': 0.0}, weight=0.2, open={}),
         "C": dict(alloc={'AAPL': 0.5}, weight=0.5, open={})},
        pos=10, price=100, fl=False, key='main'):
        asset = 'AAPL'
        exp = 0.5
        strategy = 'C'
        expected_qty = 10
        expected_quote_qty = 1000
        expected_side = 'BUY'

        usecase = OrderPlacementUseCase(
            portfolio_repository=MockPortfolioRepository(),
            order_repository=MockOrderRepository(),
            brokerage_adapter=MockBrokerageAdapter())
        order_signal = order_signal_factory(asset, exp, {'order_type': 'MARKET'}, strategy)
        ref = loop.run_until_complete(usecase.run(123, order_signal))
        res = TestResultContainer(usecase, init_table=exposure_table)

        assert bool(ref)
        assert len(usecase.order_repo.calls) == 1 #pyright: ignore
        assert res.submitted_orders[0] == (
            asset, expected_side, expected_qty, 'MARKET', None) #pyright:ignore

        assert usecase.brokerage_adapter.calls[1] == ('quantify_asset', (asset, expected_quote_qty)) #pyright: ignore
        assert len(usecase.portfolio_repo.calls) == 2 #pyright: ignore


