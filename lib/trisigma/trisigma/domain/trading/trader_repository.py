from abc import ABC, abstractmethod
from trisigma.domain.trading import Trader
from trisigma.domain.trading import StrategyDefinition
from trisigma.domain.trading import OrderSignal
from typing import List, Optional

class TraderRepository(ABC):

    async def create_trader(self, trader: Trader):...

    async def get_trader(self, trader_id: int) -> Trader:...

    async def add_strategy(self, strategy: StrategyDefinition):...

    async def get_strategies(self) -> List[StrategyDefinition]:...

    async def push_observation(self, trader_id: int, data: dict):...

    async def get_observations(
            self, trader_id: int, start_time: Optional[float] = None,
            end_time: Optional[float] = None) -> list:...

    async def push_comment(self, trader_id, comment: dict):... #comment has "time" and "comment"

    async def get_comments(
            self, trader_id, start_time: Optional[float] = None,
            end_time:Optional[float] = None) -> list:...

    async def find_comments(self, portfolio_manager_id: int) -> list:...

    async def find_traders(self, portfolio_manager_id: int) -> List[Trader]:...

