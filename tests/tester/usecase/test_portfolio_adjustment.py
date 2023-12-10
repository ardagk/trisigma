import random
import asyncio
from .common import TestResultContainer
from tests.util import statics
from tests.mock.brokerage_adapter import MockBrokerageAdapter
from tests.mock.portfolio_repository import MockPortfolioRepository
from tests.mock.order_repository import MockOrderRepository
from trisigma.app.usecase import PortfolioAdjustmentUseCase
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

def portfolio_adjustment_runner(
    generic_exposure_table, position, strategy_alloc, fl=True):
    global floor
    global allocation_table
    global portfolio
    global prices
    global exposure_table
    global financial_account
    global portfolio_manager

    floor = fl

    prices = PRICES.copy()

    allocation_table = strategy_alloc

    portfolio = position.copy()
    portfolio = {
        asset: {'qty': position[asset], 'value': prices[asset] * position[asset]}
        if asset != 'USD' else {'qty': position[asset], 'value': position[asset]}
        for asset in position}

    random.seed(0)
    for strategy, rest in generic_exposure_table.items():
        for signal_id, details in rest['open'].items():
            ref = hash(random.randint(0, 100000))
            rest['open'][signal_id] = details | dict(ref=ref)

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
    statics['allocation_table'] = allocation_table

    usecase = PortfolioAdjustmentUseCase(
        portfolio_repository=MockPortfolioRepository(),
        order_repository=MockOrderRepository(),
        brokerage_adapter=MockBrokerageAdapter())
    loop.run_until_complete(usecase.run(account_id, portfolio_manager_id))
    return TestResultContainer(usecase, init_table=generic_exposure_table)


def test_case_1():
    """All the belonging orders are cancelled when a partition is removed.
    * Open position in two remaining partitions
    """
    generic_exposure_table = {
        "A": dict(alloc={}, weight=0.25, open={
            1000: {'asset': 'AAPL', 'filled': 0, 'total': 0.2, 'method': {}},
            1001: {'asset': 'AAPL', 'filled': 0, 'total': 0.2, 'method': {}},
            1002: {'asset': 'AAPL', 'filled': 0, 'total': 0.2, 'method': {}},
        }),
        "B": dict(alloc={'AAPL': 1}, weight=0.2, open={}),
        "C": dict(alloc={'AAPL': 1}, weight=0.3, open={})}
    position = {
        'USD': 500,
        'AAPL': 5,
        'SPY': 0}
    strategy_alloc = {
        'B': 0.2,
        'C': 0.3}
    res = portfolio_adjustment_runner(
        generic_exposure_table, position, strategy_alloc)

    #ensure that only partition: 'A' is removed
    assert 'A' not in res.table.keys()
    assert res.table['B']['alloc'] == {'AAPL': 1}
    assert res.table['C']['alloc'] == {'AAPL': 1}
    assert len(res.table.keys()) == 2
    #ensure that all orders are cancelled
    assert len(res.cancelled_ids) == 3
    assert sorted(res.cancelled_ids) == [1000, 1001, 1002] #pyright: ignore
    #ensure that no orders are modified
    assert len(res.modified_orders) == 0
    #ensure that no new orders submitted
    assert len(res.submitted_orders) == 0

def test_case_2():
    """All the belonging orders are cancelled when multiple partitions are removed.
    No open position in any of the removed partitions
    """
    generic_exposure_table = {
        "A": dict(alloc={}, weight=0.25, open={
            1000: {'asset': 'AAPL', 'filled': 0, 'total': 0.2, 'method': {}},
            1001: {'asset': 'SPY', 'filled': 0, 'total': 0.2, 'method': {}},
            1002: {'asset': 'MSFT', 'filled': 0, 'total': 0.2, 'method': {}},
        }),
        "B": dict(alloc={}, weight=0.2, open={
            1003: {'asset': 'TSLA', 'filled': 0, 'total': 0.2, 'method': {}},
            1004: {'asset': 'AAPL', 'filled': 0, 'total': 0.2, 'method': {}},
            1005: {'asset': 'SPY', 'filled': 0, 'total': 0.2, 'method': {}},
        }),
        "C": dict(alloc={}, weight=0.3, open={
            1006: {'asset': 'MSFT', 'filled': 0, 'total': 0.2, 'method': {}},
            1007: {'asset': 'MSFT', 'filled': 0, 'total': 0.2, 'method': {}},
            1008: {'asset': 'AAPL', 'filled': 0, 'total': 0.2, 'method': {}},
        })}
    position = {
        'USD': 2000,
        'AAPL': 0,
        'SPY': 0}
    strategy_alloc = {}
    res = portfolio_adjustment_runner(
        generic_exposure_table, position, strategy_alloc)

    #ensure that only partition: 'A' is removed
    assert 'A' not in res.table.keys()
    assert 'B' not in res.table.keys()
    assert 'C' not in res.table.keys()
    assert len(res.table.keys()) == 0
    #ensure that all orders are cancelled
    assert len(res.cancelled_ids) == 9
    assert sorted(res.cancelled_ids) == list(range(1000,1009)) #pyright: ignore
    #ensure that no orders are modified
    assert len(res.modified_orders) == 0
    #ensure that no new orders submitted
    assert len(res.submitted_orders) == 0

