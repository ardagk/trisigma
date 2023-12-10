import random
import asyncio
from .common import TestResultContainer
from tests.util import statics
from tests.mock.brokerage_adapter import MockBrokerageAdapter
from tests.mock.portfolio_repository import MockPortfolioRepository
from trisigma.app.usecase import OrderModificationUseCase
from trisigma.domain.brokerage import FinancialAccount
from trisigma.domain.portfolio import (
        Exposure, ExposureTable, PortfolioManager)

loop = asyncio.get_event_loop()
#test runner
ACCOUNT_ID = 123
PORTFOLIO_MANAGER_ID = 555
ACCOUNT_NAME = 'demopaper'
ACCOUNT_PLATFORM = 'ibkr'
PRICES = dict(
    AAPL = 100,
    SPY = 250.0,
    MSFT = 200.0,
    TSLA = 300.0)


def order_modification_test_runner(
    generic_exposure_table, position, partition, signal_id, changes, fl=True):
    global floor
    global allocation_table
    global portfolio
    global prices
    global exposure_table
    global financial_account
    global portfolio_manager

    floor = fl

    prices = PRICES.copy()

    portfolio = position.copy()
    portfolio = {
        asset: {'qty': position[asset], 'value': prices[asset] * position[asset]}
        if asset != 'USD' else {'qty': position[asset], 'value': position[asset]}
        for asset in position}

    random.seed(0)
    for strategy, rest in generic_exposure_table.items():
        for _signal_id, details in rest['open'].items():
            ref = hash(random.randint(0, 100000))
            rest['open'][_signal_id] = details | dict(ref=ref)

    exposures = {
        strategy: Exposure(rest['alloc'], rest['open'])
        for strategy, rest in generic_exposure_table.items()}
    weights = {
        strategy: rest['weight']
        for strategy, rest in generic_exposure_table.items()}
    exposure_table = ExposureTable(exposures, weights)

    financial_account = FinancialAccount(
        account_id=ACCOUNT_ID, portfolio_manager_id=PORTFOLIO_MANAGER_ID,
        name=ACCOUNT_NAME, platform=ACCOUNT_PLATFORM, paper=True)

    portfolio_manager = PortfolioManager(
                portfolio_manager_id = 555,
                name = 'demo', meta = {})

    account_id = ACCOUNT_ID
    portfolio_manager_id = PORTFOLIO_MANAGER_ID

    statics['floor'] = floor
    statics['portfolio'] = portfolio
    statics['prices'] = prices
    statics['exposure_table'] = exposure_table
    statics['financial_account'] = financial_account
    statics['portfolio_manager'] = portfolio_manager

    usecase = OrderModificationUseCase(
        portfolio_repository=MockPortfolioRepository(),
        brokerage_adapter=MockBrokerageAdapter())
    loop.run_until_complete(usecase.run(account_id, signal_id, changes))
    return TestResultContainer(usecase, init_table=generic_exposure_table)

def test_case_1():
    """Long open position modified to a higher exposure
    """
    generic_exposure_table = {
        "A": dict(alloc={}, weight=0.5, open={
            1000: {'asset': 'AAPL', 'filled': 0, 'total': 0.2, 'method': {}},
            1001: {'asset': 'AAPL', 'filled': 0, 'total': 0.2, 'method': {}},
        }),
        "B": dict(alloc={'AAPL': 1}, weight=0.2, open={}),
        "C": dict(alloc={'AAPL': 1}, weight=0.3, open={})}
    position = {
        'USD': 500,
        'AAPL': 5,
        'SPY': 0}
    partition = 'A'
    signal_id = 1000
    changes = {'amount': 0.4}
    res = order_modification_test_runner(
        generic_exposure_table, position,
        partition, signal_id, changes)
    #ensure that only partition: 'A' is removed
    assert res.table['A']['alloc'] == {}
    assert res.table['B']['alloc'] == {'AAPL': 1}
    assert res.table['C']['alloc'] == {'AAPL': 1}
    assert res.table['A']['open'][1000]['total'] == 0.4
    assert res.table['A']['open'][1001]['total'] == 0.2
    assert len(res.table.keys()) == 3
    #ensure that all orders are cancelled
    assert len(res.cancelled_ids) == 0
    #ensure that no orders are modified
    assert len(res.modified_orders) == 1
    assert res.modified_orders[0][1] == {'qty': 2}
    #ensure that no new orders submitted
    assert len(res.submitted_orders) == 0

