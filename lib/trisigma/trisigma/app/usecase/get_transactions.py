from trisigma.domain.common import modelfactory
from trisigma.domain.brokerage import (
        Order, order_status, OrderRepository)
from typing import List
import time


class GetTransactionsUseCase:

    order_repo: OrderRepository

    def __init__(self, order_repository):
        self.order_repo = order_repository

    async def run(self, trader_id, start_time, end_time, count) -> List[dict]:
        transactions = await self.order_repo.search_orders(
                instance_id=[trader_id],
                order_status=[order_status.FILLED])
        start_time = start_time or 0
        end_time = end_time or time.time()
        result = [modelfactory.deconstruct(t) for t in transactions
                  if end_time > t.time > start_time]
        for row in result:
            row['asset'] = row['instrument']['base']
            del row['instrument']
            del row['meta']
            del row['price']
            del row['tif']
            del row['order_ref']
            del row['account_id']
        return result[-count:]

