from trisigma.app.port import BrokeragePort
from trisigma.domain.brokerage import OrderRepository
from trisigma.domain.portfolio import PortfolioRepository
from trisigma.domain.brokerage import Order, order_status
from trisigma.domain.trading import OrderSignal

class OrderStatusUpdateUseCase:

    def __init__(self,
        portfolio_repository: PortfolioRepository,
        order_repository: OrderRepository,
        brokerage_adapter: BrokeragePort):
        self.order_repo = order_repository
        self.portfolio_repo = portfolio_repository

    async def run(self,
        account_id: str, order_ref: str,
        status: str, price: int | None=None):
        await self.order_repo.update_order_status(order_ref, status, price)
        exposure_table = await self.portfolio_repo.get_exposure_table(account_id)
        partition = exposure_table.find_partition(order_ref)
        if partition is None:
            return
        exposure = exposure_table.exposures[partition]
        if status == order_status.CANCELLED:
            exposure.cancel(order_ref)
        if status == order_status.FILLED:
            exposure.flush(order_ref)
        await self.portfolio_repo.update_exposure_table(
            account_id, exposure_table)
        event = {
            'event_name': 'ORDER_STATUS_EVENT',
            'details': {
                'order_ref': order_ref,
                'status': status,
                'price': price}
            }
        return event
