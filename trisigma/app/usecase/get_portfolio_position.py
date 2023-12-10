from trisigma.domain.common import modelfactory
from trisigma.domain.portfolio import PortfolioRepository
from trisigma.domain.market import Instrument

class GetPortfolioPositionUseCase:

    def __init__(self, portfolio_repository, market_adapter):
        self.portfolio_repo = portfolio_repository
        self.market_adapter = market_adapter

    async def run(self, portfolio_manager_id) -> dict:
        all_pos = await self.portfolio_repo.get_portfolio_position(
                portfolio_manager_id)
        pos = {} 
        for acc_pos in all_pos.values():
            for asset, qty in acc_pos.items():
                pos.setdefault(asset, 0)
                pos[asset]+=qty
        full_pos = {}
        for asset, qty in pos.items():
            price = 1 if asset == 'USD' else await self.market_adapter.get_price(
                Instrument.stock(asset, 'USD'))
            full_pos[asset] = {'qty': qty, 'value': qty*price}
        return full_pos

