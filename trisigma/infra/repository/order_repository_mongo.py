import os
from pymongo import MongoClient
from trisigma.domain.market import Instrument
from trisigma.domain.common import modelfactory
from trisigma.domain.brokerage import Order, OrderRepository

class OrderRepositoryMongo(OrderRepository):
    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.db = self.client[os.getenv('DB_NAME')] #type: ignore

    async def add_order(self, order, signal_id=None):
        self.db['order'].insert_one(modelfactory.deconstruct(order))

    async def update_order_status(self, order_ref, status, price=None):
        self.db['order'].update_one(
            {'order_ref': order_ref},
            {'$set': {'status': status, 'price': price}})

    async def get_order(self, order_ref):
        res = self.db['order'].find_one({'order_ref': order_ref}, {'_id': 0})
        assert bool(res)
        order = modelfactory.construct(Order, res)
        return order

    async def search_orders(self, instance_id=None, order_status=None):
        filters = {}
        if instance_id:
            filters ={'meta.trader_id': {'$in':instance_id}, **filters}
        if order_status:
            filters ={'status': {'$in':order_status}, **filters}
        cur = self.db['order'].find(filters, {'_id': 0})
        orders = [modelfactory.construct(Order, doc) for doc in cur]
        return orders
