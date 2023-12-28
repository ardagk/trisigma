from trisigma.domain.portfolio import (
        StrategyAllocation, PortfolioRepository)

class GetStrategyAllocationUseCase:

    portfolio_repo: PortfolioRepository

    def __init__(self, portfolio_repository):
        self.portfolio_repo = portfolio_repository

    async def run(self, portfolio_manager_id) -> dict:
        alloc = await self.portfolio_repo.get_strategy_allocation(
                portfolio_manager_id)
        details = await self.portfolio_repo.get_active_strategies(
                portfolio_manager_id)
        result = {}
        for key, value in alloc.items():
            result[key] = {'allocation': value, **details[key]}
        return result

