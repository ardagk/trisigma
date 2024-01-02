from abc import ABC, abstractmethod

class TraderManagementPort(ABC):
    
    async def spawn_trader(self, account_id: int, strategy: str, config: dict) -> int:...

    async def remove_trader(self, strategy: str, trader_id: int):...

