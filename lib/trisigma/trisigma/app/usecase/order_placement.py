import numpy as np
from trisigma.app.port import BrokeragePort
from trisigma.domain.brokerage import OrderRepository
from trisigma.domain.portfolio import PortfolioRepository
from trisigma.domain.trading import OrderSignal

class OrderPlacementUseCase:

    def __init__(self,
        portfolio_repository: PortfolioRepository,
        order_repository: OrderRepository,
        brokerage_adapter: BrokeragePort):
        self.order_repo = order_repository
        self.portfolio_repo = portfolio_repository
        self.brokerage_adapter = brokerage_adapter

    async def run(self, account_id: int, order_signal: OrderSignal):
        strategy = order_signal.partition 
        #Confirm that the order type is supported
        assert order_signal.method['order_type'] in ['MARKET', 'LIMIT']

        #Confirm that there is room for the change in exposure table
        exposure_table = await self.portfolio_repo.get_exposure_table(
            account_id)
        assert strategy in exposure_table.exposures.keys()
        if not exposure_table.exposures[strategy].within_limit(
            order_signal.asset, order_signal.amount):
            raise Exception('Exposure bounds exceeded')

        # Calculate the desired exposure of the asset
        asset_exp = exposure_table.aggregate().alloc.get(
            order_signal.asset, 0)
        weight = exposure_table.weights[strategy]
        target_exposure = asset_exp + order_signal.amount * weight

        # Calculate the real exposure of the asset
        portfolio = await self.brokerage_adapter.get_portfolio()
        worth = sum([item['value'] for item in portfolio.values()])
        real_exposure = portfolio.get(
            order_signal.asset, {'value':0})['value'] / worth
        
        #Find the tradable difference in position to meet the exposure
        delta_exposure = target_exposure - real_exposure
        delta_quote_qty = delta_exposure * worth
        tradable_delta_qty = round(
            await self.brokerage_adapter.quantify_asset(
                order_signal.asset, round(abs(delta_quote_qty),6)
                ) * np.sign(delta_quote_qty),6)

        signal_side = 'BUY' if order_signal.amount > 0 else 'SELL'
        delta_qty_side = 'BUY' if tradable_delta_qty > 0 else 'SELL'
        if delta_qty_side != signal_side:
            print('signal side mismatch')
            #TODO log through a defined logger

        #Place order to close the difference of position
        order = await self.brokerage_adapter.place_order(
            asset = order_signal.asset,
            side = delta_qty_side,
            qty = abs(tradable_delta_qty),
            method = order_signal.method)
        #Save the order to the order repository
        await self.order_repo.add_order(order)

        #Update and save the new exposure table
        exposure_table.exposures[strategy].add(
            order.order_ref,
            order_signal.asset,
            order_signal.amount,
            order_signal.method)
        await self.portfolio_repo.update_exposure_table(
            account_id, exposure_table)
        return order.order_ref
