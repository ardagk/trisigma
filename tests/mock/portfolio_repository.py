from trisigma.domain.portfolio import PortfolioRepository
from tests.util import statics

class MockPortfolioRepository(PortfolioRepository):

    def __init__(self):
        self.calls = []

    async def get_strategy_allocation(self, portfolio_manager_id):
        self.calls.append(('get_strategy_allocation', (portfolio_manager_id)))
        return statics['allocation_table']

    async def get_strategy_allocation_namings(self, portfolio_manager_id):
        self.calls.append(('get_strategy_allocation_namings', (portfolio_manager_id)))
        return statics['allocation_namings']

    async def update_strategy_allocation(self, portfolio_manager_id, strategy_allocation):    
        self.calls.append(('update_strategy_allocation', (portfolio_manager_id, strategy_allocation)))

    async def update_strategy_allocation_namings(self, portfolio_manager_id, namings):    
        self.calls.append(('update_strategy_allocation', (portfolio_manager_id, namings)))

    async def get_portfolio_position(self, portfolio_manager_id):
        return {}

    async def update_portfolio_position(self, portfolio_manager_id, position):
        pass

    async def get_portfolio_snapshots( self, portfolio_manager_id, start_time, end_time):
        return []

    async def add_portfolio_snapshot(self, portfolio_manager_id, timestamp,  snapshot):
        pass

    async def get_exposure_table(self, account_id):
        self.calls.append(('get_exposure_table', (account_id)))
        return statics['exposure_table']

    async def update_exposure_table(self, account_id, exposure_table):
        self.calls.append(('update_exposure_table', (account_id, exposure_table)))

    async def get_portfolio_manager(self, portfolio_manager_id):
        self.calls.append(('get_portfolio_manager', (portfolio_manager_id)))
        return statics['portfolio_manager']

    async def get_financial_account(self, account_id):
        self.calls.append(('get_financial_account', (account_id)))
        return statics['account']

    async def bind_financial_account(self, account_id, portfolio_manager_id):
        self.calls.append(('bind_financial_account', (account_id, portfolio_manager_id)))

    async def find_financial_accounts(self, portfolio_manager_id):
        self.calls.append(('find_financial_accounts', (portfolio_manager_id)))
        return [statics['financial_account']]

