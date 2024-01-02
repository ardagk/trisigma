import numpy as np
from trisigma.app.port import BrokeragePort
from trisigma.domain.brokerage import OrderRepository
from trisigma.domain.portfolio import PortfolioRepository
from trisigma.domain.trading import OrderSignal

class OrderModificationUseCase:
    def __init__(self,
        portfolio_repository: PortfolioRepository,
        brokerage_adapter: BrokeragePort):
        self.portfolio_repo = portfolio_repository
        self.brokerage_adapter = brokerage_adapter

    async def run(self, account_id, order_ref, changes):
        exposure_table = await self.portfolio_repo.get_exposure_table(
            account_id)
        partition = exposure_table.find_partition(order_ref)
        exposure = exposure_table.exposures[partition]
        if len(changes.keys()) == 1 and 'amount' in changes.keys():
            new_amount = changes['amount']
            cur_amount = exposure.buffer[order_ref]['total']
            signal = exposure.buffer[order_ref]
            asset = signal['asset']
            exposure.within_limit(asset, new_amount - cur_amount)
            portfolio = await self.brokerage_adapter.get_portfolio() 
            worth = sum([item['value'] for item in portfolio.values()])
            asset_exposure = new_amount * exposure_table.weights[partition]
            asset_value = asset_exposure * worth
            signed_qty = await self.brokerage_adapter.quantify_asset(
                asset, asset_value)
            await self.brokerage_adapter.modify_order(
                order_ref, {'qty': abs(signed_qty)})
            exposure.modify(order_ref, new_amount)
        await self.portfolio_repo.update_exposure_table(
            account_id, exposure_table)
