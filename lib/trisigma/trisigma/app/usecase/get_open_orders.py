from trisigma.domain.common import modelfactory
from trisigma.domain.brokerage import (
        Order, order_status, OrderRepository)
from typing import List

class GetOpenOrdersUseCase:

    order_repo: OrderRepository

    def __init__(self, order_repository):
        self.order_repo = order_repository

    async def run(self, trader_id) -> List[dict]:
        open_orders = await self.order_repo.search_orders(
                instance_id=[trader_id],
                order_status=[order_status.SUBMITTED])
        result = [modelfactory.deconstruct(o) for o in open_orders]
        for row in result:
            row['asset'] = row['instrument']['base']
            del row['instrument']
            del row['order_ref']
            del row['meta']
        return result
