import asyncio
from trisigma.interface.common import RabbitServerAdapter
from trisigma.interface.common import RabbitPublisherAdapter
from trisigma.app.usecase import OrderPlacementUseCase
from trisigma.app.usecase import OrderCancellationUseCase
from trisigma.app.usecase import OrderModificationUseCase
from trisigma.app.usecase import OrderStatusUpdateUseCase
from trisigma.app.usecase import PortfolioAdjustmentUseCase

class BrokerageMiddleware():

    def __init__(self, uri, account_id, brokerage_adapter, 
                 order_repository, portfolio_repository):
        self.account_id = account_id
        self.brokerage_adapter = brokerage_adapter
        self.order_repository = order_repository
        self.portfolio_repository = portfolio_repository
        self.name = f'{str(account_id)}'
        self.rpc_adapter = RabbitServerAdapter(
                uri=uri, exchange='brokerage', server_name=self.name,
                queue_name='queue-acc-'+str(account_id),
                prefetch_count=5)
        self.publish_adapter = RabbitPublisherAdapter(
                uri=uri, exchange='brokerage', publisher_name=self.name)
        self.rpc_adapter.register('place_order', self.order_placement)
        self.rpc_adapter.register('modify_order', self.order_modification)
        self.rpc_adapter.register('cancel_order', self.order_cancellation)
        self.rpc_adapter.register('adjust_portfolio',
                                  self.portfolio_adjustment)

    async def start(self):
        await self.rpc_adapter.start()
        await self.publish_adapter.start()

    async def brokerage_event_worker(self):
        while True:
            event = await self.brokerage_adapter.event_queue.get()
            if event['event_name'] == 'ORDER_STATUS_UPDATE':
                await self.order_status_update(
                        event['order_ref'], event['status'], event['price'])
            await asyncio.sleep(0.01)

    async def order_placement(self, order_signal):
        usecase = OrderPlacementUseCase(
                portfolio_repository = self.portfolio_repository,
                order_repository = self.order_repository,
                brokerage_adapter = self.brokerage_adapter)
        resp = await usecase.run(self.account_id, order_signal)
        return resp

    async def order_modification(self, partition, signal_id, changes):
        usecase = OrderModificationUseCase(
                portfolio_repository = self.portfolio_repository,
                brokerage_adapter = self.brokerage_adapter)
        resp = await usecase.run(self.account_id, signal_id, changes)
        return resp

    async def order_cancellation(self, partition, signal_id):
        usecase = OrderCancellationUseCase(
                portfolio_repository = self.portfolio_repository,
                brokerage_adapter = self.brokerage_adapter)
        resp = await usecase.run(self.account_id, signal_id)
        return resp

    async def portfolio_adjustment(self, portfolio_manager_id):
        print('adjustment signal', portfolio_manager_id)
        usecase = PortfolioAdjustmentUseCase(
                portfolio_repository = self.portfolio_repository,
                order_repository = self.order_repository,
                brokerage_adapter = self.brokerage_adapter)
        resp = await usecase.run(self.account_id, portfolio_manager_id)
        print('done')

    async def order_status_update(self, order_ref, status, price):
        usecase = OrderStatusUpdateUseCase(
                portfolio_repository = self.portfolio_repository,
                order_repository = self.order_repository,
                brokerage_adapter = self.brokerage_adapter)
        event = await usecase.run(self.account_id, order_ref, status, price)
        await self.publish_adapter.publish(f'{self.name}.order_status', event)