def test_case_3():
    """All the belonging long orders are modified when a partition is upscaled.
    """
    generic_exposure_table = {
        "A": dict(alloc={}, weight=0.25, open={
            1000: {'asset': 'AAPL', 'filled': 0, 'total': 0.5, 'method': {}},
            1001: {'asset': 'AAPL', 'filled': 0, 'total': 0.5, 'method': {}},
        }),
        "B": dict(alloc={'AAPL': 1}, weight=0.2, open={}),
        "C": dict(alloc={'AAPL': 1}, weight=0.3, open={})}
    position = {
        'USD': 500,
        'AAPL': 5,
        'SPY': 0}
    strategy_alloc = {
        'A': 0.5,
        'B': 0.2,
        'C': 0.3}
    res = portfolio_adjustment_runner(
        generic_exposure_table, position, strategy_alloc)

    #ensure that no new partitions added or removed
    assert res.table['A']['alloc'] == {}
    assert res.table['B']['alloc'] == {'AAPL': 1}
    assert res.table['C']['alloc'] == {'AAPL': 1}
    assert len(res.table.keys()) == 3
    #ensure that no orders are cancelled
    assert len(res.cancelled_ids) == 0
    #ensure that no orders are modified
    assert len(res.modified_orders) == 2
    assert res.modified_orders[0] == (1000, {'qty': 2})
    assert res.modified_orders[1] == (1001, {'qty': 2})
    #ensure that no new orders submitted
    assert len(res.submitted_orders) == 0


def test_case_4():
    """All the belonging long orders modified when a partition is downscaled.
    """
    generic_exposure_table = {
        "A": dict(alloc={}, weight=0.5, open={
            1000: {'asset': 'AAPL', 'filled': 0, 'total': 0.5, 'method': {}},
            1001: {'asset': 'AAPL', 'filled': 0, 'total': 0.5, 'method': {}},
        }),
        "B": dict(alloc={'AAPL': 1}, weight=0.2, open={}),
        "C": dict(alloc={'AAPL': 1}, weight=0.3, open={})}
    position = {
        'USD': 500,
        'AAPL': 5,
        'SPY': 0}
    strategy_alloc = {
        'A': 0.25,
        'B': 0.2,
        'C': 0.3}
    res = portfolio_adjustment_runner(
        generic_exposure_table, position, strategy_alloc)

    #ensure that no new partitions added or removed
    assert res.table['A']['alloc'] == {}
    assert res.table['B']['alloc'] == {'AAPL': 1}
    assert res.table['C']['alloc'] == {'AAPL': 1}
    assert len(res.table.keys()) == 3
    #ensure that no orders are cancelled
    assert len(res.cancelled_ids) == 0
    #ensure that no orders are modified
    assert len(res.modified_orders) == 2
    assert res.modified_orders[0] == (1000, {'qty': 1})
    assert res.modified_orders[1] == (1001, {'qty': 1})
    #ensure that no new orders submitted
    assert len(res.submitted_orders) == 0

def test_case_5():
    """When a partition is removed, excess known long positions are correctly exited.
    """
    generic_exposure_table = {
        "A": dict(alloc={'SPY': 1}, weight=0.5, open={}),
        "B": dict(alloc={'AAPL': 1}, weight=0.25, open={}),
        "C": dict(alloc={'AAPL': 1}, weight=0.25, open={})}
    position = {
        'USD': 0,
        'AAPL': 5,
        'SPY': 2}
    strategy_alloc = {
        'B': 0.25,
        'C': 0.25}
    res = portfolio_adjustment_runner(
        generic_exposure_table, position, strategy_alloc)

    #ensure that no new partitions added or removed
    assert len(res.table.keys()) == 2
    assert res.table['B']['alloc'] == {'AAPL': 1}
    assert res.table['C']['alloc'] == {'AAPL': 1}
    #ensure that no orders are cancelled
    assert len(res.cancelled_ids) == 0
    #ensure that no orders are modified
    assert len(res.modified_orders) == 0
    #ensure that no new orders submitted
    assert len(res.submitted_orders) == 1
    assert res.submitted_orders[0] == ('SPY', 'SELL', 2, None, None)

