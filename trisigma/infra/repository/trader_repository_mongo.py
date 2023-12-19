import time
import os
from pymongo import MongoClient
from trisigma.domain.trading import Trader, TraderRepository
from trisigma.domain.trading import OrderSignal
from trisigma.domain.trading import StrategyDefinition
from trisigma.domain.common import modelfactory

class TraderRepositoryMongo(TraderRepository):

    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.db = self.client[os.getenv('DB_NAME')] #type: ignore

    async def create_trader(self, trader):
        self.db['trader'].update_one(
            {'trader_id': trader.trader_id},
            {'$set': modelfactory.deconstruct(trader)},
            upsert=True)

    async def get_trader(self, trader_id):
        res = self.db['trader'].find_one({'trader_id': trader_id}, {'_id': 0})
        assert bool(res)
        trader = modelfactory.construct(Trader, res)
        return trader

    async def add_strategy(self, strategy):    
        #check if strategy description already exists (by it's name), if so, then throw error
        res = self.db['strategy_definitions'].find_one({'name': strategy.name}, {'_id': 0})
        if res:
            raise ValueError("Strategy already exists")
        self.db['strategy_definitions'].insert_one(modelfactory.deconstruct(strategy))

    async def get_strategies(self):
        cur = self.db['strategy_definitions'].find({}, {'_id': 0})
        strategies = [modelfactory.construct(StrategyDefinition, doc) for doc in cur]
        return strategies

    async def push_observation(self, trader_id, data):
        assert isinstance(data.get('time'), float), "time does not exist or is not float"
        self.db['trader_observations'].insert_one(
            {'trader_id': trader_id, **data})

    async def get_observations(self, trader_id, start_time=None, end_time=None):
        start_time = start_time or 0
        end_time = end_time or time.time()
        cur = self.db['trader_observations'].find(
            {'trader_id': trader_id,
             'observation.time': {'$gte': start_time, '$lte': end_time}},
            {'_id': 0, 'trader_id': 0})
        return sorted([doc['observation'] for doc in list(cur)], key=lambda doc: doc['time'])

    async def push_comment(self, trader_id, comment):
        assert isinstance(comment.get('time'), float), "time does not exist or is not float"
        assert isinstance(comment.get('comment'), str), "comment does not exist or is not str"
        self.db['trader_comments'].insert_one(
            {'trader_id': trader_id, **comment})

    async def get_comments(self, trader_id, start_time=None, end_time=None):
        start_time = start_time or 0
        end_time = end_time or time.time()
        cur = self.db['trader_comments'].find(
            {'trader_id': trader_id,
             'comment.time': {'$gte': start_time, '$lte': end_time}},
            {'_id': 0, 'trader_id': 0})
        return sorted([doc['comment'] for doc in list(cur)], key=lambda doc: doc['time'])

    async def find_traders(self, portfolio_manager_id):
        pipeline = [
            {'$match': {'portfolio_manager_id': portfolio_manager_id}},
            {'$lookup': {
                'from': 'trader',
                'localField': 'account_id',
                'foreignField': 'account_id',
                'as': 'trader'}},
            {'$unwind': '$trader'}, #drop _id
            {'$project': {'trader._id': 0}},
            {'$replaceRoot': {'newRoot': '$trader'}}]
        res = self.db['financial_account'].aggregate(pipeline)
        traders = [modelfactory.construct(Trader, doc) for doc in res]
        return traders
