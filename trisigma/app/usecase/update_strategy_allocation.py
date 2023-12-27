from trisigma.domain.portfolio import StrategyAllocation, PortfolioRepository
from trisigma.app.port import AccountManagementPort, TraderManagementPort
from trisigma.domain.trading import TraderRepository, from_strategy_uri

class UpdateStrategyAllocationUseCase:

    portfolio_repo: PortfolioRepository
    trader_repo: TraderRepository
    account_management_adapter: AccountManagementPort
    trader_management_adapter: TraderManagementPort

    def __init__(
            self,
            portfolio_repository,
            trader_repository,
            account_management_adapter,
            trader_management_adapter):
        self.portfolio_repo = portfolio_repository
        self.trader_repo = trader_repository
        self.account_management_adapter = account_management_adapter
        self.trader_management_adapter = trader_management_adapter

    async def run(self, portfolio_manager_id, new_strategy_allocation) -> int:
        accounts = await self.portfolio_repo.find_financial_accounts(
                portfolio_manager_id)
        account_ids = [acc.account_id for acc in accounts]
        strategy_alloc = await self.portfolio_repo.get_strategy_allocation(
                portfolio_manager_id)

        all_traders: list = await self.trader_repo.find_traders(portfolio_manager_id)
        uris = new_strategy_allocation.keys()

        to_remove = [(from_strategy_uri(t.strategy_uri)[0], t.trader_id)
                     for t in all_traders if t.strategy_uri not in uris
                     or t.account_id not in account_ids]
        to_spawn = []
        for strategy_uri in uris:
            for account_id in account_ids:
                search_key = lambda t: (
                        t.strategy_uri == strategy_uri
                        and t.account_id == account_id)
                if not list(filter(search_key, all_traders)): #type: ignore
                    strategy, config = from_strategy_uri(strategy_uri)
                    to_spawn.append((account_id, strategy, config))

        for strategy, trader_id in to_remove:
            await self.trader_management_adapter.remove_trader(
                strategy=strategy, trader_id=trader_id)

        for account_id, strategy, config in to_spawn:
            await self.trader_management_adapter.spawn_trader(
                account_id=account_id,
                strategy=strategy,
                config=config)

        for account_id in account_ids:        
            await self.account_management_adapter.adjust_portfolio(
                    account_id=account_id,
                    portfolio_manager_id=portfolio_manager_id)

        return 1

