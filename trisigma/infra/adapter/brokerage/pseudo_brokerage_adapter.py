import asyncio
from pymongo import MongoClient
from trisigma.domain.market import Instrument
from trisigma.domain.brokerage import order_status, Order
from trisigma.domain.common import duration
from trisigma.app.port import BrokeragePort
from trisigma.infra.adapter import MarketAdapterWebull

class PseudoBrokerageAdapter(BrokeragePort):

    quote_asset = 'USD'

    def __init__(self, mongo_uri, account_id, init_balance=1000000):
        self.event_queue = asyncio.Queue()
        self._account_id = account_id
        self._open_orders = {}
        self._portfolio = {}
        self._mongo_client = MongoClient(mongo_uri)
        self._init_balance = init_balance
        self._market_adapter = MarketAdapterWebull()

    async def connect(self):    
        pass

    async def _load_portfolio(self):
        res = self._mongo_client['misc']['pseudo-portfolio'].find_one(
            {'account_id': self._account_id})
        if res:
            self._portfolio = res['portfolio']
            self._open_orders = res['open_orders']
        else:
            self._portfolio = {}
            self._open_orders = {}

    async def _save_portfolio(self):
        self._mongo_client['misc']['pseudo-portfolio'].update_one(
            {'account_id': self._account_id},
            {'$set': {'portfolio': self._portfolio, 'open_orders': self._open_orders}},
            upsert=True)

    async def _order_fill_worker(self):
        #checks the price of the order and updates the order status
        while True:
            for order_ref, order in self._open_orders.items():
                price = await self.get_price(order.instrument.base)
                if order.side == 'BUY' and price <= order.price:
                    self._portfolio.setdefault(order.instrument.base, 0)
                    self._portfolio[order.instrument.base] += order.qty
                    event = {'event_name': 'ORDER_STATUS_UPDATE',
                             'order_ref': order_ref,
                             'status': order_status.FILLED,
                             'price': price}
                    self.event_queue.put_nowait(event)
                    await self._save_portfolio()
                elif order.side == 'SELL' and price >= order.price:
                    self._portfolio.setdefault(order.instrument.base, 0)
                    self._portfolio[order.instrument.base] -= order.qty
                    event = {'event_name': 'ORDER_STATUS_UPDATE',
                             'order_ref': order_ref,
                             'status': order_status.FILLED,
                             'price': price}
                    self.event_queue.put_nowait(event)
                    await self._save_portfolio()
            await asyncio.sleep(20)

    async def get_price(self, asset):
        return await self._market_adapter.get_price(
                Instrument.stock(asset, self.quote_asset))

    async def place_order(self, asset, side, qty, method):
        order = Order(
            instrument=Instrument('crypto', asset, self.quote_asset),
            side=side,
            qty=qty,
            account_id=self._account_id,
            order_type='MARKET')
        self._open_orders[order.order_ref] = order
        self.event_queue.put_nowait(order)
        event = {'event_name': 'ORDER_STATUS_UPDATE',
                 'order_ref': order.order_ref,
                 'status': order_status.SUBMITTED,
                 'price': None}
        self.event_queue.put_nowait(event)
        await self._save_portfolio()
        return order

    async def modify_order(self, order_ref, changes):
        order = self._open_orders[order_ref]
        order.qty = changes['qty']
        await self._save_portfolio()

    async def cancel_order(self, order_ref):
        order = self._open_orders.pop(order_ref)
        event = {'event_name': 'ORDER_STATUS_UPDATE',
                 'order_ref': order_ref,
                 'status': order_status.CANCELLED,
                 'price': None}
        await self._save_portfolio()
        self.event_queue.put_nowait(event)

    async def quantify_asset(self, asset, quote_qty):
        return int(quote_qty / await self.get_price(asset))

    async def get_portfolio(self):
        return self._portfolio.copy()
