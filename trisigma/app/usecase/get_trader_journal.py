from trisigma.domain.common import modelfactory
from trisigma.domain.trading import Trader, TraderRepository
from typing import List

class GetTraderJournalUseCase:

    trader_repo: TraderRepository

    def __init__(self, trader_repository):
        self.trader_repo = trader_repository

    async def run(
            self, trader_id, 
            start_time=None, end_time=None
            ) -> List[dict]:

        result = await self.trader_repo.get_comments(
                trader_id=trader_id)
        return result

