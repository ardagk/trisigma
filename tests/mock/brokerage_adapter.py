from trisigma.app.port import BrokeragePort
from trisigma.domain.brokerage import Order
from trisigma.domain.market import Instrument
from tests.util import statics

class MockBrokerageAdapter(BrokeragePort):
    
    quote_asset = 'USD'

    def __init__(self):
        self.calls = []

    async def connect(self):
        pass

    async def place_order(self, asset, side, qty, method):
        self.calls.append(('place_order', (asset, side, qty, method)))
        return Order(
            instrument=Instrument('stock', asset, self.quote_asset),
            side=side,
            qty=qty,
            order_type=method.get('order_type', 'MARKET'),
            account_id=statics['financial_account'].account_id,
            price=method.get('price', None))

    async def modify_order(self, order_ref, changes):
        self.calls.append(('modify_order', (order_ref, changes)))

    async def cancel_order(self, order_ref):
        self.calls.append(('cancel_order', (order_ref)))

    async def quantify_asset(self, asset, quote_qty):
        self.calls.append(('quantify_asset', (asset, quote_qty)))
        qty = quote_qty / statics['prices'][asset]
        return int(qty) if statics['floor'] else qty

    async def get_portfolio(self):
        self.calls.append(('get_portfolio', ()))
        return statics['portfolio']

    async def get_price(self, asset):
        self.calls.append(('get_price', (asset)))
        return statics['prices'][asset]
