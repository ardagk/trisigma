from trisigma.infra.common import RabbitClientAdapter
from trisigma.app.port import TraderManagementPort
import asyncio

class TraderManagementAdapterRabbit(TraderManagementPort):

    def __init__(self, uri):
        self._rpc_adapter = RabbitClientAdapter(uri, exchange='tradingengine')

    async def connect(self):
        await self._rpc_adapter.connect()

    async def spawn_trader(self, account_id, strategy, config):
        endpoint = 'spawn_trader'
        params = {'account_id': account_id, 'config': config}
        hostname = strategy
        trader_id = await self._rpc_adapter.request(hostname, endpoint, params) #XXX err response might not be raised
        assert isinstance(trader_id, int)
        return trader_id

    async def remove_trader(self, strategy, trader_id):
        endpoint = 'remove_trader'
        params = {'trader_id': trader_id}
        hostname = strategy
        await self._rpc_adapter.request(hostname, endpoint, params) #XXX err response might not be raised


