import uuid
import asyncio
from trisigma.domain.trading import OrderSignal, to_strategy_uri, Trader

class StrategyBehavior:

    _signal_buffer: list
    _signal_map: dict
    _action_queue: asyncio.Queue
    account_id: int
    tick_key = lambda: None
    STRATEGY_NAME = ''

    def __init__(self, config, account_id, action_queue):
        assert bool(self.STRATEGY_NAME), '`STRATEGY_NAME` attribute is missing'
        self._signal_buffer = []
        self._signal_map = {}
        self._action_queue = action_queue
        self._trader = Trader(
                account_id = account_id, 
                strategy_uri = to_strategy_uri(self.STRATEGY_NAME, config))
        self.config = config
        self.signals = {}

    def buy(self, symbol, exposure):
        order_signal = OrderSignal(
            asset=symbol, amount=exposure, partition=self._trader.strategy_uri,
            trader_id=self._trader.trader_id, method={})
        action = {'action': 'TRADE',
                  'order_signal': order_signal,
                  'account_id': self._trader.account_id}
        self._action_queue.put_nowait(action)
        self.signals[order_signal.signal_id] = order_signal
        return order_signal.signal_id

    def sell(self, symbol, exposure):
        signal_id = uuid.uuid4()
        order_signal = OrderSignal(
            asset=symbol, amount=-exposure, partition=self._trader.strategy_uri,
            trader_id=self._trader.trader_id, method={})
        action = {'action': 'TRADE',
                  'order_signal': order_signal,
                  'account_id': self._trader.account_id}
        self._action_queue.put_nowait(action)
        self.signals[order_signal.signal_id] = order_signal
        return order_signal.signal_id

    def bid(self, symbol, price, exposure):
        order_signal = OrderSignal(
            asset=symbol, amount=exposure, partition=self._trader.strategy_uri,
            trader_id=self._trader.trader_id, method={
                'order_type': 'LIMIT', 'price': price})
        action = {'action': 'TRADE',
                  'order_signal': order_signal,
                  'account_id': self._trader.account_id}
        self._action_queue.put_nowait(action)
        self.signals[order_signal.signal_id] = order_signal
        return order_signal.signal_id

    def ask(self, symbol, price, exposure):
        order_signal = OrderSignal(
            asset=symbol, amount=-exposure, partition=self._trader.strategy_uri,
            trader_id=self._trader.trader_id, method={
                'order_type': 'LIMIT', 'price': price})
        action = {'action': 'TRADE',
                  'order_signal': order_signal,
                  'account_id': self._trader.account_id}
        self._action_queue.put_nowait(action)
        self.signals[order_signal.signal_id] = order_signal
        return order_signal.signal_id

    def _map_signal_id(self, signal_id, order_ref):
        self._signal_map[order_ref] = signal_id

    def say(self, msg):
        ...

    def on_start(self):...

    def on_tick(self, data):...

    def on_order_fill(self, signal_id):...

    def on_order_cancel(self, signal_id):...


