import numpy as np
from trisigma.app.port import BrokeragePort
from trisigma.domain.brokerage import OrderRepository
from trisigma.domain.portfolio import PortfolioRepository
from trisigma.domain.trading import OrderSignal

class OrderCancellationUseCase:
    def __init__(self,
        portfolio_repository: PortfolioRepository,
        brokerage_adapter: BrokeragePort):
        self.portfolio_repo = portfolio_repository
        self.brokerage_adapter = brokerage_adapter

    async def run(self, account_id, order_ref):
        exposure_table = await self.portfolio_repo.get_exposure_table(
            account_id)
        partition = exposure_table.find_partition(order_ref)
        await self.brokerage_adapter.cancel_order(order_ref)
        exposure_table.exposures[partition].cancel(order_ref)
        await self.portfolio_repo.update_exposure_table(
            account_id, exposure_table)