def test_case_6():
    """When a partition is removed, excess known short positions are correctly exited.
    """
    generic_exposure_table = {
        "A": dict(alloc={'SPY': -1}, weight=0.5, open={}),
        "B": dict(alloc={'AAPL': 1}, weight=0.25, open={}),
        "C": dict(alloc={'AAPL': 1}, weight=0.25, open={})}
    position = {'USD': 1000, 'AAPL': 5, 'SPY': -2}
    strategy_alloc = {'B': 0.25, 'C': 0.25}
    res = portfolio_adjustment_runner(
        generic_exposure_table, position, strategy_alloc)
    #ensure that no new partitions added or removed
    assert len(res.table.keys()) == 2
    assert res.table['B']['alloc'] == {'AAPL': 1}
    assert res.table['C']['alloc'] == {'AAPL': 1}
    #ensure that no orders are cancelled
    assert len(res.cancelled_ids) == 0
    #ensure that no orders are modified
    assert len(res.modified_orders) == 0
    #ensure that no new orders submitted
    assert len(res.submitted_orders) == 1
    assert res.submitted_orders[0] == ('SPY', 'BUY', 2, None, None)

def test_case_7():
    """When there are no changes in allocation, unknown positions are correctly exited.
    """
    generic_exposure_table = {
        "A": dict(alloc={}, weight=0.25, open={}),
        "B": dict(alloc={'AAPL': 1}, weight=0.25, open={}),
        "C": dict(alloc={'AAPL': 1}, weight=0.25, open={})}
    position = {
        'USD': 100,
        'AAPL': 5,
        'MSFT': 2}
    strategy_alloc = {
        'A': 0.25,
        'B': 0.25,
        'C': 0.25}
    res = portfolio_adjustment_runner(
        generic_exposure_table, position, strategy_alloc)

    #ensure that no new partitions added or removed
    assert len(res.table.keys()) == 3
    assert res.table['A']['alloc'] == {}
    assert res.table['B']['alloc'] == {'AAPL': 1}
    assert res.table['C']['alloc'] == {'AAPL': 1}
    #ensure that no orders are cancelled
    assert len(res.cancelled_ids) == 0
    #ensure that no orders are modified
    assert len(res.modified_orders) == 0
    #ensure that no new orders submitted
    assert len(res.submitted_orders) == 1
    assert res.submitted_orders[0] == ('MSFT', 'SELL', 2, None, None)

def test_case_8():
    """When there are no changes in allocation, unknown positions are correctly exited.
    """
    generic_exposure_table = {
        "A": dict(alloc={}, weight=0.25, open={}),
        "B": dict(alloc={'AAPL': 1}, weight=0.25, open={}),
        "C": dict(alloc={'AAPL': 1}, weight=0.25, open={})}
    position = {
        'USD': 900,
        'AAPL': 5,
        'MSFT': -2}
    strategy_alloc = {
        'A': 0.25,
        'B': 0.25,
        'C': 0.25}
    res = portfolio_adjustment_runner(
        generic_exposure_table, position, strategy_alloc)

    #ensure that no new partitions added or removed
    assert len(res.table.keys()) == 3
    assert res.table['A']['alloc'] == {}
    assert res.table['B']['alloc'] == {'AAPL': 1}
    assert res.table['C']['alloc'] == {'AAPL': 1}
    #ensure that no orders are cancelled
    assert len(res.cancelled_ids) == 0
    #ensure that no orders are modified
    assert len(res.modified_orders) == 0
    #ensure that no new orders submitted
    assert len(res.submitted_orders) == 1
    assert res.submitted_orders[0] == ('MSFT', 'BUY', 2, None, None)

def test_case_9():
    """When there are no changes in allocation, missing short positions are correctly entered.
    """
    generic_exposure_table = {
        "A": dict(alloc={'SPY': -1}, weight=0.25, open={}),
        "B": dict(alloc={'AAPL': 1}, weight=0.25, open={}),
        "C": dict(alloc={'AAPL': 1}, weight=0.25, open={})}
    position = {
        'USD': 500,
        'AAPL': 5}
    strategy_alloc = {
        'A': 0.25,
        'B': 0.25,
        'C': 0.25}
    res = portfolio_adjustment_runner(
        generic_exposure_table, position, strategy_alloc)

    assert len(res.table.keys()) == 3
    assert res.table['A']['alloc'] == {'SPY': -1}
    assert res.table['B']['alloc'] == {'AAPL': 1}
    assert res.table['C']['alloc'] == {'AAPL': 1}
    assert len(res.cancelled_ids) == 0
    assert len(res.modified_orders) == 0
    assert len(res.submitted_orders) == 1
    assert res.submitted_orders[0] == ('SPY', 'SELL', 1, None, None)
