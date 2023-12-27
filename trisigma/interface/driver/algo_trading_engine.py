import asyncio
from trisigma.interface.common import RabbitServerAdapter
from trisigma.interface.common import RabbitPublisherAdapter
from trisigma.domain.brokerage import order_status
from trisigma.domain.common import modelfactory

class AlgoTradingEngine():

    def __init__(self, uri, strategy_executor, trading_adapter, trader_repository):
        self.trading_adapter = trading_adapter
        self.trader_repository = trader_repository
        self.strategy_executor = strategy_executor
        self.executer_worker = None
        self.rpc_adapter = RabbitServerAdapter(
                uri=uri, exchange='tradingengine', 
                server_name=strategy_executor.STRATEGY_NAME,
                prefetch_count=5)
        self.rpc_adapter.register('spawn_trader', self.spawn_instance)
        self.rpc_adapter.register('remove_trader', self.remove_instance)
        self.loop = asyncio.get_event_loop()

    async def start(self):
        await self.rpc_adapter.start()
        self._executer_worker = asyncio.create_task(
                self.strategy_executor.start())
        self._trading_action_worker = asyncio.create_task(
                self._trading_action_handler())
        self._trading_event_worker = asyncio.create_task(
                self._trading_event_handler())

    async def spawn_instance(self, account_id, config):
        trader = self.strategy_executor.spawn_instance(account_id, config)
        await self.trader_repository.create_trader(trader)
        return trader.trader_id

    async def remove_instance(self, trader_id):
        self.strategy_executor.remove_instance(trader_id)

    async def _trading_action_handler(self):
        while True:
            action = await self.strategy_executor.action_queue.get()
            print(action)
            if action['action'] == 'TRADE':
                order_signal = action['order_signal']
                account_id = action['account_id']
                ref = await self.trading_adapter.send_order_request(
                        account_id, order_signal)
                self.strategy_executor.recv_order_ack(order_signal, ref)
            elif action['action'] == "CANCEL_ORDER":
                signal_id = action['signal_id']
                account_id = action['account_id']
                await self.trading_adapter.send_cancel_request(
                        account_id, signal_id)

    async def _trading_event_handler(self):
        while True:
            event = await self.trading_adapter.event_queue.get()
            if event['event_name'] == 'ORDER_STATUS_UPDATE':
                signal_id = event['details']['order_ref']
                status = event['details']['status']
                if status == order_status.FILLED:
                    await self.strategy_executor.recv_order_fill(signal_id)
                elif status == order_status.CANCELLED:
                    await self.strategy_executor.recv_order_cancel(signal_id)
