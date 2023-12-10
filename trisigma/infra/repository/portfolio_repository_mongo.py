import time
import os
from pymongo import MongoClient
from trisigma.domain.common import modelfactory
from trisigma.domain.brokerage import FinancialAccount
from trisigma.domain.portfolio import (
        PortfolioRepository,
        StrategyAllocation,
        ExposureTable,
        PortfolioManager,)

class PortfolioRepositoryMongo(PortfolioRepository):

    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.db = self.client[os.getenv('DB_NAME')] #type: ignore

    async def get_strategy_allocation(self, portfolio_manager_id):
        res = self.db['strategy_allocation'].find_one(
            {'portfolio_manager_id': portfolio_manager_id})
        assert bool(res)
        strategy_allocation = StrategyAllocation(res['allocation'])
        return strategy_allocation

    async def get_strategy_allocation_namings(self, portfolio_manager_id):
        res = self.db['strategy_allocation'].find_one(
            {'portfolio_manager_id': portfolio_manager_id})
        assert bool(res)
        namings = res['namings']
        return namings

    async def update_strategy_allocation(
            self, portfolio_manager_id, strategy_allocation):
        self.db['strategy_allocation'].update_one(
            {'portfolio_manager_id': portfolio_manager_id},
            {'$set': {'allocation': strategy_allocation}},
            upsert=True)

    async def update_strategy_allocation_namings(
            self, portfolio_manager_id, namings):
        self.db['strategy_allocation'].update_one(
            {'portfolio_manager_id': portfolio_manager_id},
            {'$set': {'namings': namings}},
            upsert=True)

    async def get_portfolio_position(self, portfolio_manager_id):
        res = self.db['portfolio_position'].find_one(
            {'portfolio_manager_id': portfolio_manager_id})
        assert bool(res)
        return res['position']

    async def update_portfolio_position(
            self, portfolio_manager_id, position):
        res = self.db['portfolio_position'].update_one(
            {'portfolio_manager_id': portfolio_manager_id},
            {'$set': {'position': position}},
            upsert=True)

    async def get_portfolio_snapshots(
            self, portfolio_manager_id, start_time=None, end_time=None):
        start_time = start_time or 0
        end_time = end_time or time.time()
        res = self.db['portfolio_snapshot'].find(
            {'portfolio_manager_id': portfolio_manager_id,
             'time': {'$gte': start_time, '$lte': end_time}})
        snapshots = [
                {'time': doc['time'], **doc['snapshot']} 
                for doc in res]
        return snapshots

    async def add_portfolio_snapshot(
            self, portfolio_manager_id, timestamp, snapshot):
        self.db['portfolio_snapshot'].insert_one(
            {'portfolio_manager_id': portfolio_manager_id,
             'time': timestamp,
             'snapshot': snapshot})

    async def get_exposure_table(self, account_id):
        res = self.db['exposure_table'].find_one(
            {'account_id': account_id})
        return modelfactory.construct(
                ExposureTable, res['exposure_table']) #type: ignore

    async def update_exposure_table(self, account_id, exposure_table):
        self.db['exposure_table'].update_one(
            {'account_id': account_id},
            {'$set': {'exposure_table': modelfactory.deconstruct(
                    exposure_table)}},
            upsert=True)

    async def create_portfolio_manager(self, portfolio_manager):
        self.db['portfolio_manager'].insert_one(
                modelfactory.deconstruct(portfolio_manager))

    async def get_portfolio_manager(self, portfolio_manager_id):
        res = self.db['portfolio_manager'].find_one(
            {'portfolio_manager_id': portfolio_manager_id})
        return modelfactory.construct(PortfolioManager, res)

    async def create_financial_account(self, financial_account):
        self.db['financial_account'].insert_one(
                modelfactory.deconstruct(financial_account))

    async def get_financial_account(self, account_id):
        res = self.db['financial_account'].find_one(
            {'account_id': account_id})
        assert bool(res)
        financial_account = modelfactory.construct(FinancialAccount, res)
        return financial_account

    async def find_financial_accounts(self, portfolio_manager_id):
        cur = self.db['financial_account'].find(
            {'portfolio_manager_id': portfolio_manager_id},
            {'_id': 0})
        accounts = [modelfactory.construct(FinancialAccount, doc) for doc in cur]
        return accounts

    async def bind_financial_account(self, account_id, portfolio_manager_id):
        self.db['financial_account'].update_one(
            {'account_id': account_id},
            {'$set': {'portfolio_manager_id': portfolio_manager_id}})

