from abc import ABC, abstractmethod
from typing import List, Optional
from trisigma.domain.portfolio import StrategyAllocation
from trisigma.domain.portfolio import PortfolioManager
from trisigma.domain.portfolio import ExposureTable
from trisigma.domain.brokerage import FinancialAccount


#Portfolio Repository
class PortfolioRepository(ABC):

    @abstractmethod
    async def get_strategy_allocation(self, portfolio_manager_id) -> StrategyAllocation:...

    @abstractmethod
    async def set_strategy_allocation(self, portfolio_manager_id, strategy_allocation) -> None:...

    @abstractmethod
    async def get_active_strategies(self, portfolio_manager_id: str) -> dict:...

    @abstractmethod
    async def set_active_strategies(self, portfolio_manager_id: str, strategies: dict) -> None:...

    @abstractmethod
    async def get_portfolio_position(self, portfolio_manager_id) -> dict:...

    @abstractmethod
    async def update_portfolio_position(
            self, portfolio_manager_id, position):...

    @abstractmethod
    async def get_portfolio_snapshots(
            self, portfolio_manager_id, start_time: Optional[float],
            end_time: Optional[float]) -> List[dict]:...

    @abstractmethod
    async def add_portfolio_snapshot(
            self, portfolio_manager_id, timestamp, snapshot: dict):...

    @abstractmethod
    async def get_exposure_table(self, account_id) -> ExposureTable:...

    @abstractmethod
    async def update_exposure_table(self, account_id, exposure_table) -> None:...

    @abstractmethod
    async def get_portfolio_manager(self, portfolio_manager_id) -> PortfolioManager:...

    @abstractmethod
    async def get_financial_account(self, account_id) -> FinancialAccount:...

    @abstractmethod
    async def bind_financial_account(self, account_id, portfolio_manager_id) -> None:...

    @abstractmethod
    async def find_financial_accounts(self, portfolio_manager_id) -> List[FinancialAccount]:...
