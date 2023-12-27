import asyncio
import uuid
from trisigma.interface.driver import AlgoTradingEngine
from trisigma.app.port import TradingPort
from trisigma.domain.trading import StrategyExecutor, StrategyBehavior, OrderSignal, Trader

class MockStrategyBehavior(StrategyBehavior):
    STRATEGY_NAME = 'mock'
    calls = []

    def start(self):
        self.calls.append(('start', ()))

    def on_order_fill(self, signal_id):
        self.calls.append(('on_order_fill', (signal_id)))

    def on_order_cancel(self, signal_id):
        self.calls.append(('on_order_cancel', (signal_id)))

class MockStrategyExecutor(StrategyExecutor):
    STRATEGY_NAME = 'mock_strategy'
    calls = []
    instance_counter = 0

    async def start(self):
        pass

    def spawn_instance(self, account_id, config):
        self.calls.append(('spawn_trader', (account_id, config)))
        self.instance_counter+=1
        trader = Trader(account_id, 'someuri', trader_id=self.instance_counter)
        print(trader.__dict__)
        return trader

    def remove_instance(self, trader_id):
        self.calls.append(('remove_trader', (trader_id)))

class MockTradingAdapter(TradingPort):
    calls = []
    order_counter = 0
    event_queue = asyncio.Queue()
    async def send_order_request(self, account_id, order_signal) -> str:
        self.calls.append(('send_order_request', (account_id, order_signal)))
        order_counter = 0
        return str(order_counter)

    async def send_cancel_request(self, account_id, signal_id):
        self.calls.append(('send_cancel_request', (account_id, signal_id)))

    async def send_modify_request(self, account_id, signal_id, changes):
        self.calls.append(('send_modify_request', (account_id, signal_id, changes)))

class MockTraderRepository():

    async def create_trader(self, trader: Trader):...

    async def get_trader(self, trader_id: int):...

    async def add_strategy(self, strategy):...

    async def get_strategies(self): return []

    async def push_observation(self, trader_id: int, data: dict):...

    async def get_observations(
            self, trader_id: int, start_time = None,
            end_time = None) -> list: return []

    async def push_comment(self, trader_id, comment: dict):...

    async def get_comments(
            self, trader_id, start_time = None,
            end_time = None) -> list: return []

    async def find_comments(self, portfolio_manager_id: int) -> list: return []

    async def find_traders(self, portfolio_manager_id: int): return []

def test_spawn_remove_trader():
    loop = asyncio.get_event_loop()
    strategy_executor = MockStrategyExecutor()
    trading_adapter = MockTradingAdapter()
    trader_repository = MockTraderRepository()
    uri = 'amqp://null:null@host:port/'
    trading_engine = AlgoTradingEngine(uri, strategy_executor, trading_adapter, trader_repository)
    resp = loop.run_until_complete(trading_engine.spawn_instance(123, {'asset': 'AAPL'}))
    assert resp == 1
    assert strategy_executor.calls[0] == ('spawn_trader', (123, {'asset': 'AAPL'}))
    loop.run_until_complete(trading_engine.remove_instance(1))
    assert strategy_executor.calls[1] == ('remove_trader', (1))

def test_action_handling():
    loop = asyncio.get_event_loop()
    strategy_executor = MockStrategyExecutor()
    strategy_behavior = MockStrategyBehavior({}, 123, strategy_executor.action_queue)
    trading_adapter = MockTradingAdapter()
    trader_repository = MockTraderRepository()
    uri = 'amqp://null:null@host:port/'
    trading_engine = AlgoTradingEngine(uri, strategy_executor, trading_adapter, trader_repository)
    strategy_behavior.buy('AAPL', 1)
    async def run_worker():
        ilen = len(trading_adapter.calls)
        count = 0
        task = loop.create_task(trading_engine._trading_action_handler())
        while ilen == len(trading_adapter.calls) and count < 50:
            count+=1
            await asyncio.sleep(0.01)
        task.cancel()
    loop.run_until_complete(run_worker())
    req = trading_adapter.calls[0]
    assert req[0] == 'send_order_request'
    assert req[1][0] == 123
    assert isinstance(req[1][1], OrderSignal)


def test_event_handling():
    loop = asyncio.get_event_loop()
    strategy_executor = MockStrategyExecutor()
    strategy_behavior = MockStrategyBehavior({}, 123, strategy_executor.action_queue)
    trading_adapter = MockTradingAdapter()
    trader_repository = MockTraderRepository()
    uri = 'amqp://null:null@host:port/'
    trading_engine = AlgoTradingEngine(uri, strategy_executor, trading_adapter, trader_repository)
    signal_id = strategy_behavior.buy('AAPL', 1)
    strategy_executor.instances.add_instance(strategy_behavior, '123')
    strategy_behavior._map_signal_id(signal_id, "1")
    trading_adapter.event_queue.put_nowait(
            {'event_name': 'ORDER_STATUS_UPDATE',
             'details': {'order_ref': "1", 'status': 'FILLED', 'price': 100}}
            )
    async def run_worker():
        ilen = len(strategy_behavior.calls)
        count = 0
        task = loop.create_task(trading_engine._trading_event_handler())
        while ilen == len(strategy_behavior.calls) and count < 50:
            count+=1
            await asyncio.sleep(0.01)
        task.cancel()
    loop.run_until_complete(run_worker())
    req = strategy_behavior.calls[0]
    assert req[0] == 'on_order_fill'

