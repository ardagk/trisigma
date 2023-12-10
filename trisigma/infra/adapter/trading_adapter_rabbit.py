import asyncio
from trisigma.app.port import TradingPort
from trisigma.domain.trading import OrderSignal
from trisigma.domain.brokerage import order_status
from trisigma.infra.common import RabbitClientAdapter, RabbitSubscriberAdapter

class TradingAdapterRabbitMQ(TradingPort):

    def __init__(self, uri):
        self.event_queue = asyncio.Queue()
        self._rpc_adapter = RabbitClientAdapter(uri, exchange='brokerage')
        self._sub_adapter = RabbitSubscriberAdapter(uri, exchange='brokerage')
        #XXX non-belonging signals will be received
        self._sub_adapter.subscribe('*.order_status', self._status_event_handler)

    async def _status_event_handler(self, event):
        if event['event_name'] == 'ORDER_STATUS_EVENT':
            await self.event_queue.put(event)

    async def send_order_request(self, account_id, order_signal: OrderSignal) -> str:
        endpoint = 'order_placement'
        params = {'order_signal': order_signal}
        ref = await self._rpc_adapter.request(account_id, endpoint, params) #XXX err response might not be raised
        assert isinstance(ref, str)
        return ref

    async def send_cancel_request(self, account_id, signal_id: int):
        endpoint = 'order_modification'
        params = {'signal_id': signal_id}
        await self._rpc_adapter.request(account_id, endpoint, params) #XXX err response might not be raised

    async def send_modify_request(self, account_id, signal_id: int, changes: dict):
        endpoint = 'order_cancellation'
        params = {'signal_id': signal_id, 'changes': changes}
        await self._rpc_adapter.request(account_id, endpoint, params) #XXX err response might not be raised
