from trisigma.domain.trading import TraderRepository
from trisigma.domain.common import modelfactory


class GetActiveBotsUseCase:

    trader_repo: TraderRepository
    
    def __init__(self, trader_repository: TraderRepository):
        self.trader_repo = trader_repository

    async def run(self, portfolio_manager_id) -> list:
        traders = await self.trader_repo.find_traders(portfolio_manager_id)
        result = [modelfactory.deconstruct(t) for t in traders]
        return result
