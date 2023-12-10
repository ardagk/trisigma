from abc import ABC, abstractmethod

class AccountManagementPort(ABC):
    
    async def adjust_portfolio(self, account_id: int, portfolio_manager_id: int):...

