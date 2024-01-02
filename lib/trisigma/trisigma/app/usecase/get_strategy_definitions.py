from trisigma.domain.common import modelfactory
from trisigma.domain.trading import TraderRepository
from typing import List

class GetStrategyDefinitionsUseCase:

    trader_repo: TraderRepository

    def __init__(self, trader_repository):
        self.trader_repo = trader_repository

    async def run(self) -> List[dict]:
        sdefs = await self.trader_repo.get_strategies()
        result = [modelfactory.deconstruct(sdef) for sdef in sdefs]
        return result

