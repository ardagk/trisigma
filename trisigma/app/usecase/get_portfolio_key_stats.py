from trisigma.domain.portfolio import PortfolioRepository
from trisigma.domain.common import modelfactory

class GetPortfolioKeyStatsUseCase:

    portfolio_repository: PortfolioRepository
    
    def __init__(self, portfolio_repository):
        self.portfolio_repo = portfolio_repository

    async def run(self, portfolio_manager_id, interval) -> dict:
        return {'someStat': 'someStatValue-' +interval, 'someOtherStat': 'someOtherStatValue-'+interval}