def test_case_2():
    """Long open position modified to a lower exposure
    """
    generic_exposure_table = {
        "A": dict(alloc={}, weight=0.5, open={
            1000: {'asset': 'AAPL', 'filled': 0, 'total': 0.4, 'method': {}},
            1001: {'asset': 'AAPL', 'filled': 0, 'total': 0.2, 'method': {}},
        }),
        "B": dict(alloc={'AAPL': 1}, weight=0.2, open={}),
        "C": dict(alloc={'AAPL': 1}, weight=0.3, open={})}
    position = {
        'USD': 500,
        'AAPL': 5,
        'SPY': 0}
    partition = 'A'
    signal_id = 1000
    changes = {'amount': 0.2}
    res = order_modification_test_runner(
        generic_exposure_table, position,
        partition, signal_id, changes)
    #ensure that only partition: 'A' is removed
    assert res.table['A']['alloc'] == {}
    assert res.table['B']['alloc'] == {'AAPL': 1}
    assert res.table['C']['alloc'] == {'AAPL': 1}
    assert res.table['A']['open'][1000]['total'] == 0.2
    assert res.table['A']['open'][1001]['total'] == 0.2
    assert len(res.table.keys()) == 3
    #ensure that all orders are cancelled
    assert len(res.cancelled_ids) == 0
    #ensure that no orders are modified
    assert len(res.modified_orders) == 1
    assert res.modified_orders[0][1] == {'qty': 1}
    #ensure that no new orders submitted
    assert len(res.submitted_orders) == 0

def test_case_3():
    """Short open position modified to a higher exposure
    """
    generic_exposure_table = {
        "A": dict(alloc={}, weight=0.5, open={
            1000: {'asset': 'AAPL', 'filled': 0, 'total': -0.2, 'method': {}},
            1001: {'asset': 'SPY', 'filled': 0, 'total': 0.2, 'method': {}},
        }),
        "B": dict(alloc={'AAPL': 1}, weight=0.2, open={}),
        "C": dict(alloc={'AAPL': 1}, weight=0.3, open={})}
    position = {
        'USD': 500,
        'AAPL': 5,
        'SPY': 0}
    partition = 'A'
    signal_id = 1000
    changes = {'amount': -0.4}
    res = order_modification_test_runner(
        generic_exposure_table, position,
        partition, signal_id, changes)
    #ensure that only partition: 'A' is removed
    assert res.table['A']['alloc'] == {}
    assert res.table['B']['alloc'] == {'AAPL': 1}
    assert res.table['C']['alloc'] == {'AAPL': 1}
    assert res.table['A']['open'][1000]['total'] == -0.4
    assert res.table['A']['open'][1001]['total'] == 0.2
    assert len(res.table.keys()) == 3
    #ensure that all orders are cancelled
    assert len(res.cancelled_ids) == 0
    #ensure that no orders are modified
    assert len(res.modified_orders) == 1
    assert res.modified_orders[0][1] == {'qty': 2}
    #ensure that no new orders submitted
    assert len(res.submitted_orders) == 0

def test_case_4():
    """Short open position modified to a lower exposure
    """
    generic_exposure_table = {
        "A": dict(alloc={}, weight=0.5, open={
            1000: {'asset': 'AAPL', 'filled': 0, 'total': -0.4, 'method': {}},
            1001: {'asset': 'SPY', 'filled': 0, 'total': 0.2, 'method': {}},
        }),
        "B": dict(alloc={'AAPL': 1}, weight=0.2, open={}),
        "C": dict(alloc={'AAPL': 1}, weight=0.3, open={})}
    position = {
        'USD': 500,
        'AAPL': 5,
        'SPY': 0}
    partition = 'A'
    signal_id = 1000
    changes = {'amount': -0.2}
    res = order_modification_test_runner(
        generic_exposure_table, position,
        partition, signal_id, changes)
    #ensure that only partition: 'A' is removed
    assert res.table['A']['alloc'] == {}
    assert res.table['B']['alloc'] == {'AAPL': 1}
    assert res.table['C']['alloc'] == {'AAPL': 1}
    assert res.table['A']['open'][1000]['total'] == -0.2
    assert res.table['A']['open'][1001]['total'] == 0.2
    assert len(res.table.keys()) == 3
    #ensure that all orders are cancelled
    assert len(res.cancelled_ids) == 0
    #ensure that no orders are modified
    assert len(res.modified_orders) == 1
    assert res.modified_orders[0][1] == {'qty': 1}
    #ensure that no new orders submitted
    assert len(res.submitted_orders) == 0

