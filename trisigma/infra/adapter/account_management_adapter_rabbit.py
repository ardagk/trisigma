from trisigma.infra.common import RabbitClientAdapter
from trisigma.app.port import AccountManagementPort
import asyncio

class AccountManagementAdapterRabbit(AccountManagementPort):

    def __init__(self, uri):
        self._rpc_adapter = RabbitClientAdapter(uri, exchange='brokerage')

    async def connect(self):
        await self._rpc_adapter.connect()

    async def adjust_portfolio(self, account_id, portfolio_manager_id):
        endpoint = 'adjust_portfolio'
        params = {'portfolio_manager_id': portfolio_manager_id}
        hostname = str(account_id)
        await self._rpc_adapter.request(hostname, endpoint, params) #XXX err response might not be raised
