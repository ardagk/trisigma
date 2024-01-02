from trisigma.app.port import BrokeragePort
from trisigma.domain.brokerage import OrderRepository
from trisigma.domain.portfolio import PortfolioRepository
from trisigma.domain.trading import OrderSignal

class PortfolioAdjustmentUseCase:

    def __init__(self,
        portfolio_repository: PortfolioRepository,
        order_repository: OrderRepository,
        brokerage_adapter: BrokeragePort):
        self.order_repo = order_repository
        self.portfolio_repo = portfolio_repository
        self.brokerage_adapter = brokerage_adapter

    async def run(self, account_id: int, portfolio_manager_id: int):
        #TODO log a report of changes that will be made
        #XXX  exit modifications must be done prior to entry

        #Fetch strategy allocation and exposure table
        strategy_alloc = await self.portfolio_repo.get_strategy_allocation(
            portfolio_manager_id)
        exposure_table = await self.portfolio_repo.get_exposure_table(
            account_id)

        #Determine the partitions to add, remove, and rescale
        new_partitions = [
            (partition, weight)
            for partition, weight in strategy_alloc.items()
            if partition not in exposure_table.exposures.keys()]
        removed_partitions = [
            partition for partition in exposure_table.exposures.keys()
            if partition not in strategy_alloc.keys()]
        rescaled_partitions = [
            (partition, weight)
            for partition, weight in strategy_alloc.items()
            if partition in exposure_table.exposures.keys()
            and exposure_table.weights[partition] != weight]

        #Determine the orders that must be cancelled
        orders_to_cancel = []
        for partition in removed_partitions:
            buffer = exposure_table.exposures[partition].buffer
            orders_to_cancel.extend([
                val['ref'] for val in buffer.values()]
                )

        #Determine the orders that must be modified
        orders_to_modify = []
        portfolio = await self.brokerage_adapter.get_portfolio()
        worth = sum([item['value'] for item in portfolio.values()])
        for partition, weight in rescaled_partitions:
            buffer = exposure_table.exposures[partition].buffer
            for details in buffer.values():
                target_value = details['total'] * weight * worth
                #XXX if qty is same, submitting might raise error on adapter
                #XXX same goes if it's zero
                #XXX how does adapter quantify negative value?
                target_qty = await self.brokerage_adapter.quantify_asset( 
                    details['asset'], target_value)
                orders_to_modify.append((details['ref'], target_qty))

        #Determine the new orders that must be submitted
        orders_to_create = []
        target_asset_alloc = {}
        for partition, weight in strategy_alloc.items():
            alloc = exposure_table.exposures[partition].alloc
            for asset, exposure in alloc.items():
                target_asset_alloc.setdefault(asset, 0)
                target_asset_alloc[asset] += exposure * weight
        real_asset_alloc = {
            asset: amount['value'] / worth
            for asset, amount in portfolio.items()
            if asset != self.brokerage_adapter.quote_asset}
        involved_assets = set(
            target_asset_alloc.keys()
            ).union(real_asset_alloc.keys())
        for asset in involved_assets:
            delta_alloc = target_asset_alloc.get(
                asset, 0) - real_asset_alloc.get(asset, 0)
            delta_value = delta_alloc * worth
            delta_qty = await self.brokerage_adapter.quantify_asset(
                asset, delta_value)
            if delta_qty != 0:
                orders_to_create.append((asset, delta_qty))

        #Cancel selected open orders
        for order_ref in orders_to_cancel:
            #print('canceling', order_ref)
            await self.brokerage_adapter.cancel_order(order_ref)
        
        #Modify selected open orders
        for order_ref, target_qty in orders_to_modify:
            await self.brokerage_adapter.modify_order(
                order_ref, {'qty': target_qty})

        #Submit new orders
        for asset, delta_qty in orders_to_create:
            order = await self.brokerage_adapter.place_order(
                asset = asset,
                side = 'BUY' if delta_qty > 0 else 'SELL',
                qty = abs(delta_qty),
                method = {})
            await self.order_repo.add_order(order)

        #Update the exposure table
        for partition in removed_partitions:
            exposure_table.remove_partition(partition)
        for partition, weight in rescaled_partitions:
            exposure_table.rescale_partition(partition, weight)
        for partition, weight in new_partitions:
            exposure_table.add_partition(partition, weight)
        await self.portfolio_repo.update_exposure_table(
            account_id, exposure_table)

        #Bind the financial account to the given portfolio manager
        await self.portfolio_repo.bind_financial_account(
            account_id, portfolio_manager_id)
